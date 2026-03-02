from typing import assert_type
import unittest
import pytest
import datetime

from src.utils.utility_methods import *

def test_converting_string_to_timedelta():
    """
    Test ensures method converts correctly to identical timedelta object

    Args:
        None
    """
    original = datetime.timedelta(days=2)   #Builds timedelta
    string_original = str(original)
    assert convertStringToTimeDelta(string_original) == original    #Asserts oriignal timedelta is identical to one converted back from string

def test_convert_datetime_objects_to_strings():
    """
    Test ensures that both datetime and timedelta objects get converted to strings

    Args:
        None
    """
    original = {"datetime": datetime.datetime.now(), "timedelta": datetime.timedelta(days=2)}
    converted: dict = convert_datetime_to_string(original)

    assert_type(converted["datetime"], str)
    assert_type(converted["timedelta"], str)

def test_convert_datetime_to_string_with_no_datetime_objects():
    """
    Ensures persistance of non-datetime objects through conversion

    Args:
        None
    """
    original = {"int": 3, "string": "string", "float": 2.3}
    converted: dict = convert_datetime_to_string(original)

    assert converted == original