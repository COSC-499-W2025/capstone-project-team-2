import shutil
import zipfile
import os
from pathlib import Path



class extractInfo:
    """
    This is a helper class that is for extracting the
    contents of a ZIP file into a temporary directory for
    further processing

    """

    PATH_ERROR_TEXT = "Error! File not found at path: "
    NOT_ZIP_ERROR_TEXT = "Error! File at path is not a ZIP file:\n"
    BAD_FILE_ERROR_TEXT = "Error! Zip file contains bad file: "
    BAD_ZIP_ERROR_TEXT = "Error! Zip file is bad!"

    def __init__(self, zipfilePath):

        """
        Initializes the extractor with file path to the
        ZIP file/archive

        :param str zipfilePath : path to the ZIP file

        """

        self.zipfilePath = zipfilePath

    def runExtraction(self) -> str:
        """
        Method that runs all extraction protocols

        Returns any errors encountered, otherwise returns the path for the temp folder that files were extracted to
        """
        error = self.verifyZIP()
        if error != None:
            return error
        self.extractFiles()
        return os.path.join(os.getcwd(), "temp")

    def extractFiles(self):
        """
        Extracts the contents of the defined ZIP file/archive
        into a 'temp' directory in current working directory.

        The method create a folder called 'temp' in the current
        working directory if it does not exist than from this it
        performs extraction where the extracted files are placed
        into the 'temp' folder

        :raises FileNotFoundError: if the entered zip file path is not found or not vaild
        :raises zipfile.BadZipFile: if the entered zip file is invalid or corrupted

        """


        if not os.path.exists(self.zipfilePath):
            raise FileNotFoundError(f'ZIP file: {self.zipfilePath} not found please make sure of the file path')

        if not zipfile.is_zipfile(self.zipfilePath):
            raise zipfile.BadZipFile(f"{self.zipfilePath} is either Invalid or corrupted  ")



        workingdirectory = os.getcwd()
        os.makedirs("temp", exist_ok=True)
        temp_file_path = os.path.join(workingdirectory, "temp")
        with zipfile.ZipFile(self.zipfilePath, 'r') as zip_ref:
            zip_ref.extractall(temp_file_path)

    def verifyZIP(self) -> str:
        """
        Tests that file at self.zipfilePath is a valid zip file

        Return None if file is validated, or error text if file invalid
        """
        if not os.path.exists(self.zipfilePath):    #Checks filepath
            return self.PATH_ERROR_TEXT + self.zipfilePath
        if not zipfile.is_zipfile(self.zipfilePath):    #checks if zip file is a zip file
            return self.NOT_ZIP_ERROR_TEXT + self.zipfilePath
        try:
            with zipfile.ZipFile(self.zipfilePath, 'r') as zip_test:
                bad_file = zip_test.testzip()   #Checks for corruption in zip file
                if (bad_file == None):
                    return None
                return self.BAD_FILE_ERROR_TEXT + bad_file
        except zipfile.BadZipFile:  #Catches corrupted zip files
            return self.BAD_ZIP_ERROR_TEXT



