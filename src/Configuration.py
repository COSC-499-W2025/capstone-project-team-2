import json
import os


class configuration_for_users:

    def save_config(self, jsonfile):
        #os.makedirs("UserConfigs", exist_ok=True)

        #save_path = os.path.join("UserConfigs", "UserConfig.json")
        with open("UserConfigs.json", "w", encoding="utf-8") as f:
            json.dump(jsonfile, f, indent=4)









