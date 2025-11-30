import unittest
from pathlib import Path
from src.AI_analysis_code import codeAnalysisAI
import pytest


class TestAIOutput(unittest.TestCase):

    @classmethod
    def setUpClass(cls):

        """
        Set up the test class by defining the folder path to the
        "tiny_scripts" directory and running the code analysis
        on it. The result is stored in the "result" class
        variable and additional make so that the run_analysis() method is called
        once for the entire test suite, preventing it from being called again in other words,
        The Ollama model is only ran once
        """
        root_folder = Path(__file__).resolve().parent
        cls.folder = root_folder / "tiny_scripts"
        cls.instance = codeAnalysisAI(cls.folder)
        cls.result = cls.instance.run_analysis()

    #pytest.skip("Skipping Ollama-dependent tests", allow_module_level=True)
    def test_analysis_returns_valid_result(self):
        """Tests that the result of the code analysis is valid.

        The result should not be None, should be a dictionary, and should not be empty.
        """
        self.assertIsNotNone(self.result, "Result should not be None")

        self.assertIsInstance(self.result, dict, "Result should be a dictionary")

        self.assertGreater(
            len(self.result),
            0,
            "Result dictionary should not be empty"
        )
        self.assertEqual(
            len(self.result),
            8,
            "Result dictionary should have 8 items"
        )

    def test_output_structure(self):

        """Tests the structure of the output of the code analysis.

        The output should be a dictionary with the following top-level keys:
            - file: A string representing the file path.
            - language: A string representing the programming language.
            - summary: A string representing a summary of the code.
            - design_and_architecture: A dictionary containing code analysis results related to design and architecture.
            - data_structures_and_algorithms: A dictionary containing code analysis results related to data structures and algorithms.
            - control_flow_and_error_handling: A dictionary containing code analysis results related to control flow and error handling.
            - library_and_framework_usage: A dictionary containing code analysis results related to library and framework usage.
            - code_quality_and_maintainability: A dictionary containing code analysis results related to code quality and maintainability.
            - inferred_strengths: A list of strings representing inferred code strengths.
            - growth_areas: A list of strings representing potential growth areas for the code.
            - recommended_refactorings: A list of strings representing recommended refactorings for the code.

        The nested dictionaries should also be checked for the correct keys and data types.
        """
        for key, value in self.result.items():
            # Check that key is a file path string
            self.assertIsInstance(key, str)

            # Check that value is a dictionary
            self.assertIsInstance(value, dict)

            # Check top-level keys exist

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
    unittest.main(verbosity=2)