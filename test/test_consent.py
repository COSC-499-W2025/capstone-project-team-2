import os
import tempfile
import zipfile
import shutil
import unittest



class TestConsent(unittest.TestCase):

    def setUp(self):
        # create a fresh temporary directory and switch to it so extractFiles writes to './temp'
        self.temp_dir = tempfile.mkdtemp()
        self.original_cwd = os.getcwd()
        os.chdir(self.temp_dir)

        # create a simple zip file containing one file
        self.zip_path = os.path.join(self.temp_dir, "sample.zip")
        with zipfile.ZipFile(self.zip_path, "w") as zf:
            zf.writestr("a.txt", "hello")

        # expected extraction directory created by extractFiles()
        self.expected_extract_dir = os.path.join(self.temp_dir, "temp")

    def tearDown(self):
        # return to original cwd and remove temp dir
        os.chdir(self.original_cwd)
        if os.path.exists(self.temp_dir):
            shutil.rmtree(self.temp_dir)

    def test_default_consent_is_false(self):
        instance = extractInfo(self.zip_path)
        # by default there should be no consent flag set (or it should be False)
        self.assertFalse(getattr(instance, "consent", False))

    def test_extract_without_consent_raises(self):
        instance = extractInfo(self.zip_path)
        # calling extractFiles without consent must raise a permission-like error
        with self.assertRaises(PermissionError):
            instance.extractFiles()

    def test_extract_with_constructor_consent_succeeds(self):
        # if constructor accepts consent=True the extraction should proceed
        instance = extractInfo(self.zip_path, consent=True)
        instance.extractFiles()
        # extracted file should exist inside expected_extract_dir
        files = os.listdir(self.expected_extract_dir)
        self.assertTrue(len(files) > 0)

    def test_grant_consent_then_extract_succeeds(self):
        instance = extractInfo(self.zip_path)
        # if the API provides a grant_consent method it should allow extraction
        # this test assumes such a method will be added
        instance.grant_consent()
        instance.extractFiles()
        self.assertTrue(os.path.exists(os.path.join(self.expected_extract_dir, "a.txt")))

    def test_invalid_consent_value_raises(self):
        # passing a non-boolean consent value should raise a TypeError at construction
        with self.assertRaises(TypeError):
            extractInfo(self.zip_path, consent="yes")


if __name__ == "__main__":
    unittest.main()