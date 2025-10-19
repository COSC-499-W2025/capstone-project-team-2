import os
import tempfile
import shutil
import unittest
import json
from pathlib import Path


class TestStartupConfigPull(unittest.TestCase):
    """
    This is a Test unit used in testing ability to 
    pull settings from a configuration file at startup

#     """
    def setUp(self):

        """
        This is a setup function that does the following at
        the start of this pytest run:
        - Generates a temporary test directory
        - creates a temporary JSON file inside that directory
        pre-populated with sample user configuration data

        """


    def tearDown(self):
        """
        This function cleans up after the test is complete.
        Does the following:
        -Returns to the original working directory.
        -Removes the temporary folder and its associated
        content.
        """

        os.chdir(self.original_cwd)
        if os.path.exists(self.temp_dir):
            shutil.rmtree(self.temp_dir)


