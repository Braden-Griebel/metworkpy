# Core Library modules
import os.path
import pathlib
import unittest

# External Library Imports
from cobra import Metabolite, Reaction
from cobra.core.configuration import Configuration

# Local imports
import metworkpy.utils.models


class TestParseFileType(unittest.TestCase):
    """
    Class for testing if _parse_file_type function works correctly
    """

    @classmethod
    def setUpClass(cls):
        Configuration.solver = "glpk"  # Use GLPK solver for testing

    def test_parse_file_type(self):
        self.assertEqual(metworkpy.utils.models._parse_file_type("joblib"), "joblib")
        self.assertEqual(metworkpy.utils.models._parse_file_type("pkl"), "pickle")
        self.assertEqual(metworkpy.utils.models._parse_file_type("pickle"), "pickle")
        self.assertEqual(metworkpy.utils.models._parse_file_type("yml"), "yaml")
        self.assertEqual(metworkpy.utils.models._parse_file_type("xml"), "sbml")
        self.assertEqual(metworkpy.utils.models._parse_file_type("jsn"), "json")
        self.assertEqual(metworkpy.utils.models._parse_file_type("m"), "mat")
        self.assertEqual(metworkpy.utils.models._parse_file_type("mat"), "mat")
        self.assertEqual(metworkpy.utils.models._parse_file_type("sbml"), "sbml")


class TestModelIO(unittest.TestCase):
    """
    Class for testing if read_model function works correctly
    """

    @classmethod
    def setUpClass(cls):
        Configuration.solver = "glpk"  # Use GLPK solver for testing

    def test_read_model(self):
        data_path = str(pathlib.Path(__file__).parent.parent.joinpath("data"))
        model_json = metworkpy.utils.models.read_model(
            os.path.join(data_path, "textbook_model.json")
        )
        model_xml = metworkpy.utils.models.read_model(
            os.path.join(data_path, "textbook_model.xml")
        )
        model_mat = metworkpy.utils.models.read_model(
            os.path.join(data_path, "textbook_model.mat")
        )
        model_yaml = metworkpy.utils.models.read_model(
            os.path.join(data_path, "textbook_model.yaml")
        )
        for rxn in model_json.reactions:
            self.assertTrue(rxn in model_xml.reactions)
            self.assertTrue(rxn in model_mat.reactions)
            self.assertTrue(rxn in model_yaml.reactions)
        for met in model_json.metabolites:
            self.assertTrue(met in model_xml.metabolites)
            self.assertTrue(met in model_mat.metabolites)
            self.assertTrue(met in model_yaml.metabolites)
        for gene in model_json.genes:
            self.assertTrue(gene in model_xml.genes)
            self.assertTrue(gene in model_mat.genes)
            self.assertTrue(gene in model_yaml.genes)

    def test_write_model(self):
        data_path = str(pathlib.Path(__file__).parent.parent.joinpath("data"))
        out_dir = str(
            pathlib.Path(__file__).parent.parent.joinpath("data").joinpath("temp")
        )
        try:
            os.mkdir(out_dir)
            model = metworkpy.utils.models.read_model(
                os.path.join(data_path, "textbook_model.json")
            )
            metworkpy.utils.models.write_model(
                model, os.path.join(out_dir, "textbook_model.json")
            )
            metworkpy.utils.models.write_model(
                model, os.path.join(out_dir, "textbook_model.xml")
            )
            metworkpy.utils.models.write_model(
                model, os.path.join(out_dir, "textbook_model.yaml")
            )
            metworkpy.utils.models.write_model(
                model, os.path.join(out_dir, "textbook_model.mat")
            )
            self.assertTrue(
                os.path.exists(os.path.join(out_dir, "textbook_model.json"))
            )
            self.assertTrue(os.path.exists(os.path.join(out_dir, "textbook_model.xml")))
            self.assertTrue(
                os.path.exists(os.path.join(out_dir, "textbook_model.yaml"))
            )
            self.assertTrue(os.path.exists(os.path.join(out_dir, "textbook_model.mat")))
            model_json = metworkpy.utils.models.read_model(
                os.path.join(out_dir, "textbook_model.json")
            )
            model_mat = metworkpy.utils.models.read_model(
                os.path.join(out_dir, "textbook_model.mat")
            )
            model_xml = metworkpy.utils.models.read_model(
                os.path.join(out_dir, "textbook_model.xml")
            )
            model_yaml = metworkpy.utils.models.read_model(
                os.path.join(out_dir, "textbook_model.yaml")
            )
            for rxn in model_json.reactions:
                self.assertTrue(rxn in model_xml.reactions)
                self.assertTrue(rxn in model_mat.reactions)
                self.assertTrue(rxn in model_yaml.reactions)
            for met in model_json.metabolites:
                self.assertTrue(met in model_xml.metabolites)
                self.assertTrue(met in model_mat.metabolites)
                self.assertTrue(met in model_yaml.metabolites)
            for gene in model_json.genes:
                self.assertTrue(gene in model_xml.genes)
                self.assertTrue(gene in model_mat.genes)
                self.assertTrue(gene in model_yaml.genes)
        finally:
            if os.path.exists(out_dir):
                if os.path.exists(os.path.join(out_dir, "textbook_model.json")):
                    os.remove(os.path.join(out_dir, "textbook_model.json"))
                if os.path.exists(os.path.join(out_dir, "textbook_model.xml")):
                    os.remove(os.path.join(out_dir, "textbook_model.xml"))
                if os.path.exists(os.path.join(out_dir, "textbook_model.yaml")):
                    os.remove(os.path.join(out_dir, "textbook_model.yaml"))
                if os.path.exists(os.path.join(out_dir, "textbook_model.mat")):
                    os.remove(os.path.join(out_dir, "textbook_model.mat"))
                os.rmdir(out_dir)


class TestModelEquality(unittest.TestCase):
    data_path = None
    model_path = None

    @classmethod
    def setUpClass(cls):
        Configuration().solver = "glpk"
        cls.data_path = str(pathlib.Path(__file__).parent.parent / "data")
        cls.model_path = os.path.join(cls.data_path, "test_model.json")
        cls.model = metworkpy.utils.models.read_model(cls.model_path)

    def test_identical_models(self):
        self.assertTrue(metworkpy.utils.models.model_eq(self.model, self.model))

    def test_model_copy(self):
        model_copy = self.model.copy()
        self.assertTrue(metworkpy.utils.models.model_eq(self.model, model_copy))
        self.assertTrue(
            metworkpy.utils.models.model_eq(model_copy, self.model)
        )  # Should be order independent

    def test_adding_metabolite(self):
        model1 = self.model.copy()
        model2 = self.model.copy()
        # Initial equality check
        self.assertTrue(metworkpy.utils.models.model_eq(model1, model2))
        test_met = Metabolite(
            "test_met",
            formula="C1H2O3",
            name="Test Metabolite",
            compartment="c",
        )
        model1.add_metabolites(test_met)
        self.assertFalse(metworkpy.utils.models.model_eq(model1, model2))
        self.assertFalse(metworkpy.utils.models.model_eq(model2, model1))

    def test_adding_reaction(self):
        model1 = self.model.copy()
        model2 = self.model.copy()
        # Initial equality check
        self.assertTrue(metworkpy.utils.models.model_eq(model1, model2))
        test_rxn = Reaction("test_rxn")
        test_rxn.name = "Test Reaction"
        test_rxn.subsystem = "Test Subsystem"
        test_rxn.lower_bound = -42
        test_rxn.upper_bound = 42
        test_rxn.add_metabolites(
            {
                model1.metabolites.get_by_id("A_c"): -1,
                model1.metabolites.get_by_id("B_c"): 1,
                model1.metabolites.get_by_id("C_c"): 1,
                model1.metabolites.get_by_id("D_c"): -1,
                model1.metabolites.get_by_id("E_c"): 1,
                model1.metabolites.get_by_id("F_c"): -1,
                model1.metabolites.get_by_id("G_c"): 1,
            }
        )
        model1.add_reactions([test_rxn])
        self.assertFalse(metworkpy.utils.models.model_eq(model1, model2))
        self.assertFalse(metworkpy.utils.models.model_eq(model2, model1))

    def test_changes_reaction_bounds(self):
        model1 = self.model.copy()
        model2 = self.model.copy()
        model1.reactions.get_by_id("r_A_B_D_E").bounds = (-3.14, 3.14)
        self.assertFalse(metworkpy.utils.models.model_eq(model1, model2))
        self.assertFalse(
            metworkpy.utils.models.model_eq(model2, model1)
        )  # Order independent

    def test_gpr_change(self):
        model1 = self.model.copy()
        model2 = self.model.copy()
        model1.reactions.get_by_id(
            "r_A_B_D_E"
        ).gene_reaction_rule = "g_A_B_D_E or g_C_E_F"
        self.assertFalse(metworkpy.utils.models.model_eq(model1, model2))
        self.assertFalse(metworkpy.utils.models.model_eq(model2, model1))

    def test_adding_variable(self):
        model1 = self.model.copy()
        model2 = self.model.copy()
        # Initial equality check
        self.assertTrue(metworkpy.utils.models.model_eq(model1, model2))
        var = model1.solver.interface.Variable("test_var")
        model1.solver.add(var)
        self.assertFalse(
            metworkpy.utils.models.model_eq(model1, model2)
        )  # Should detect added variable
        self.assertFalse(
            metworkpy.utils.models.model_eq(model2, model1)
        )  # Should be order independent

    def test_adding_constraint(self):
        model1 = self.model.copy()
        model2 = self.model.copy()
        # Initial equality check
        self.assertTrue(metworkpy.utils.models.model_eq(model1, model2))
        var1 = model1.solver.variables["r_A_B_D_E"]
        var2 = model1.solver.variables["r_C_E_F"]
        test_const = model1.solver.interface.Constraint(var1 + var2, lb=-5, ub=5)
        model1.solver.add(test_const)
        self.assertFalse(metworkpy.utils.models.model_eq(model1, model2))
        self.assertFalse(metworkpy.utils.models.model_eq(model2, model1))

    def test_changing_constraint_bound(self):
        model1 = self.model.copy()
        model2 = self.model.copy()
        # Initial equality check
        self.assertTrue(metworkpy.utils.models.model_eq(model1, model2))
        model1.solver.constraints["E_c"].lb = -5
        self.assertFalse(metworkpy.utils.models.model_eq(model1, model2))
        self.assertFalse(metworkpy.utils.models.model_eq(model2, model1))


class TestModelBoundsEquality(unittest.TestCase):
    data_path = None
    model_path = None

    @classmethod
    def setUpClass(cls):
        Configuration().solver = "glpk"
        cls.data_path = str(pathlib.Path(__file__).parent.parent / "data")
        cls.model_path = os.path.join(cls.data_path, "test_model.json")
        cls.model = metworkpy.utils.models.read_model(cls.model_path)

    def test_bounds_equal(self):
        # Copy the model to get two identical models
        model1 = self.model.copy()
        model2 = self.model.copy()
        # Check that the bounds are all equal
        self.assertTrue(metworkpy.utils.models.model_bounds_eq(model1, model2))

    def test_bound_unequal(self):
        # Copy the model to get two identical models
        model1 = self.model.copy()
        model2 = self.model.copy()
        # Change one of the bounds of model1
        model1.reactions.get_by_id("r_A_B_D_E").bounds = (-10, 10)
        # Ensure that the bounds are now different
        self.assertFalse(metworkpy.utils.models.model_bounds_eq(model1, model2))


if __name__ == "__main__":
    unittest.main()
