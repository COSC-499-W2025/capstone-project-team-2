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

    def __init__(self, zipfilePath):

        """
        Initializes the extractor with file path to the
        ZIP file/archive

        parameters
        ----------
        ZipfilePath: path to the ZIP file

        """

        self.zipfilePath = zipfilePath

    def extractFiles(self):
        """
        Extracts the contents of the defined ZIP file/archive
        into a 'temp' directory in current working directory.

        The method create a folder called 'temp' in the current
        working directory if it does not exist than from this it
        performs extraction where the extracted files are placed
        into the 'temp' folder


        Raises
        ------
        if the entered zip file path is not found or not valid
        it raises FileNotFoundError

        if the entered zip file is either invalid or corrupted
        it raise the zipfile.BadZipFile exception from ZipFile

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
