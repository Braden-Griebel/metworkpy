# Standard Library Imports
import os
import pathlib
import unittest
from unittest import skipIf

# External Imports
import cobra
import numpy as np
from cobra.manipulation import knock_out_model_genes

# Local Imports
import metworkpy
from metworkpy.synleth.fastsl import (_get_potentially_active_genes, _is_essential,
                                      _rxns_to_genes, find_synthetic_lethal_genes)

BASE_PATH = pathlib.Path(__file__).parent.parent.absolute()
IN_GITHUB_ACTIONS = os.getenv("GITHUB_ACTIONS") == "true"


class TestFindSyntheticLethalGenes(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.test_model = metworkpy.read_model(BASE_PATH / "data" / "test_model.json")
        cls.textbook_model = metworkpy.read_model(BASE_PATH / "data" / "textbook_model.json")

    def test_single_gene_deletions(self):
        single_gene_ko = find_synthetic_lethal_genes(model=self.test_model,
                                                     max_depth=1,
                                                     processes=1)
        single_gene_ko_parallel = find_synthetic_lethal_genes(model=self.test_model,
                                                              max_depth=1,
                                                              processes=2)
        expected_ko = {g.id for g in cobra.flux_analysis.variability.find_essential_genes(model=self.test_model)}
        self.assertCountEqual(single_gene_ko, single_gene_ko_parallel)
        self.assertSetEqual({s.__iter__().__next__() for s in single_gene_ko}, expected_ko)
        self.assertSetEqual({s.__iter__().__next__() for s in single_gene_ko_parallel}, expected_ko)

    @skipIf(IN_GITHUB_ACTIONS, "Long Running Tests Skipped")
    def test_double_ko(self):
        ESSENTIAL_PROPORTION = 0.01
        double_ko = find_synthetic_lethal_genes(model=self.textbook_model,
                                                max_depth=2,
                                                processes=1,
                                                essential_proportion=ESSENTIAL_PROPORTION)
        double_ko_parallel = find_synthetic_lethal_genes(model=self.textbook_model,
                                                         max_depth=2,
                                                         processes=2,
                                                         essential_proportion=ESSENTIAL_PROPORTION
                                                         )
        self.assertCountEqual(double_ko, double_ko_parallel)
        max_objective_value = self.textbook_model.slim_optimize()
        for gene_set in double_ko:
            with self.textbook_model as m:
                knock_out_model_genes(model=m, gene_list=list(gene_set))
                obj_value = m.slim_optimize(error_value=np.nan)
                if not np.isnan(obj_value):  # Inconsistent linear programs are also considered essential
                    self.assertLessEqual(m.slim_optimize(), ESSENTIAL_PROPORTION * max_objective_value)

class TestHelperFunctions(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.test_model = metworkpy.read_model(BASE_PATH / "data" / "test_model.json")
        cls.textbook_model = metworkpy.read_model(BASE_PATH / "data" / "textbook_model.json")

    def test_rxns_to_genes(self):
        gene_actual = _rxns_to_genes(model=self.test_model, rxns = {'r_A_B_D_E', 'r_C_E_F'})
        genes_expected = {'g_A_B_D_E', 'g_C_E_F'}
        self.assertSetEqual(gene_actual, genes_expected)

    def test_get_potentially_active_genes(self):
        actual = _get_potentially_active_genes(model = self.test_model,
                                               pfba_fraction_of_optimum=0.95,
                                               active_cutoff=0.01)
        expected = {'g_A_imp', 'g_B_imp', 'g_C_imp', 'g_F_exp',
                    'g_G_exp', 'g_A_B_D_E', 'g_C_E_F', 'g_D_G'}
        self.assertSetEqual(actual, expected)

    def test_is_essential(self):
        expected_essential = cobra.flux_analysis.variability.find_essential_genes(model=self.textbook_model)
        for gene in expected_essential:
            self.assertTrue(_is_essential(model=self.textbook_model,
                                          gene=gene.id,
                                          essential_cutoff=0.01))



if __name__ == '__main__':
    unittest.main()
