import shutil
import zipfile
import os, time
import tempfile
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

    @staticmethod
    def _build_extraction_dir(file_name: str) -> str:
        """
        Create a unique extraction directory under the OS temp folder.

        Args:
            file_name: Base project/archive name used as prefix.

        Returns:
            str: Absolute extraction directory path.
        """
        safe_name = "".join(ch if ch.isalnum() or ch in {"-", "_"} else "_" for ch in file_name)
        base_tmp = Path(tempfile.gettempdir()) / "devdoc_extracts"
        base_tmp.mkdir(parents=True, exist_ok=True)
        return tempfile.mkdtemp(prefix=f"{safe_name}_", dir=str(base_tmp))

    def runExtraction(self, zip_file: Path | UploadFile) -> str:
        """
        Method that runs all zip extraction protocols

        Args:
            zipfile (Path | UploadFile): File path or file-like object that contains a zip file to be extracted.
        """
        error = self.verifyZIP(zip_file)
        if error != None:
            return error
        if (isinstance(zip_file, Path)):
            file_name: str = zip_file.stem
        else:   #Must be UploadFile if not Path
            upload_name = zip_file.filename or "uploaded_project.zip"
            file_name = Path(upload_name).stem
        temp_path = self.extractFiles(zip_file, file_name)
        error = self.validateExtractedFiles(temp_path)
        if error != None:
            shutil.rmtree(temp_path, ignore_errors=True)
            return error
        return temp_path

    def extractFiles(self, zip_file: Path | UploadFile, file_name: str) -> str:
        """
        Extract ZIP contents into a unique directory under OS temp storage.

        Returns:
            str: Absolute path to extracted directory.
        """


        if isinstance(zip_file, Path):
            file = str(zip_file)
        else:   #Must be UplaodFile if not Path
            file = zip_file.file
            try:
                file.seek(0)
            except Exception:
                pass

        temp_file_path = self._build_extraction_dir(file_name)
        with zipfile.ZipFile(file, 'r') as zip_ref:
            zip_ref.extractall(temp_file_path)
        self.RestoreTimestampsOfZipContents(zip_file, temp_file_path)
        return temp_file_path

    def RestoreTimestampsOfZipContents(self, zipname, extract_dir):
        for f in zipfile.ZipFile(zipname, 'r').infolist():
            # path to this extracted f-item
            fullpath = os.path.join(extract_dir, f.filename)
            # still need to adjust the dt o/w item will have the current dt
            date_time = time.mktime(f.date_time + (0, 0, -1))
            # update dt
            os.utime(fullpath, (date_time, date_time))

    def verifyZIP(self, zip_file: Path | UploadFile) -> str | None:
        """
        Tests that file is a valid zip file

        Args:
            zip_file(Path | UploadFile): Path or file-like object to be ensured is a zip file

        Return None if file is validated, or error text if file invalid
        """
        if isinstance(zip_file, Path):
            file = str(zip_file)
            if not os.path.exists(file):    #Checks filepath
                return self.PATH_ERROR_TEXT + file
        else:   #Must be UploadFile if not Path
            file = zip_file.file
        if not zipfile.is_zipfile(file):    #checks if zip file is a zip file
            return self.NOT_ZIP_ERROR_TEXT
        try:
            with zipfile.ZipFile(file, 'r') as zip_test:
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
