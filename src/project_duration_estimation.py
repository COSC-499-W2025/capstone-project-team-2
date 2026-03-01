import datetime

class Project_Duration_Estimator:
    '''
    Class for estiamting the duration of a project after the files have had metadata extracted
    Takes dictionary format of file hieracrhy on initialization and extracts "created" and "modified" dates from the files to create an estimate of project duration.

    self.start_estimate stores the start date. Can be modified for future scenarios of user input.
    self.end_estimate stores the end date. Can be modified for future scenarios of user input.
    get/set functions are not designed for these yet.

    get_duration() returns the project duration.
    '''


    def __init__(self, hierarchy: dict):
        '''
        Takes in hierarchy of files with metadata upon initialization and pulls the datetime information neccessary
        '''
        self.hierarchy = hierarchy  #stores hierarchy for use
        self.__list_dates()
        if (self.created_dates.count == 0 or self.mod_dates == 0):  #Ensures that error is raised at relevant time if there are no files to pull dates from
            raise Exception("No files found. Estimate cannot be made.")
        else: 
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
        Function that takes a file from the recursive method list_dates_recursive and extracts the creation and last modified dates of files
        '''
        self.created_dates.append(file["created"])
        self.mod_dates.append(file["modified"])

    def __find_duration(self):
        '''
        Takes a list of creation dates and last modified dates of files, finding the earliest creation date and latest last modified date for the use of estimating project length.
        '''
        start_estimate = self.created_dates[0]  #Starter for earliest creation date
        end_estimate = self.mod_dates[0]    #Starter for latest last modified date
        for date in self.created_dates: #Finds earliest creation date
            if date < start_estimate:
                start_estimate = date

        for date in self.mod_dates: #Finds latest last modified date
            if date > end_estimate:
                end_estimate = date

        self.start_estimate = start_estimate
        self.end_estimate = end_estimate

    def get_duration(self) -> datetime.timedelta:
        '''
        Returns a datetime.timedelta showing the project duration estimate.
        '''
        return self.end_estimate - self.start_estimate

