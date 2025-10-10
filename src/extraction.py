import shutil
import zipfile
import os
from pathlib import Path



def test():
    """
       Send a message to a recipient.

       :param str sender: The person sending the message
       :param str recipient: The recipient of the message
       :param str message_body: The body of the message
       :param priority: The priority of the message, can be a number 1-5
       :type priority: integer or None
       :return: the message id
       :rtype: int
       :raises ValueError: if the message_body exceeds 160 characters
       :raises TypeError: if the message_body is not a basestring
       """



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

        :param str zipfilePath : path to the ZIP file

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
