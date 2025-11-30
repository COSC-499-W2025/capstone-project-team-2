import re

class ai_data_scrubber:
    
    def __init__(self, analysis: dict) -> dict:
        pass

    def _remove_sentence_data(self, data: list, tolerance=0) -> list:
        '''
        Iterates over data and returns a list of strings that aren't sentences

        parameters:
            data: list of strings
            tolerance: defaults to 0. How many spaces to tolerate before determining string is a sentence.

        returns:
            returns a list of strings from data with sentence data removed
        '''
        no_sentence_list = list()
        for string in data:
            if not (string.type() == str):  #If value isn't a string, it shouldn't be in the list
                continue
            if string.count(" ") > tolerance:   #Counts the spaces to find if it's considered a sentence according to tolerance
                continue
            no_sentence_list.append(string)
        return no_sentence_list


    def _clip_sentences_off_data(self, data: list, tolerance=0, character=' ', clip_after_character=False) -> list:
        '''
        Iterates over data and returns all strings with text only until first space (or specified character)
            Tolerance increases the amount of spaces before clipping

        parameters:
            data: list of strings
            tolerance: defaults to 0. How many spaces/specified characters to include before clipping end off.
            character: defaults to space. Can be changed to clip on different characters.
            clip_after_character: default to false. When true, clips after first space/specified character instead of clipping the space/character.

        returns:
            returns a list of strings from data with sentences clipped off
        '''
        clipped_data = list()
        for string in data:
            if not (string.type() == str):  #If value isn't a string, it shouldn't be in the list
                continue
            space_count = 0
            for i in range(0, len(string)):
                if string[i] == character:
                    space_count+=1
                if space_count > tolerance: #once enough spaces are found, we clip the extra sentence off
                    clipped_data.append(string[:i+int(clip_after_character == True)])
                    break
            if space_count <= tolerance:    #adds string if tolerance to clip not met
                clipped_data.append(string)
        return clipped_data


    def _gather_unique(self, data: list, casing="lower") -> list:
        '''
        Iterates over data and returns a list of unique strings from data

        parameters:
            data: list of strings
            casing: default "lower". sets string to lowercase for comparison and outputs as such. "upper" converts to uppercase. Any other string will result in no casing being applied for comparison and output which could leave duplicates of differing casing.

        return:
            returns a list of unique strings from data of unique values
        '''
        unique_list = list()
        for item in data:
            if not (item.type() == str):    #If value isn't a string, it shouldn't be in the list
                continue
            if casing == "lower":
                item = item.lower()
            elif casing == "upper":
                item = item.upper()
            if item not in unique_list:
                unique_list.append(item)
        return unique_list

    def _remove_similar_data(self, data: list, similarity_word_num=2) -> list:
        '''
        Iterates over data to find similar strings and group them. Returns one of each group of similar strings as a list.

        parameters:
            data: list of strings
            similarity_word_num: default of 2. Number of words needed to consider two strings as similar.

        returns:
            list of strings containing shortest strings of each group of similar strings.
        '''
        words_in_data = list()
        for string in data:
            if not (string.type() == str):  #If value isn't a string, it shouldn't be in the list
                data.remove(string)
                continue
            words_in_data.append([string, re.findall(r"\w+", string.lower())])  #Pulls the words out of string, seperating by special characters and spaces
        similar_sets = list()
        for item in words_in_data:
            if len(similar_sets) == 0:  #adds first item so we can start checking for similar items
                similar_sets.append([item])
                continue
            similarity_found = False
            for item_set in similar_sets:
                similarity = 0
                for similar_item in item_set:   #iterates over list of similar items to find if new item is similar to all of them, needs to be all of them in case of extra words
                    if self._compare_word_sets(item, similar_item, similarity_word_num):
                        similarity+=1
                if similarity == len(item_set): #if new item is similar to all of list of similar items, adds it to that list of similar items
                    item_set.append(item)
                    similarity_found = True
                    break
            if similarity_found == False:   #makes new list of similar items if new item doesn't fit into any other list of similar items
                similar_sets.append([item])
        final_set = list()
        for similar_set in similar_sets:    #Pulls shortest item of each list of similar items
            final_set.append(min(similar_set, key=len))
        return final_set

    def _compare_word_sets(self, set1: list, set2: list, words_needed: int) -> bool:
        '''
        Iterates over two lists of words to compare them. Returns whether the count of similar words is >= words_needed.

        paramters:
            set1: list of words
            set2: list of words to compare set1 to
            words_needed: amount of words needed to return true that both sets are similar

        returns:
            true when lists are similar by #"words_needed" strings
        '''
        similar_words = 0
        for word1 in set1:
            for word2 in set2:
                if word1 in word2 or word2 in word1:
                    similar_words+=1
                    break   #breaks for efficiency once similarity found once
            if similar_words >= words_needed:
                return True
        return False


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
                if type(value[key]) is list:    #If value of value[key] is a list, we add all elements of list to value_list instead of a list as one element
                    value_list.extend(value[key])
                else:
                    value_list.append(value[key])
        return value_list