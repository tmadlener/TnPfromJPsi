import os

def condMkDir(path):
    """
    check if the folder with the given path exists and if not create it
    Taken from: http://stackoverflow.com/a/14364249/3604607
    """
    try:
        os.makedirs(path)
    except OSError:
        if not os.path.isdir(path):
            raise


def condMkDirFile(filename):
    """
    Check if the folder exists to store the passed file.
    The filename (i.e. everything after the last "/") is removed and then the directory is conditionally made
    """
    [path, name] = os.path.split(filename)
    condMkDir(path)
