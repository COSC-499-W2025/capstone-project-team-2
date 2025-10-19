import json
import os
import orjson


class configuration_for_users:

    def save_config(self, jsonfile):
        #os.makedirs("UserConfigs", exist_ok=True)

        #save_path = os.path.join("UserConfigs", "UserConfig.json")
        with open("UserConfigs.json", "wb") as f:
            f.write(orjson.dumps(jsonfile,option=orjson.OPT_INDENT_2))



















