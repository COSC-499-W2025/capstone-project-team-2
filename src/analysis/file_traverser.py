from pathlib import Path

from src.core.data_extraction import FileMetadataExtractor

class ProjectTraversalModule:

    #Guide on how to merge your rebuilt system into this system
    #1. Import your class or methods and global variable
    #2. Initialize your class under __init__() to ensure data in your analyzer will persist between files
    #   or, reset a global variable storing your data directly or via a method if class not used
    #3. Build a constant list of suffixes under this class' attributes for use in sorting files into your analyzer
    #4. Under _sort_into_analyzers(), build an if statement to conditionally sort files you want
    #5. Under that if statement in _sort_into_analyzers(), place your method that takes a single file for analysis and pass "file" into it (file is a Path object)
    #6. Under build_analysis_with_project(), place the method that takes your aggregated results of the analzyer and place it in building_dict
    #If your system analyzes all file types, ignore steps 4 and 5 and don't place your method under an if statement in step 6
    #WARNING!!! Not adapting your system to analyze files individually, unless explained in detail how it would affect analysis results negatively,
    # will not be tolerated

    #Build list of suffixes that apply to your analyzer for use in sorting here
    #vvvvvv

    #Example suffix list for sorting condition
    PYTHON_SUFFIXES = list(".py")

    #^^^^^^

    def __init__(self, root: Path):
        """
        Class initialization for traversing files of project.
        Sets the root directory as well as builds the classes for aggregating the file analysis for each system.

        Args:
            root (Path): directory root of the project to traverse

        Returns:
            None
        """
        if (not root.is_dir()):
            raise Exception("ProjectTraversalModule: File path is not a project directory!")
        self.root_dir = root

        #initialize classes for aggregating analysis of individual files here
        #vvvvvvv

        #^^^^^^^

    def build_analysis_with_project(self) -> dict:
        """
        Method calling the traversal of all files which sorts files into relevant analyzers, then builds a dictionary from aggregated results of each analyzer

        Args:
            None

        Returns:
            dict: aggregated analysis of all files compiled into dictionary
        """
        self._project_traversal()
        building_dict = {}

        #If something cannot be done individualy on each file then aggregated, place into building_dict here
        #WARNING!!! Abuse of this section to not rebuild systems will not be tolerated
        #vvvvvv

        #This could be reasonably replaced with individual file analysis but I believe it would remove valuable hierarchy information by doing so
        #Could also be merged with this code with little effort from what I've seen, but other analyzers rely on some if this data being complete first
        building_dict["hierarchy"] = FileMetadataExtractor(self.root_dir).file_hierarchy()
        #^^^^^^

        #Insert return methods for aggregated analysis into building_dict here
        #vvvvvv

        #^^^^^^

        return building_dict

    def _project_traversal(self):
        """
        Begins traversal of file hierarchy and passes children of directory into recursive helper

        Args:
            None

        Returns:
            None
        """
        try:
            children = list(self.root_dir.iterdir())
        except:
            return
        for c in children:
            self._helper_traversal(c)

    def _helper_traversal(self, current_dir: Path):
        """
        Recursive helper method that passes files to be sorted into analyzers and traverses other directories

        Args:
            current_dir (Path): Path object of the current path node in the project directory

        Returns:
            None
        """
        if (current_dir.is_file()):
            self._sort_into_analyzers(current_dir)
        else:
            try:
                children = list(current_dir.iterdir())
            except:
                return
            for c in children:
                self._helper_traversal(c)

    def _sort_into_analyzers(self, file: Path):
        """
        Method that takes in a file and sorts it into the relevant analyzers

        Args:
            file (Path): path to a file to be sorted into analyzers

        Returns:
            None
        """

        suffix = file.suffix

        #Place conditional statement alongside call for your analyzer for individual files here
        #vvvvvv

        if suffix in self.PYTHON_SUFFIXES:
            #send to python analyzers
            pass

        #^^^^^^