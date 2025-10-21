import time

import orjson
from rich import print
from src.Configuration import configuration_for_users


class ConfigurationForUsersUI:
    def __init__(self, Configuration_json):
        self.Configuration_json = Configuration_json


    def display_settings(self):
        """
        Displays the current configuration settings to the console

        This method prints out the current configuration settings in a key-pair format
        with index associated with each one

        """
        print("------------------------")
        for index, (key, value) in enumerate(self.Configuration_json.items()):
            print(f"{index+1} - {key} : {value}")
        print("------------------------")


    def get_setting_choice(self):
        """
        :return:
            str: The chosen setting key or q for exiting this particular program
        :raises:
            IndexError: If choice is out of range
            ValueError: If choice is not a number

    """
        Setting_to_change = input("Please choose a setting you want to change or type q:")

        if Setting_to_change == "q":

            return "Quit"

        elif Setting_to_change is not None:
            chosen_setting = list(self.Configuration_json.keys())[int(Setting_to_change) - 1]
            return chosen_setting




    def validate_modifiable_field(self,chosen_setting):
        """
        Validates whether a selected configuration filed can be modified which in this case is ID

        :param chosen_setting:
        :raises Exception: If the chosen setting is not modifiable (e.g., 'ID').

        """


        if chosen_setting == "ID":
            raise Exception("ID cannot be modified")


    def confirm_modification(self,chosen_setting, current_value):
        """
        Ask user to confirm modification

        :param chosen_setting:
        :param current_value:
        :return:
            str or None: New value if confirmed, None if declined
        """
        print(f"Current setting: {chosen_setting} is {current_value}")
        confirmed = False

        while not confirmed:
            modify = str(input("Would you like to modify this setting? (y/n) "))
            if modify == "y":
                confirmed = True
                new_update = str(input(f"Please enter your new value you want to update {chosen_setting}:"))
                return new_update

            elif modify == "n":
                print("[bold red] ERROR:[/bold red],Please choose (yes or no)")
                time.sleep(1.5)





    def modify_settings(self, chosen_setting, json_class):
        """

        :param setting_json:
        :param chosen_setting:
        :return:
            bool: True if modification was successful, False otherwise

        """
        current_entry = self.Configuration_json.get(chosen_setting)
        new_update = self.confirm_modification(chosen_setting, current_entry)
        if new_update is not None:
            self.Configuration_json[chosen_setting] = new_update
            print(f"{chosen_setting} is now set from {current_entry} to {new_update}")
            json_class.save_config(self.Configuration_json)
            time.sleep(1.5)
            return True

        return False


    def run_configuration_cli(self):
        """
        Main function to run the configuration CLI
        """

        json_functions = configuration_for_users()

        while True:
            self.display_settings()
            try:
                chosen_setting = self.get_setting_choice()
                if chosen_setting=='Quit':
                    print("Returning you back to main page")
                    break

                self.validate_modifiable_field(chosen_setting)
                self.modify_settings(chosen_setting, json_functions)



            except IndexError:
                print("[bold red] ERROR:[/bold red],Please select a valid choice")
                time.sleep(1.5)
            except ValueError:
                print("[bold red] ERROR:[/bold red],Please enter a valid number")
                time.sleep(1.5)

            except Exception as e:
                print(f"[bold red] ERROR:[/bold red], {str(e)}")
                time.sleep(1.5)

            except KeyboardInterrupt:
                print("\n[bold yellow]Exiting configuration...[/bold yellow]")
                break


if __name__ == "__main__":
    sample_json = {
        "ID": 1,
        "First Name": "Jane",
        "Student id": "2003357",
        "Last Name": "Doe",
        "Email": "Jane.Doe@gmail.com",
        "Role": "Student",
        "Preferences": {
            "theme": "dark"
        }}

    UI=ConfigurationForUsersUI(sample_json)
    UI.run_configuration_cli()
    #ConfigurationForUsersUI.run_configuration_cli(sample_json)
