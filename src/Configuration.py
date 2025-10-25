import json
import os
import orjson


class configuration_for_users:

    def __init__(self,jsonfile):
        self.jsonfile = jsonfile

    def save_config(self):
        with open("UserConfigs.json", "wb") as f:
            f.write(orjson.dumps(self.jsonfile,option=orjson.OPT_INDENT_2))

        if os.path.exists("UserConfigs.json"):
            return True

        if not os.path.exists("UserConfigs.json"):
            return False




















