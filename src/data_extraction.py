import os
import unittest
import datetime
import platform
import getpass
import json


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
        """
        Initialize the FileMetadataExtractor.

        Args:
            dir_path (str | Path): The directory path to scan for file hierarchy and metadata.
        """
        self.dir_path = Path(dir_path)
        
## creating a helper function in preparation of cross platform file checking
    def get_author(self, path: Path):
        try:
            #checks for a windows system and an installation of winsecurity
            if platform.system() == "Windows" and win32security:
                try:
                    # pulls the windows security descriptor from the file
                    SecDesc = win32security.GetFileSecurity(str(path), win32security.OWNER_SECURITY_INFORMATION)
                    owner_sid = SecDesc.GetSecurityDescriptorOwner()
                    #only pulls the name of the file author
                    name, _, _ = win32security.LookupAccountSid(None, owner_sid)
                    return name
                except Exception:
                 return getpass.getuser()
        
            # this returns the current logged in user for the system if not window
            return getpass.getuser()
        except Exception:
            return "Unknown"



    def file_hierarchy(self, dir_path: Path | None = None):

        """
        Helps identify, whether or not files or directories exist
        
        """

        if not self.dir_path.exists():
            print("Error: Filepath not found")
            return {"name": self.dir_path.name, "type": "DIR", "children": [{"name": "Not Found", "type": "DIR", "children": []}]}
        if not self.dir_path.is_dir():
            print("Error: File is not a directory")
            return {"name": self.dir_path.name, "type": "DIR", "children": [{"name": "Not a Directory", "type": "DIR", "children": []}]}

        return self.tree(self.dir_path)


    def tree(self, dir_path: Path):
        """
        systematically runs through the directory pulls the statistics off each file, pulling metadata pertaining to 
        creation date, modified date, author, file size and file type

        Args:
            dir_path (Path): The directory to traverse.
            prefix (str): The prefix used to format tree levels visually.

        Returns:
            dict: A dictionary representing the directory and its children with metadata.
        
        """
        node = {"name": dir_path.name, "type": "DIR", "children": []}

        if not dir_path.exists():
            node["children"].append({"name": "Not Found", "type": "DIR", "children": []})
            return node
        if not dir_path.is_dir():
            node["children"].append({"name": "Not a Directory", "type": "DIR", "children": []})
            return node
        

        try:
            content = list(dir_path.iterdir())
        except PermissionError:
            node["children"].append({"name": "No Access", "type": "DIR", "children": []})
            return node
        except Exception:
            node["children"].append({"name": "Error accessing folder", "type": "DIR", "children": []})
            return node

        if not content:
            node["children"].append({"name": "Empty", "type": "DIR", "children": []})
            return node


        for path in content:
            try:
                stat = path.stat()
                created = datetime.datetime.fromtimestamp(stat.st_birthtime).strftime('%Y-%m-%d %H:%M:%S')
                modified = datetime.datetime.fromtimestamp(stat.st_mtime).strftime('%Y-%m-%d %H:%M:%S')
                size = stat.st_size
                author = self.get_author(path)
            except Exception:
                created = modified = "N/A"
                size = 0
                author = "Unknown"

            if path.is_dir():
                node["children"].append(self.tree(path))

            else:
                node["children"].append({
                    "name": path.name,
                    "type": path.suffix.lstrip('.') or "FILE",
                    "size": size,
                    "created": created,
                    "modified": modified,
                    "author": author,
                    "children": []
                })

        return node

    def print_tree(self, node, prefix = " "):
        """
        Run through the tree nodes and reformats them in to a readable formatt
        """
        if node is None:
            return
        
        if node["type"] == "DIR":
            print(prefix + node["name"] + " [DIR]")
        else:
            print(prefix + node["name"] + f" [{node['type']}] size: {node['size']}B, created: {node['created']}, modified: {node['modified']}, author: {node['author']}")

        
        for i, child in enumerate(node["children"]):
            # Determine pointer style
            pointer = TEE if i < len(node["children"]) - 1 else LAST
            cprefix = prefix + pointer
            # Use BRANCH spacing for nested items
            nprefix = prefix + (BRANCH if pointer == TEE else SPACE)
            self.print_tree(child, nprefix)

    def print_hierarchy(self, File_Path):

        """
        Prints the directory tree and metadata for the given path.

        Args:
            file_path (Path): The root path to print.
        """
        #outputs code in the same readable format as before
        tree_data = self.tree(self.dir_path)
        if tree_data:
            self.print_tree(tree_data)
