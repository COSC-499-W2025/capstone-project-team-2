import zipfile
import os
class extractInfo:


    """
    This is class function that takes in a zip folder
    and extract the contents to temporary folder to be used in further
    analysis
    """


    """
    parameters:
    zipFilePath: str
    """
    def __init__(self,zipfilePath):
        self.zipfilePath = zipfilePath



    """
    This is a function which makes a temporary folder if it does not exist in the program
    then peforem extaction on the given zip file
    
    """
    def extraction(self):
        workingdirectory=os.getcwd()
        os.makedirs("temp",exist_ok=True)
        temp_file_path=os.path.join(workingdirectory,"temp")
        with zipfile.ZipFile(self.zipfilePath, 'r') as zip_ref:
            zip_ref.extractall(temp_file_path)


