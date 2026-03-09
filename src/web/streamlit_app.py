"""
This is the main file for our streamlit app
in other words this is where stuff is displayed firsst

"""



import sys
from pathlib import Path

import streamlit as st

# Add project root to path so we can import src.web modules.
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from src.web.theme import apply_theme_from_config

apply_theme_from_config()

st.title("Hello World")
st.write("CAPSTONE 499 project Team 2 (Data mining software)")
