import os
import unittest
import datetime
import platform
import getpass


from pathlib import Path

SPACE = '    '
BRANCH = '|   '
TEE = '|-- '
LAST = '`-- '
TARGET_FILE = Path("FILE DIRECTORY HERE")

## creating a helper function in preparation of cross platform file checking
def get_author(path: Path):
    try:
        if platform.system() == "Windows":
            return getpass.getuser()
        else:
            return "Author Unknown"
    except Exception:
         return "Unknown"



def file_heirarchy(File_Path):

    if not os.path.exists(File_Path):
        print(f"Error: Filepath not found")
        return
    
    if not os.path.isdir(File_Path):
        print(f"Error: File is not a directory")
        return

    print_hierarchy(File_Path)


def tree(dir_path: Path, prefix: str= ' '):

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
            author = get_author(path)
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
            yield from tree(path, prefix= prefix + extension)


def print_hierarchy(File_Path):
    print(File_Path.resolve())
    for Ftree in tree(File_Path):
        print(Ftree)

def main():
   print_hierarchy(TARGET_FILE)

main()


