import json
import os
import orjson


class configuration_for_users:

    def save_config(self, jsonfile):
        with open("UserConfigs.json", "wb") as f:
            f.write(orjson.dumps(jsonfile,option=orjson.OPT_INDENT_2))

        if os.path.exists("UserConfigs.json"):
            return True

        if not os.path.exists("UserConfigs.json"):
            return False




















