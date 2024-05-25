"""
Module Implementing the Metchange Algorithm
"""
# Imports
# Standard Library Imports
from __future__ import annotations
from functools import reduce
from typing import Iterable
import warnings

# External Imports
import cobra
import numpy as np
import pandas as pd
from tqdm import tqdm


# Local Imports


# region Metchange

def metchange(model: cobra.Model,
              reaction_weights: dict[str, float] | pd.Series,
              metabolites: Iterable[str] = None,
              proportion: float = 0.95
              ) -> pd.Series:
    """
    Use the Metchange algorithm to find the inconsistency scores for a set of
    metabolites based on reaction weights.

    :param model: Cobra model to use for performing the metchange algorithm
    :type model: cobra.Model
    :param metabolites: Metabolites to calculate consistency scores for, if None
        (default) will calculate for all metabolites in the model
    :type metabolites: Iterable[str]
    :param reaction_weights: Weights for the reactions in the model, should
        correspond to the probability that reaction should not be active.
    :type reaction_weights: dict[str, float] | pd.Series
    :param proportion: Proportion of the maximum to constrain the metabolite
        production to be above.
    :type proportion: float
    :return: Series of inconsistency scores for all the `metabolites`
    :rtype: pd.Series

    .. note:
       This algorithm seeks to find an inconsistency score for metabolites based
       on gene expression. The gene expression is represented by reaction weights,
       which can be calculated by combining
       `metworkpy.metabolites.metchange_functions.expr_to_metchange_gene_weights`_ and
       `metworkpy.parse.gpr.gene_to_rxn_weights`_ . The algorithm calculates the
       inconsistency score through a two part optimization. First, for a given
       metabolite, the maximum metabolite production is found. Then the metabolite
       production is constrained to stay above proportion*maximum metabolite production,
       and the inner product of reaction weights, and reaction fluxes is minimized.
       This minimum inner product is the inconsistency score.
    """
    if isinstance(reaction_weights, dict):
        reaction_weights = pd.Series(reaction_weights)
    # If reaction weights is empty, set it to be 0 for all metabolites
    # And raise warning
    if len(reaction_weights) == 0:
        raise ValueError("Reaction weights is empty, must have at least one weight.")
    if metabolites is None:
        metabolites = model.metabolites.list_attr("id")
    elif isinstance(metabolites, str):
        metabolites = metabolites.split(sep=",")
    res_series = pd.Series(np.nan, index=metabolites)
    for metabolite in tqdm(metabolites):
        with MetchangeObjectiveConstraint(model=model,
                                          metabolite=metabolite,
                                          reaction_weights=reaction_weights,
                                          proportion=proportion) as m:
            res_series[metabolite] = m.slim_optimize()
    return res_series


# endregion Metchange

# region Context Manager

class MetchangeObjectiveConstraint:
    """
    Context Manager for creating the Metchange objective

    :param model: Cobra model to add metchange objective to
    :type model: cobra.Model
    :param metabolite: String ID of metabolite to add metchange objective for
    :type metabolite: str
    :param reaction_weights: Weights for each reaction, representing the probability
        of that reaction being missing. A lower value indicates that the reaction is
        more likely to be present.
    :type reaction_weights: pd.Series
    :param proportion: Proportion of maximum metabolite production required as a
        constraint during the second optimization, where the inner product of
        reaction weights and reaction fluxes is minimized.
    :type proportion: float
    """

    def __init__(self, model: cobra.Model,
                 metabolite: str,
                 reaction_weights: pd.Series,
                 proportion: float = 0.95):
        if (reaction_weights == 0.).all():
            raise ValueError(f"At least one weight must be non-zero, but all weights "
                             f"in reaction_weights are zero.")
        self.added_sink = f"tmp_{metabolite}_sink"
        self.metabolite = metabolite
        self.model = model
        self.rxn_weights = reaction_weights
        self.proportion = proportion
        self.to_add = []

    def __enter__(self):
        self.original_objective = self.model.objective
        self.original_objective_direction = self.model.objective_direction
        met_sink_reaction = cobra.Reaction(id=self.added_sink,
                                           name=f"Temporary {self.metabolite} sink",
                                           lower_bound=0.)
        met_sink_reaction.add_metabolites({
            self.model.metabolites.get_by_id(self.metabolite): -1
        })
        self.model.add_reactions([met_sink_reaction])
        self.model.objective = self.added_sink
        self.model.objective_direction = 'max'
        obj_max = self.model.slim_optimize()
        self.model.reactions.get_by_id(self.added_sink).lower_bound = (obj_max *
                                                                       self.proportion)
        rxn_vars = []
        for rxn, weight in self.rxn_weights.items():
            # If the weight is 0., doesn't need to be added
            if weight == 0.:
                continue
            abs_var, *constr = (cobra.util.solver
            .add_absolute_expression(
                model=self.model,
                expression=self.model.reactions.get_by_id(rxn).flux_expression,
                name=f"abs_var_{rxn}_{self.metabolite}",
                add=False
            ))
            self.to_add.append(abs_var)
            self.to_add.extend(constr)
            rxn_vars.append(abs_var * weight)
        # Add needed constraints and variables to model
        self.model.add_cons_vars(self.to_add)
        # Create objective of weight*abs value of rxn flux
        self.model.objective = reduce(lambda x, y: x + y, rxn_vars)
        self.model.objective_direction = "min"
        return self.model

    def __exit__(self, exc_type, exc_value, exc_tb):
        self.model.objective = self.original_objective
        self.model.objective_direction = self.original_objective_direction
        self.model.remove_reactions([self.added_sink])
        cobra.util.solver.remove_cons_vars_from_problem(self.model, self.to_add)

# endregion Context Manager