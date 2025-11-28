

class ai_data_scrubber:
    
    def __init__(self, analysis: dict) -> dict:
        pass

    def _remove_sentence_data(self, data: list, tolerance: int) -> list:
        pass

    def _clip_sentences_off_data(self, data: list, tolerance: int) -> list:
        pass

    def _gather_unique(self, data: list, casing: str) -> list:
        pass

    def _remove_similar_data(self, data: list) -> list:
        pass

    def _gather_from_dict(self, dictionary: dict, key: str) -> list:
        value_list = list()
        for name, value in dictionary.items():
            if key in value:
                if type(value[key]) is list:
                    value_list.extend(value[key])
                else:
                    value_list.append(value[key])
        return value_list