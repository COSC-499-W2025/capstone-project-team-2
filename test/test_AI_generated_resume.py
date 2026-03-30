import warnings
warnings.filterwarnings(
    "ignore",
    message=".*MessageMapContainer.*",
    category=DeprecationWarning
)
warnings.filterwarnings(
    "ignore",
    message=".*ScalarMapContainer.*",
    category=DeprecationWarning
)
import unittest
import pytest
from src.reporting.Generate_AI_Resume import GenerateProjectResume
from src.reporting.Generate_AI_Resume import OOPPrinciple,ResumeItem
from pathlib import Path
from types import SimpleNamespace


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
        cls.instance = GenerateProjectResume.__new__(GenerateProjectResume)
        cls.instance.project_root = cls.folder
        cls.instance.saveToJson = False
        cls.instance.returnResume = None
        cls.instance.max_chars = 20_000
        cls.instance.chain = SimpleNamespace(
            invoke=lambda _payload: {
                "project_title": "Tiny Scripts",
                "one_sentence_summary": "Summarizes scripts",
                "detailed_summary": "Detailed summary for local deterministic test.",
                "key_responsibilities": ["Implemented script utilities"],
                "key_skills_used": ["Python", "Testing"],
                "tech_stack": "Python",
                "impact": "Improved developer productivity.",
                "oop_principles_detected": {
                    "abstraction": {
                        "present": True,
                        "description": "Used class abstraction.",
                        "code_snippets": [{"file": "Classes.py", "code": "class A: pass"}],
                    },
                    "encapsulation": {
                        "present": False,
                        "description": "",
                        "code_snippets": [],
                    },
                },
            }
        )
        cls.result = cls.instance.generate(saveToJson=False)


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
