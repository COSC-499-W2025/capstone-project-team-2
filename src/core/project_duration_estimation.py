import datetime

def _format_duration(delta: datetime.timedelta) -> str:
    '''
    Formats a timedelta into a human-readable string.

    Args:
        delta (datetime.timedelta): Duration to format.

    Returns:
        str: Human-readable duration string.
    '''
    total_seconds = delta.total_seconds()
    if total_seconds == 0:
        return "0 seconds"
    if 0 < total_seconds < 1:
        return "less than 1 second"

    sign = ""
    if total_seconds < 0:
        sign = "-"
        total_seconds = abs(total_seconds)

    total_seconds = int(total_seconds)
    days, rem = divmod(total_seconds, 86400)
    hours, rem = divmod(rem, 3600)
    minutes, seconds = divmod(rem, 60)

    parts = []
    if days:
        parts.append(f"{days} day" + ("s" if days != 1 else ""))
    if hours:
        parts.append(f"{hours} hour" + ("s" if hours != 1 else ""))
    if minutes:
        parts.append(f"{minutes} minute" + ("s" if minutes != 1 else ""))
    if seconds or not parts:
        parts.append(f"{seconds} second" + ("s" if seconds != 1 else ""))

    return sign + ", ".join(parts)

class Project_Duration_Estimator:
    '''
    Estimate project duration from file metadata.

    Takes a dictionary hierarchy and extracts "created" and "modified" dates
    from files to estimate project duration.
    '''

    def __init__(self, hierarchy: dict):
        '''
        Takes a hierarchy of files with metadata and pulls the datetime information needed.

        Args:
            hierarchy (dict): hierarchy of files with metadata of last modified dates and created dates

        Returns:
            None
        '''
        self.hierarchy = hierarchy  #stores hierarchy for use
        self.__list_dates()
        if (len(self.created_dates) == 0 and len(self.mod_dates) == 0):  #Ensures that error is raised at relevant time if there are no files to pull dates from
            raise Exception("No files found. Estimate cannot be made.")
        self.__find_duration()

    def __list_dates(self):
        '''
        Recursive method that traverses dictionary of hierarchy for creation and last modified datetimes
        '''
        self.created_dates = [] #list for all creation dates of files
        self.mod_dates = [] #list for all last modified dates of files

        self.__list_dates_recurse(self.hierarchy)   #recursion function helper to this method

    def __list_dates_recurse(self, node: dict):
        '''
        Helper method to recursive function list_dates
        Traverses hierarchy and sends files to have creation dates and last modified dates to be extracted
        '''
        for file in node["children"]:
            if file["type"] != "DIR":
                self.__add_file_dates(file) #Recursively traverses files
            else:
                self.__list_dates_recurse(file) #extracts dates from files

    def __add_file_dates(self, file: dict):
        '''
        Function that takes a file from list_dates_recursive and extracts creation and last modified dates.
        '''
        created = file.get("created")
        modified = file.get("modified")
        if created is not None:
            self.created_dates.append(created)
        if modified is not None:
            self.mod_dates.append(modified)

    def __find_duration(self):
        '''
        Takes lists of creation and last modified dates and finds the earliest and latest
        values to estimate project duration.
        '''
        if self.created_dates:
            start_estimate = self.created_dates[0]  #Starter for earliest creation date
            for date in self.created_dates: #Finds earliest creation date
                if date < start_estimate:
                    start_estimate = date
        else:
            # Fallback: use earliest modified date when created dates are missing
            start_estimate = self.mod_dates[0]
            for date in self.mod_dates:
                if date < start_estimate:
                    start_estimate = date

        if self.mod_dates:
            end_estimate = self.mod_dates[0]    #Starter for latest last modified date
            for date in self.mod_dates: #Finds latest last modified date
                if date > end_estimate:
                    end_estimate = date
        else:
            # Fallback: use latest created date when modified dates are missing
            end_estimate = self.created_dates[0]
            for date in self.created_dates:
                if date > end_estimate:
                    end_estimate = date

        self.start_estimate = start_estimate
        self.end_estimate = end_estimate

    def get_duration(self) -> datetime.timedelta:
        '''
        Returns a datetime.timedelta showing the project duration estimate.

        Args:
            None

        Returns:
            datetime.timedelta: estimation of project duration
        '''
        return self.end_estimate - self.start_estimate

    def get_duration_human(self) -> str:
        '''
        Returns a human-readable duration estimate without microseconds.
        '''
        return _format_duration(self.get_duration())
