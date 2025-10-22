import orjson

class LoadConfigs:
    def LoadUserConfigs(self):
        default_user_configs = "user_configs.json"
        with open(UserConfigs.json, "rb") as f:  # Open in binary read mode ('rb')
            json_bytes = f.read()
        

    def LoadDefaultConfigs(self):
        default_user_configs = "default_user_configs.json"
        with open(default_user_configuration.json, "rb") as f:  # Open in binary read mode ('rb')
            json_bytes = f.read()

    try:
        LoadUserConfigs(self)
    except Exception as e:
        LoadDefaultConfigs(self)
        print("No User Settings Saved:", e)
    


