import unittest
from pathlib import Path
from src.AI_anlysis_code import code_analysis_AI

class TestAIOutput(unittest.TestCase):


    def setUp(self):
        root_folder = Path(__file__).parent.resolve()
        self.folder=root_folder / "test" / "tiny_scripts"
        self.instance=code_analysis_AI(self.folder)


    def test_AI_output(self):
        result=self.instance.run_analysis()
        print(result)
        self.assertIn()