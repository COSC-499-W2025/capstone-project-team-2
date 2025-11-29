

class ai_data_scrubber:
    
    def __init__(self, analysis: dict) -> dict:
        pass

    def _remove_sentence_data(self, data: list, tolerance=0) -> list:
        no_sentence_list = list()
        for string in data:
            if not (string.type() == str):
                pass
            if string.count(" ") > tolerance:
                pass
            no_sentence_list.append(string)
        return no_sentence_list


    def _clip_sentences_off_data(self, data: list, tolerance: int) -> list:
        pass

    def _gather_unique(self, data: list, casing="lower") -> list:
        '''
        Returns a list of unique strings from another list

        parameters:
            data: list of strings
            casing: default "lower". sets string to lowercase for comparison and outputs as such. "upper" converts to uppercase. Any other string will result in no casing being applied for comparison and output which could leave duplicates of differing casing.

        return:
            returns a list of unique strings from data
        '''
        unique_list = list()
        for item in data:
            if not (item.type() == str):
                pass
            if casing == "lower":
                item = item.lower()
            elif casing == "upper":
                item = item.upper()
            if item not in unique_list:
                unique_list.append(item)
        return unique_list

    def _remove_similar_data(self, data: list) -> list:
        pass

    def _gather_from_dict(self, dictionary: dict, key: str) -> list:
        '''
        Iterates over every files analysis to gather all elements from specified key into a list.

        paramters:
            dictionary: unprocessed dictionary from ollama AI analysis
            key: dictionary index/key to gather data into list from

        return:
            list of all data from key value. Not unique.
        '''
        value_list = list()
        for name, value in dictionary.items():
            if key in value:
                if type(value[key]) is list:
                    value_list.extend(value[key])
                else:
                    value_list.append(value[key])
        return value_list