from pathlib import Path

from src.extraction import extractInfo

#Todo:
# - Have the ability for user to upload multiple zip files at once (Optional)
# - TimeOut feature for user input (Optional)


class  zipExtractionCLI():
    """
    Command-line interface (CLI) class for extracting ZIP files.

    This class provides a simple user interface that allows users to input
    the path of a ZIP file and automatically extract its contents using the
    `extractInfo` class. The process continues until a valid ZIP file is
    successfully extracted.

    """
    def __init__(self):
        # Initializing the retries counter to 1 ant the start of the program
        self.retries = 1


    def run_zip_interface(self):
        """
        Runs the main CLI interface for ZIP file extraction.
        """
        file_path_to_extract = input("Please upload the project folder or type q to exit:")

        if file_path_to_extract != "q":
            # Asking the users for the file p
            doc = Path(file_path_to_extract).name
            # Finding the uploaded zips file name
            messages = extractInfo(file_path_to_extract).runExtraction()
            # Here I am running the extraction class to extract the zip file and also getting an
            #Error message if there is any

            if "Error!" in messages:
                print(messages)
                print("Please try again")
                self.retries += 1
            # Here, if there is an error message, it prints it out and also increments the retries counter

            if "Error!" not in messages:
                print(f"{doc} has been extracted successfully")
                print("Returning you back to main screen")
                return "extraction_successful"
            # Here is there is no error message it prints out a success message then returns A successful extraction message

        if file_path_to_extract == 'q':
            print("Exiting zip Extraction Returning you back to main screen")
            return "Exit"

            # Here when the user types q,the program breaks out of the loop



        return None

    def run_cli(self,max_retries=3):
        """
        Here is where the main CLI loop runs until a valid ZIP file is extracted
        or the user decides to exit.

        :param max_retries: This is the number of times to retry that a user can do
        :return:
        """

        while self.retries <= max_retries: # Loop until a valid ZIP file is extracted or max retries reached which is 3 by default
            print(f'try: {self.retries}/{max_retries}')
            result = self.run_zip_interface()
            # Here I am calling the run_zip_interface method to start the zip extraction process and storing return messages

            if result == "extraction_successful":
                break

            if result == "Exit":
                break

        """
         Here, if the user exceeds the maximum number of retries, it prints an exit message 
         returns the user back to the main screen
        """
        if self.retries>=max_retries:
            print("Too many invalid attempts. Exiting...")


if __name__ == "__main__":
    # Only runs when you execute this file directly:
    # python -m src.CLI_interface_for_file_extraction
    cli = zipExtractionCLI()
    cli.run_cli()