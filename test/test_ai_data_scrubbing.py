import unittest
from pathlib import Path
from src.ai_data_scrubbing import ai_data_scrubber
import pytest

class TestAIDataScrubbing(unittest.TestCase):
    '''
    Tests contents of ai_data_scrubbing, ensuring outputs are correct formats.
    '''

    #Test dictionary based off ai analysis of this project's source files, only a handful of files used and only some of the data to keep the dict smaller
    test_dict = {'test_dict_file1': {
        'design_and_architecture': {'concepts_observed': []},
        'data_structures_and_algorithms': {'structures_used': ['List', 'Dict', 'Set'], 'time_complexity': {'best_case': 'O(n)', 'average_case': 'O(n log n)', 'worst_case': 'O(n^2)'}, 'space_complexity': 'O(1)'},
        'control_flow_and_error_handling': {'patterns': ['If-Else', 'For-Loop', 'While-Loop'], 'error_handling_quality': 'High'},
        'library_and_framework_usage': {'libraries_detected': ['numpy', 'pandas', 'matplotlib', 'scikit-learn', 'pytest', 'unittest', 'jest', 'cypress', 'Docker', 'Docker Compose', 'Terraform']},
        'inferred_strengths': ['Data Analysis', 'Machine Learning', 'Testing', 'DevOps']
    }, 'test_dict_file2': { #this error was found in an output but still contained a few empty keys, used to test error handling
        'error': 'The provided code snippet is incomplete and lacks the necessary context to fully understand its purpose. It appears to be a class definition for a `codeAnalysisAI` class, but it does not contain any methods or functions that would allow it to perform analysis on source files.',
        'inferred_strengths': []
    }, 'test_dict_file3': {
        'design_and_architecture': {'concepts_observed': ['User Consent Management', 'Data Processing', 'External Services']},
        'data_structures_and_algorithms': {'structures_used': ['List', 'Dictionary', 'Tuple', 'Set'], 'time_complexity': {'best_case': 'O(1)', 'average_case': 'O(n)', 'worst_case': 'O(n)'}, 'space_complexity': 'O(n)'},
        'control_flow_and_error_handling': {'patterns': ['If-Else Statements', 'While Loops', 'Recursion'], 'error_handling_quality': 'The code handles errors gracefully by providing appropriate messages and retrying in case of invalid inputs. It also includes a mechanism to revoke consent if necessary.'},
        'library_and_framework_usage': {'libraries_detected': ['os', 'sys', 'src.Configuration', 'src.user_startup_config']},
        'inferred_strengths': ['Modular Design', 'Error Handling', 'Code Reusability']
    }, 'test_dict_file4': {
        'design_and_architecture': {'concepts_observed': ['File handling', 'Path manipulation', 'List operations', 'Dictionary usage', 'Function definition and invocation', 'Loop control', 'Conditional statements', 'Error handling', 'Module import', 'Class definition', 'Inheritance', 'Polymorphism', 'Data structures (e.g., lists, dictionaries)', 'Recursion', 'File system operations', 'String manipulation', 'Regular expressions', 'Logging', 'System calls', 'Concurrency and parallelism']},
        'data_structures_and_algorithms': {'structures_used': ['List', 'Dictionary', 'Set', 'Tuple', 'String', 'File path', 'Path object', 'Module import', 'Class definition', 'Inheritance', 'Polymorphism'], 'algorithmic_insights': '', 'time_complexity': {'best_case': 'O(n log n)', 'average_case': 'O(n log n)', 'worst_case': 'O(n^2)'}, 'space_complexity': 'O(n)'},
        'control_flow_and_error_handling': {'patterns': ['If-else statements', 'For loops', 'While loops', 'Conditional expressions', 'Error handling with try-except blocks', 'File operations with try-catch block'], 'error_handling_quality': ''},
        'library_and_framework_usage': {'libraries_detected': ['pathlib', 'typing', 'tempfile', 'shutil', 'logging', 'sys', 'os', 'contribution_skill_insights', 'individual_contribution_detection'], 'experience_inference': ''},
        'inferred_strengths': ['File handling and path manipulation', 'List operations and dictionary usage', 'Function definition and invocation', 'Loop control and conditional statements', 'Error handling with try-except blocks', 'Module import and class definition', 'Inheritance and polymorphism', 'Data structures (e.g., lists, dictionaries)', 'Recursion', 'File system operations', 'String manipulation and regular expressions', 'Logging', 'System calls', 'Concurrency and parallelism']
    }}

    design_concepts_expectation = ['user consent management', 'data processing', 'external services', 'file handling', 'path manipulation', 'list operations', 'dictionary usage', 'function definition and invocation', 'loop control', 'conditional statements', 'error handling', 'module import', 'class definition', 'inheritance', 'polymorphism', 'recursion', 'file system operations', 'string manipulation', 'regular expressions', 'logging', 'system calls', 'concurrency and parallelism']
    structures_used_expectation = ['list', 'dict', 'set', 'tuple', 'string', 'file path', 'module import', 'class definition', 'inheritance', 'polymorphism']
    time_complexity_expectations = ['O(n log n)', 'O(n)']
    space_complexity_expectations = ['O(1)', 'O(n)']
    patterns_expectations = ['if-else', 'for-loop', 'while-loop', 'recursion', 'conditional expressions', 'file operations with try-catch block']
    libraries_expectation = ['numpy', 'pandas', 'matplotlib', 'scikit-learn', 'pytest', 'unittest', 'jest', 'cypress', 'docker', 'terraform', 'os', 'sys', 'src.configuration', 'src.user_startup_config', 'pathlib', 'typing', 'tempfile', 'shutil', 'logging', 'contribution_skill_insights', 'individual_contribution_detection']
    strengths_expectation = ['data analysis', 'machine learning', 'testing', 'devops', 'modular design', 'error handling', 'code reusability', 'file handling and path manipulation', 'list operations and dictionary usage', 'function definition and invocation', 'loop control and conditional statements', 'error handling with try-except blocks', 'module import and class definition', 'inheritance and polymorphism', 'data structures (e.g., lists, dictionaries)', 'recursion', 'file system operations', 'string manipulation and regular expressions', 'logging', 'system calls', 'concurrency and parallelism']

    def setUp(self):
        '''
        Sets up scrubbed data for testing against
        '''
        self.ai_scrubber = ai_data_scrubber(self.test_dict)
        self.ai_scrubbed = self.ai_scrubber.get_scrubbed_dict()

    def test_output_format(self):
        '''
        Ensures that output is a dictionary of lists
        '''
        for key, value in self.ai_scrubbed.items():
            print(key)
            self.assertIsInstance(value, list)

    def test_correctness_of_scrub(self):
        '''
        Ensures that scrubbed data is correct from test_dict to output
        '''
        print(self.ai_scrubbed["design_concepts"])
        self.assertCountEqual(self.ai_scrubbed["design_concepts"], self.design_concepts_expectation)
        print(self.ai_scrubbed["structures_used"])
        self.assertCountEqual(self.ai_scrubbed["structures_used"], self.structures_used_expectation)
        print(self.ai_scrubbed["time_complexities_recorded"])
        self.assertCountEqual(self.ai_scrubbed["time_complexities_recorded"], self.time_complexity_expectations)
        print(self.ai_scrubbed["space_complexities_recorded"])
        self.assertCountEqual(self.ai_scrubbed["space_complexities_recorded"], self.space_complexity_expectations)
        print(self.ai_scrubbed["control_flow_and_error_handling_patterns"])
        self.assertCountEqual(self.ai_scrubbed["control_flow_and_error_handling_patterns"], self.patterns_expectations)
        print(self.ai_scrubbed["libraries_detected"])
        self.assertCountEqual(self.ai_scrubbed["libraries_detected"], self.libraries_expectation)
        print(self.ai_scrubbed["inferred_strengths"])
        self.assertCountEqual(self.ai_scrubbed["inferred_strengths"], self.strengths_expectation)