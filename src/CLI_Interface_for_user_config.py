import orjson
from rich import print
from Configuration import configuration_for_users


json_file=configuration_for_users()


sample_json={
    "ID": 1,
    "First Name": "Jane",
    "Student id": "2003357",
    "Last Name": "Doe",
    "Email": "Jane.Doe@gmail.com",
    "Role": "Student",
    "Preferences": {
        "theme": "dark"
    }
}


#loaded_Json=orjson.loads(sample_json)

while True:
    print("------------------------")
    for index, (key, value) in enumerate(sample_json.items()):

        print(index+1, key, value)
    print("------------------------")


    try:
        setting_to_change = int(input("Please select a which setting you want to change:"))

        if setting_to_change is not None:
            chosenSetting = list(sample_json.keys())[setting_to_change - 1]
            if chosenSetting == "ID":
                print("[bold red] ERROR:[/bold red], you cannot modified your ID")

            else:
                currentEntry = sample_json.get(chosenSetting)
                print(f"Current setting for {chosenSetting} are {currentEntry}")
                modify = str(input("Do want to modify this: (yes or no):"))
                if modify == 'yes':
                    new_update = str(input("what would like to update this with:"))

                    sample_json[chosenSetting] = new_update
                    print(f"{chosenSetting} with {currentEntry} has been changed to {new_update}")
                    json_file.save_config(sample_json)
                else:
                    print("[bold red] ERROR:[/bold red],Please choose (yes or no)")

    except IndexError:
        print("[bold red] ERROR:[/bold red],Please select a valid choice")








#print("Hello, [bold magenta]World[/bold magenta]!", ":vampire:")



