import datetime
import pandas as pd
from dataclasses import asdict


def dataclass_to_dict(obj) -> dict:
    """
    Convert a dataclass instance to dictionary, excluding fields with None values.

    This utility function is used to serialize dataclass objects for YAML output,
    ensuring that optional fields with no value are omitted from the final output.

    Args:
        obj: A dataclass instance to be converted to a dictionary.

    Returns:
        dict: A dictionary containing only the non-None fields from the dataclass.
    """
    return {k: v for k, v in asdict(obj).items() if v is not None}


def convertStringToTimeDelta(deltatime: str) -> datetime.timedelta:
        '''
        Converts string in timedelta format to datetime.timedelta

        Args:
            deltatime (str): string in timedelta format

        Returns:
            datetime.timedelta
        '''

        duration = pd.Timedelta(deltatime).to_pytimedelta()  #String to timedelta using a pandas library
        return duration

def convert_datetime_to_string(obj):
    """
    Recursively convert datetime/timedelta objects to strings.

    Args:
        obj: Arbitrary nested structure containing datetime values.

    Returns:
        Any: Same structure with serialized datetimes.
    """
    if isinstance(obj, datetime.datetime):
        return obj.strftime("%Y-%m-%d %H:%M:%S")
    if isinstance(obj, datetime.timedelta):
        return str(obj)
    if isinstance(obj, dict):
        return {key: convert_datetime_to_string(value) for key, value in obj.items()}
    if isinstance(obj, list):
        return [convert_datetime_to_string(item) for item in obj]
    return obj