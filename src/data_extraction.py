import os
import unittest
from pathlib import Path

SPACE = '    '
BRANCH = '|   '
TEE = '|-- '
LAST = '`-- '
TARGET_FILE = Path("TEMP FOLDER PATH HERE")



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

    for pointer, path in zip(pointers,content):
        yield prefix + pointer + path.name
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


"""
import os
from treelib import Tree
from pathlib import Path


def list_file_directory(file_path):
    file_to_read_from=file_path
    tree = Tree()
    files_List=[]
    folders_list=[]

    tree.create_node(tag=file_to_read_from, identifier=str(file_to_read_from))


    for root,dirs,files in os.walk(file_to_read_from,topdown=True):
        for name in files:
            file_path=os.path.join(root,name)
            files_List.append(Path(os.path.join(root,name)))
        for name in dirs:
            directory_path=os.path.join(root,name)
            folders_list.append(Path(directory_path))



    for folder in folders_list:
        folder_parent=folder.parent
        tree.create_node(tag=folder.name,parent=str(folder_parent),identifier=str(folder))

    for file in files_List:
        file_parent=file.parent
        tree.create_node(tag=file.name,parent=str(file_parent),identifier=str(file))


    tree.show()
    """