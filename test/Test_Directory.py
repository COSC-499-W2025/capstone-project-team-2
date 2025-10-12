import os
from pathlib import Path

space = '    '
branch = '|   '
tee = '|-- '
last = '`-- '
Target_File = Path("TEMP FOLDER PATH HERE")



def File_Heirarchy(File_Path):

    if not os.path.exists(File_Path):
        print(f"Error: Filepath not found")
        return
    
    if not os.path.isdir(File_Path):
        print(f"Error: File is not a Zip file")
        return

    Print_Heirarchy(File_Path)


def tree(dir_path: Path, prefix: str= ' '):

    try:
        content = list(dir_path.iterdir())
    except PermissionError:
        yield prefix + "No Access"
        return
    if not content:
        yield prefix + "Empty"
        return
    
    pointers = [tee] * (len(content) - 1) + [last]

    for pointer, path in zip(pointers,content):
        yield prefix + pointer + path.name
        if path.is_dir():
            extension = branch if pointer == tee else space
            yield from tree(path, prefix= prefix + extension)



def Print_Heirarchy(File_Path):
    print(File_Path.resolve())
    for Ftree in tree(File_Path):
        print(Ftree)

def main():
    File_Heirarchy(Target_File)

main()