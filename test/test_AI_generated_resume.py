import unittest
import pytest
from src.Generate_AI_Resume import GenerateProjectResume
from src.Generate_AI_Resume import OOPPrinciple,ResumeItem
from pathlib import Path


class TestGenerateProjectResume(unittest.TestCase):
    """
    Test class for the GenerateProjectResume class.
    """

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
        cls.instance = GenerateProjectResume(cls.folder)
        cls.result = cls.instance.generate()


    def test_output_resume_type(self):
        """
        Tests that the output of generate() is a ResumeItem object and that its
        oop_principles_detected attribute is a dictionary containing OOPPrinciple objects.
        """

        self.assertIsInstance(self.result, ResumeItem)
        principles=self.result.oop_principles_detected
        self.assertIsInstance(principles,dict)
        for p in principles.values():
            self.assertIsInstance(p, OOPPrinciple)
            self.assertIsInstance(p.present, bool)
            self.assertIsInstance(p.description, str)
            self.assertIsInstance(p.code_snippets, list)



if __name__ == "__main__":
    unittest.main()
