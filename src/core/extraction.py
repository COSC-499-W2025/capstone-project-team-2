import shutil
import zipfile
import os
from pathlib import Path
from fastapi import UploadFile



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
    CORRUPT_FILE_ERROR_TEXT = "Error! Corrupt file detected - invalid header: "

    # Magic bytes for file type validation
    MAGIC_BYTES = {
        '.png': b'\x89PNG\r\n\x1a\n',
        '.jpg': b'\xff\xd8\xff',
        '.jpeg': b'\xff\xd8\xff',
        '.gif': b'GIF8',
        '.pdf': b'%PDF',
        '.zip': b'PK\x03\x04',
    }

    def runExtraction(self, zip_file: Path | UploadFile) -> str:
        """
        Method that runs all zip extraction protocols

        Args:
            zipfile (Path | UploadFile): File path or file-like object that contains a zip file to be extracted.

        Returns:
            str: returns errors encountered, otherwise returns the string path for the temp folder that files were extracted to
        """
        error = self.verifyZIP(zip_file)
        if error != None:
            return error
        if (isinstance(zip_file, Path)):
            file_name: str = zip_file.stem
        elif isinstance(zip_file, UploadFile):
            file_name: str = zip_file.filename.split(".")[0] #Should return the file name without the extension
        self.extractFiles(zip_file, file_name)  
        temp_path = os.path.join(os.getcwd(), file_name)
        error = self.validateExtractedFiles(temp_path)
        if error != None:
            return error
        return temp_path
        

    def extractFiles(self, zip_file: Path | UploadFile, file_name: str):
        """
        Extracts the contents of the defined ZIP file/archive
        into a directory in current working directory named after the zip file.

        The method create a folder called 'temp' in the current
        working directory if it does not exist than from this it
        performs extraction where the extracted files are placed
        into the 'temp' folder

        """

        if isinstance(zip_file, Path):
            zip_file = str(zip_file)

        workingdirectory = os.getcwd()
        os.makedirs(file_name, exist_ok=True)
        temp_file_path = os.path.join(workingdirectory, file_name)
        with zipfile.ZipFile(zip_file, 'r') as zip_ref:
            zip_ref.extractall(temp_file_path)

    def verifyZIP(self, zip_file: Path | UploadFile) -> str | None:
        """
        Tests that file is a valid zip file

        Args:
            zip_file(Path | UploadFile): Path or file-like object to be ensured is a zip file

        Return None if file is validated, or error text if file invalid
        """
        if isinstance(zip_file, Path):
            zip_file = str(zip_file)
            if not os.path.exists(zip_file):    #Checks filepath
                return self.PATH_ERROR_TEXT + zip_file
        if not zipfile.is_zipfile(zip_file):    #checks if zip file is a zip file
            return self.NOT_ZIP_ERROR_TEXT
        try:
            with zipfile.ZipFile(zip_file, 'r') as zip_test:
                bad_file = zip_test.testzip()   #Checks for corruption in zip file
                if (bad_file == None):
                    return None
                return self.BAD_FILE_ERROR_TEXT + bad_file
        except zipfile.BadZipFile:  #Catches corrupted zip files
            return self.BAD_ZIP_ERROR_TEXT

    def validateExtractedFiles(self, temp_path: str) -> str | None:
        """
        Validates extracted files by checking their magic bytes (file signatures).

        :param temp_path: Path to the directory containing extracted files
        :return: None if all files are valid, or error text if a corrupt file is detected
        """
        for root, dirs, files in os.walk(temp_path):
            for file in files:
                # Skip macOS resource fork files to avoid false corruption errors
                if file.startswith("._") or "__MACOSX" in root:
                    continue

                filepath = os.path.join(root, file)
                ext = os.path.splitext(file)[1].lower()

                if ext in self.MAGIC_BYTES:
                    expected_magic = self.MAGIC_BYTES[ext]
                    try:
                        with open(filepath, 'rb') as f:
                            header = f.read(len(expected_magic))
                            if header != expected_magic:
                                return self.CORRUPT_FILE_ERROR_TEXT + filepath
                    except Exception:
                        return self.CORRUPT_FILE_ERROR_TEXT + filepath
        return None

