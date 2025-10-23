import os
import unittest
import datetime
import platform
import getpass


from pathlib import Path

# will only import on windows
try:
    if platform.system() == "Windows":
        import win32security
    else:
        win32security = None
except ImportError:
        win32security = None

SPACE = '    '
BRANCH = '|   '
TEE = '|-- '
LAST = '`-- '

class FileMetadataExtractor:


    """
    This is a helper class that takes in a file mapping the directory and collect file metadata
    pertaining to size, creation/modification time, and author (file owner on Windows).

    Attributes:
        dir_path (Path): The root directory path to extract metadata from.
    """
    def __init__(self, dir_path: str | Path):
        self.dir_path = Path(dir_path)
        
## creating a helper function in preparation of cross platform file checking
    def get_author(self, path: Path):
        try:
            if platform.system() == "Windows":
                return getpass.getuser()
            else:
                return "Author Unknown"
        except Exception:
            return "Unknown"



    def file_hierarchy(self):

        if not os.path.exists(self.dir_path):
            print(f"Error: Filepath not found")
            return
    
        if not os.path.isdir(self.dir_path):
            print(f"Error: File is not a directory")
            return

        self.print_hierarchy(self.dir_path)


    def tree(self, dir_path: Path, prefix: str= ' '):

        try:
            content = list(dir_path.iterdir())
        except PermissionError:
            yield prefix + "No Access"
            return
        if not content:
            yield prefix + "Empty"
            return
    
        pointers = [TEE] * (len(content) - 1) + [LAST]

        for pointer, path in zip(pointers, content):
            # Get file stats
            try:
                stat = path.stat()
                created = datetime.datetime.fromtimestamp(stat.st_birthtime).strftime('%Y-%m-%d %H:%M:%S')
                modified = datetime.datetime.fromtimestamp(stat.st_mtime).strftime('%Y-%m-%d %H:%M:%S')
                size = stat.st_size
                author = self.get_author(path)
            except Exception as e:
                created = modified = "N/A"
                size = 0

            # Formating the tree display to include new meta data
            if path.is_file():
                file_type = path.suffix.lstrip('.') or "FILE"
                metadata = f"[{file_type}] size: {size}B, created: {created}, modified: {modified}, author: {author}"
            else:
                metadata = "[DIR]"

            yield prefix + pointer + path.name + ' ' + metadata
        
            if path.is_dir():
                extension = BRANCH if pointer == TEE else SPACE
                yield from self.tree(path, prefix= prefix + extension)


    def print_hierarchy(self, File_Path):
        print(File_Path.resolve())
        for Ftree in self.tree(File_Path):
            print(Ftree)
