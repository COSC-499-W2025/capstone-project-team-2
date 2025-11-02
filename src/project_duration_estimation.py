import datetime

class Project_Duration_Estimator:

    def __init__(self, hierarchy: dict):
        self.hierarchy = hierarchy
        self.__list_dates()
        self.__find_duration()

    def __list_dates(self):
        self.created_dates = []
        self.mod_dates = []

        self.__list_dates_recurse(self.hierarchy)

    def __list_dates_recurse(self, node: dict):
        for file in node["children"]:
            if file["type"] != "DIR":
                self.__add_file_dates(file)
            else:
                self.__list_dates_recurse(file)

    def __add_file_dates(self, file: dict):
        self.created_dates.append(file["created"])
        self.mod_dates.append(file["modified"])

    def __find_duration(self):
        start_estimate = self.created_dates[0]
        end_estimate = self.mod_dates[0]
        for date in self.created_dates:
            if date < start_estimate:
                start_estimate = date

        for date in self.mod_dates:
            if date > end_estimate:
                end_estimate = date

        self.start_estimate = start_estimate
        self.end_estimate = end_estimate
        self.duration_estiamte = end_estimate - start_estimate

    def get_duration(self) -> datetime.timedelta:
        return self.duration_estiamte

