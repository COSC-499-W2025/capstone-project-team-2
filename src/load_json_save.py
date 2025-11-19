import json
import os, datetime, pandas as pd

class SaveLoader:

    def __init__(self, json_filepath):
        with open(json_filepath, 'r') as file:
            self.json_text = file.read()