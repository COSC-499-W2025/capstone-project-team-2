import unittest
from pathlib import Path
from src.AI_analysis_code import codeAnalysisAI


class TestAIOutput(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        """Run the analysis once for the entire test class."""
        root_folder = Path(__file__).resolve().parent
        cls.folder = root_folder / "tiny_scripts"
        cls.instance = codeAnalysisAI(cls.folder)
        cls.result = cls.instance.run_analysis()

    def test_analysis_returns_valid_result(self):
        # The result should not be None
        self.assertIsNotNone(self.result, "Result should not be None")

        # The result should be a dictionary
        self.assertIsInstance(self.result, dict, "Result should be a dictionary")

        # The dictionary should not be empty
        self.assertGreater(
            len(self.result),
            0,
            "Result dictionary should not be empty"
        )

    def test_output_structure(self):
        """Test that each result has the correct structure."""
        for key, value in self.result.items():
            # Check that key is a file path string
            self.assertIsInstance(key, str)

            # Check that value is a dictionary
            self.assertIsInstance(value, dict)

            # Check top-level keys exist
            required_keys = [
                "file", "language", "summary",
                "design_and_architecture",
                "data_structures_and_algorithms",
                "control_flow_and_error_handling",
                "library_and_framework_usage",
                "code_quality_and_maintainability",
                "inferred_strengths",
                "growth_areas",
                "recommended_refactorings",
            ]

            for required_key in required_keys:
                self.assertIn(required_key, value,
                              f"Missing key '{required_key}' in {key}")

            # Check data types of top-level fields
            self.assertIsInstance(value["file"], str)
            self.assertIsInstance(value["language"], str)
            self.assertIsInstance(value["summary"], str)
            self.assertIsInstance(value["inferred_strengths"], list)
            self.assertIsInstance(value["growth_areas"], list)
            self.assertIsInstance(value["recommended_refactorings"], list)

            # Check nested dictionaries exist
            self.assertIsInstance(value["design_and_architecture"], dict)
            self.assertIsInstance(value["data_structures_and_algorithms"], dict)
            self.assertIsInstance(value["control_flow_and_error_handling"], dict)
            self.assertIsInstance(value["library_and_framework_usage"], dict)
            self.assertIsInstance(value["code_quality_and_maintainability"], dict)


if __name__ == "__main__":
    unittest.main(verbosity=2, buffer=False)
