def recurseOnFile(f, func, dirFunc = None):
    """
    Generic root file recursion function that traverses all TDirectories that can be found in a TFile.
    For every key that is found in the file it is checked if it inherits from TDirectory and if not the
    function passed in via the func paramter is executed.

    * f is the TFile or TDirectory to recurse on.
    * func is any function that takes a TObject as its single argument.
    * dirFunc is any function taking a TDirectory as its single argument that is executed on each directory but
      should be outside of the recursion (e.g. obtaining the current path)
    """
    for key in f.GetListOfKeys():
        obj = key.ReadObj()
        if not obj.InheritsFrom('TDirectory'):
            func(obj)
        else:
            dirFunc(obj)
            recurseOnFile(obj, func, dirFunc)
