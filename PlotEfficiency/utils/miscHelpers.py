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


def getCommonBinning(bins1, bins2):
    """
    Get the binning that is common to both passed binnings
    """
    # NOTE: For the moment it seems that we can get away without dealing with numerical effects here
    # Using this to find the same elements in both lists: http://stackoverflow.com/a/1388842/3604607
    # Turning the set back into a list again sorted from lowest to highest value, which should be our use case
    return sorted(frozenset(bins1).intersection(bins2))


def getOverlappingBins(bins1, bins2):
    """
    Get the indices in both passed binnings of those bins that do overlap.
    """
    coBins = set(getCommonBinning(bins1, bins2))
    iB1 = [i for i, item in enumerate(bins1) if item in coBins]
    iB2 = [i for i, item in enumerate(bins2) if item in coBins]

    return [iB1, iB2]
