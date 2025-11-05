from pathlib import Path

from src.extraction import extractInfo
import zipfile
import os


class  zipExtractionCLI():
    """
    Command-line interface (CLI) class for extracting ZIP files.

    This class provides a simple user interface that allows users to input
    the path of a ZIP file and automatically extract its contents using the
    `extractInfo` class. The process continues until a valid ZIP file is
    successfully extracted.

    """


    def run_cli(self,max_retries=3):
        """

        :param max_retries: This is the number of times to retry that a user can do
        :return:
        """
        retires=1
        while retires <= max_retries:
            print(f'try: {retires}/{max_retries}')
            file_path_to_extract=input("Please upload the project folder or type q to exit:")
            #Asking the users for the file p
            doc=Path(file_path_to_extract).name
            #Finding the uploaded zips file name
            messages=extractInfo(file_path_to_extract).runExtraction()
            # Here I am running the extraction class

            if file_path_to_extract=='q':
                print("Exiting zip Extraction Returning you back to main screen")
                break
                #Here when the user types q  the program breaks out of the loop

            if "Error!" in messages:
                print(messages)
                retires += 1

            if "Error!" not in messages:
                print(f"{doc} has been extracted successfully")
                print("Returning you back to main screen")
                break


        if retires>=max_retries:
            print("Too many invalid attempts. Exiting...")


if __name__ == "__main__":
    # Only runs when you execute this file directly:
    # python -m src.CLI_interface_for_file_extraction
    cli = zipExtractionCLI()
    cli.run_cli()