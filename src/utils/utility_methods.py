import datetime
import pandas as pd

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