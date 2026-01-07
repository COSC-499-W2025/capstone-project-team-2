import re

class ai_data_scrubber:
    '''
    Class that conatins methods to gather and scrub data from ollama AI analysis of project files

    Current output in format:
    new_dict = {
        "design_concepts": design_concepts,
        "structures_used": data_structures,
        "time_complexities_recorded": time_complexities_recorded,
        "space_complexities_recorded": space_complexities_recorded,
        "control_flow_and_error_handling_patterns": control_flow_and_error_handling_patterns,
        "libraries_detected": libraries_detected,
        "inferred_strengths": inferred_strengths
    }
    '''
    
    def __init__(self, analysis: dict):
        '''
        Constructor
        Immediately takes unprocessed ollama AI analysis and gathers and scrubs useful data from it

        Use get_scrubbed_dict to return final dictionary
        '''
        design_concepts = self._gather_from_list(self._gather_from_dict(analysis, "design_and_architecture"), "concepts_observed")  #Gathers "design_and_architecture" dictionaries then pulls "concepts_observed" that is nested in those dictionaries
        design_concepts = self._remove_sentence_data(design_concepts, tolerance=3)  #Removes possible sentences, analysis of a prior output shows that 3 spaces are possible in good data
        design_concepts = self._gather_unique(design_concepts)  #Removes extra values to ensure all values unique
        design_concepts = self._remove_similar_data(design_concepts)    #Removes possible iterations that contain differing special characters

        #Gather dictionaries for contained keys
        data_structures_and_algorithms = self._gather_from_dict(analysis, "data_structures_and_algorithms")

        data_structures = self._gather_from_list(data_structures_and_algorithms, "structures_used")
        data_structures = self._remove_sentence_data(data_structures, tolerance=1)  #Tolerance 1 rationlized by looking at a generated analysis
        data_structures = self._gather_unique(data_structures)
        data_structures = self._remove_similar_data(data_structures, similarity_word_num=1) #Considering data structure names, one similar word should be valid

        time_complexities_recorded = self._gather_from_list(data_structures_and_algorithms, "time_complexity")
        time_complexities_recorded = self._gather_from_list(time_complexities_recorded, "average_case") #Average case used for recorded time complexities. Can add all three later if wanted.
        time_complexities_recorded = self._clip_sentences_off_data(time_complexities_recorded, character=')', clip_after_character=True)    #This use of character ')' should only clip after a big O notation ends
        time_complexities_recorded = self._remove_sentence_data(time_complexities_recorded, tolerance=2)    #nlogn was seen as the max number of spaces at 2, anything more should be sentences with no notation or notation placed in the middle
        time_complexities_recorded = self._gather_unique(time_complexities_recorded, casing="") #We don't want to change the casing to preserve correct big O notation

        space_complexities_recorded = self._gather_from_list(data_structures_and_algorithms, "space_complexity")
        space_complexities_recorded = self._clip_sentences_off_data(space_complexities_recorded, character=')', clip_after_character=True)    #This use of character ')' should only clip after a big O notation ends
        space_complexities_recorded = self._remove_sentence_data(space_complexities_recorded, tolerance=2)    #nlogn was seen as the max number of spaces at 2, anything more should be sentences with no notation or notation placed in the middle
        space_complexities_recorded = self._gather_unique(space_complexities_recorded, casing="") #We don't want to change the casing to preserve correct big O notation

        #Gather dictionaries for contained keys
        control_flow_and_error_handling = self._gather_from_dict(analysis, "control_flow_and_error_handling")

        control_flow_and_error_handling_patterns = self._gather_from_list(control_flow_and_error_handling, "patterns")
        control_flow_and_error_handling_patterns = self._remove_sentence_data(control_flow_and_error_handling_patterns, tolerance=5)    #Tolerance assumed from data, larger sections more helpful here than other data values
        control_flow_and_error_handling_patterns = self._gather_unique(control_flow_and_error_handling_patterns)
        control_flow_and_error_handling_patterns = self._remove_similar_data(control_flow_and_error_handling_patterns)  #2 word similarity should work best, though may be unstable with larger strings if larger strings found first

        #error handling quality to be added later, requires averaging string ratings for overall output since list of ratings isn't helpful unless associated with files which isn't supported yet and some outputs aren't simple one word responses

        #Gather dictionaries for contained keys
        library_and_framework_usage = self._gather_from_dict(analysis, "library_and_framework_usage")

        libraries_detected = self._gather_from_list(library_and_framework_usage, "libraries_detected")
        libraries_detected = self._remove_sentence_data(libraries_detected) #No spaces should be found in libraries
        libraries_detected = self._gather_unique(libraries_detected)

        #Not adding any of these yet since data would require file association or averaging of strings. Useful data however.
        #code_quality_and_maintainability
        #readability
        #testability
        #technical debt

        #inferred_strengths
        inferred_strengths = self._gather_from_dict(analysis, "inferred_strengths")
        inferred_strengths = self._remove_sentence_data(inferred_strengths, tolerance=4)    #Strings longer than 5 words stop being meaningful strenghts and start being observations of uses
        inferred_strengths = self._gather_unique(inferred_strengths)

        #Growth areas discluded for now considering it is mostly sentence data but theoretically useful data for future releases

        new_dict = {
            "design_concepts": design_concepts,
            "structures_used": data_structures,
            "time_complexities_recorded": time_complexities_recorded,
            "space_complexities_recorded": space_complexities_recorded,
            "control_flow_and_error_handling_patterns": control_flow_and_error_handling_patterns,
            "libraries_detected": libraries_detected,
            "inferred_strengths": inferred_strengths
        }
        self.new_dict = new_dict

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
            if not (isinstance(string, str)):  #If value isn't a string, it shouldn't be in the list
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
            if not (isinstance(string, str)):  #If value isn't a string, it shouldn't be in the list
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
            if not (isinstance(item, str)):    #If value isn't a string, it shouldn't be in the list
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
            if not (isinstance(string, str)):  #If value isn't a string, it shouldn't be in the list
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
                    if self._compare_word_sets(item[1], similar_item[1], similarity_word_num):
                        similarity+=1
                if similarity == len(item_set): #if new item is similar to all of list of similar items, adds it to that list of similar items
                    item_set.append(item)
                    similarity_found = True
                    break
            if similarity_found == False:   #makes new list of similar items if new item doesn't fit into any other list of similar items
                similar_sets.append([item])
        final_set = list()
        for similar_set in similar_sets:    #Pulls shortest item of each list of similar items
            similar_words = list()
            for item in similar_set:
                similar_words.append(item[0])
            final_set.append(min(similar_words, key=len))
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
                if (word1 in word2) or (word2 in word1):
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
                if isinstance(value[key], list):    #If value of value[key] is a list, we add all elements of list to value_list instead of a list as one element
                    value_list.extend(value[key])
                else:
                    value_list.append(value[key])
        return value_list
    
    def _gather_from_list(self, dict_list: list, key: str) -> list:
        '''
        Iterates over every gathered dictionary in list when wanted key is nested in a second dictionary of AI analysis.

        paramters:
            dict_list: list of dictionaries from _gather_from_dict when wanted key is nested in a second dictionary in every analysis
            key: dictionary index/key to gather data into list from

        return:
            list of all data from key value. Not unique.
        '''
        value_list = list()
        for dictionary in dict_list:
            if key in dictionary:
                if isinstance(dictionary[key], list):    #If value of dictionary[key] is a list, we add all elements of list to value_list instead of a list as one element
                    value_list.extend(dictionary[key])
                else:
                    value_list.append(dictionary[key])
        return value_list

    def get_scrubbed_dict(self) -> dict:
        '''
        Returns gathered and scrubbed data

        Refer to class for current output dictionary format
        '''
        return self.new_dict