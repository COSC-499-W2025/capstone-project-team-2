from pathlib import Path

from src.extraction import extractInfo
import asyncio

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
        self.timeout = 10

    async def timeout_input(self, prompt:str, timeout:int):
        try:
            return await asyncio.wait_for(asyncio.to_thread(input,prompt),timeout)

        except asyncio.TimeoutError:
            print(f"\nInput timed out after {timeout} seconds. Returning you back to main menu.\nPress enter to continue...")
            return None

    async def run_zip_interface(self):
        """
         Runs the main CLI interface for ZIP file extraction.
         """
        file_path_to_extract = await self.timeout_input(""
                                                        "Please enter the path to the ZIP file you want to extract (or type 'q' to quit): ",self.timeout)
        if file_path_to_extract is None:
            return "Timeout"

        file_path_to_extract = file_path_to_extract.strip()

        if file_path_to_extract!='q' and file_path_to_extract!="Q":
            doc=Path(file_path_to_extract).name
            messages=extractInfo(file_path_to_extract).runExtraction()
            if "Error!" in messages:
                print(messages)
                print("Please try again")
                self.retries += 1
                # No explicit return -> None, run_cli will loop again
                return None

                # No error in messages → success
            print(f"{doc} has been extracted successfully")
            print("Returning you back to main screen")
            return "extraction_successful"

        else:
            print("Exiting zip Extraction. Returning you back to main screen")
            return "Exit"


    async def run_cli(self,max_retries=3):
        """
        Here is where the main CLI loop runs until a valid ZIP file is extracted
        or the user decides to exit.

        :param max_retries: This is the number of times to retry that a user can do
        :return:
        """

        while self.retries <= max_retries: # Loop until a valid ZIP file is extracted or max retries reached which is 3 by default
            print(f'try: {self.retries}/{max_retries}')
            result = await self.run_zip_interface()
            # Here I am calling the run_zip_interface method to start the zip extraction process and storing return messages

            if result == "extraction_successful":
                break

            if result == "Exit" or result == "Timeout":
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
    asyncio.run(cli.run_cli())