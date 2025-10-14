import os
import tempfile
import shutil
import unittest

class TestUserConfigStore(unittest.TestCase):
    def setUp(self):
        self.temp_dir=tempfile.mkdtemp()
        self