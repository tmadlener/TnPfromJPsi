import ROOT as r
from utils.recurseTFile import recurseOnFile
from utils.miscHelpers import *
import re
import json
import argparse

# Keep ROOT from polluting stdout with its info messages
r.gROOT.ProcessLine("gErrorIgnoreLevel = 1001")

def renameFit(plotName):
    """
    rename the fit to a name that is more convenient to the eye than the auto-generated name of the TnP-Fitter
    """
    # NOTE: the used trigger regex is hardcoded into here, maybe this can (and has to) be changed at one point
    trigRgx = re.compile('(_tag)?_Mu7p5_Track2_Jpsi(_(TK|MU)_pass_)?') # matches the whole trigger name
    fn = trigRgx.sub('', plotName)
    fn = fn.replace('_pair_drM1_bin0_', '').replace('_pair_probeMultiplicity_bin0_', '')
    # remove the ID subfolder from the name, since that is already set in the output-directory
    return ''.join(fn.split('/')[1:]);


class SaveCanvasIfMatch(object):
    """
    Functor that saves a TCanvas if its name matches the internal regex.
    The resulting filename is the path of the TCanvas _inside_ the rootfile. (The appropriate folder structure will
    be created by the function).

    Reasons for this to be a functor:
    1) Interface requirements: the recurseOnFile expects a fucntion with a TObject as single argument
    2) In this way the value of the current path _inside_ the file can easily be stored and changed
    """

    def __init__(self, regex, extension = 'pdf', path = './'):
        """
        Initialize: store (and compile) the regex and the file extension and set the current path to empty string
        """
        self.regex = re.compile(regex)
        self.ext = extension
        self.basePath = path
        self.currentPath = ''


    def __call__(self, obj):
        """
        Provide the required interface.
        Checks if the passed TObject inherits from a TCanvas and if its name matches the regex.
        If this is the case the output file is created and stored in the appropriate folder, which is created if
        necessary
        """
        if obj.InheritsFrom('TCanvas'):
            if self.regex.match(obj.GetName()):
                # The TDirectory::GetPath() method returns in the format /file/on/disk:/path/in/file
                path = self.currentPath.split(':')[1]
                path = '/'.join((path.split('/')[2:])) # remove the /tpTree/ directory from the path
                filename = ''.join([self.basePath, '/', renameFit(path), '_', obj.GetName(), '.', self.ext])
                condMkDirFile(filename)
                obj.SaveAs(filename)


    def setPath(self, directory):
        """
        Set the internal path variable to the path of the passed TDirectory
        """
        self.currentPath = directory.GetPath()


def getOutputDir(filename, defaultdir):
    """
    if we are in the pt_abseta scenario, the fitting has to be done in different abseta bins.
    This is not reflected in the directory names inside the .root files produced by the TagProbeFitTreeAnalyzer
    In order to have a separate folder for each of the pt_abseta input files, information from the filename is used
    """
    # strip off everything besides the scenario and the ID
    outdir = filename.replace("TnP_MuonID_","").replace("_data_all__", "").replace("_signal_mc__","").replace(".root", "")
    return '/'.join([defaultdir, outdir])

"""
Setup arg parser
"""
parser = argparse.ArgumentParser(description='This script saves all TCanvas that are stored in a root file')
parser.add_argument('jsonFile', help='Path to the json file containing all configuration')
parser.add_argument('-nr', '--name_regex', help='The regex that the name of a TCanvas has to match in order to be saved. Will override the one given in the input json file!')
parser.add_argument('-f', '--file_extensions',
                    help='The file format for the output plots will override the one in the input json file!',
                    nargs='*')
parser.add_argument('-o', '--output_dir',
                    help='The base directory under which all plots will be saved')
parser.add_argument('-v', '--verbosity', default=1, help='In- or Decrease the amount of output to stdout (0 disables it completely, 1 prints some basic information)')

[args, leftovers] = parser.parse_known_args()

"""
Read JSON file
"""
with open(args.jsonFile, 'r') as f:
    json = json.loads(f.read())


# Check if the json arguments have been overriden by the command line
if args.file_extensions is not None:
    extensions = args.file_extensions
else:
    extensions = json["file_extensions"]

if args.name_regex is not None:
    nameRgx = args.name_regex
else:
    nameRgx = json["name_regex"]

if args.output_dir is not None:
    outdir = args.output_dir
else:
    outdir = json["output_dir"]

if args.verbosity > 0:
    print('Saving extensions: {}'.format(', ').join(extensions))
    print('Used regex to match canvas names: {}'.format(nameRgx))
    print('Saving to directory: {}'.format(outdir))


for ext in extensions:
    for fn in json["input_files"]:
        canSaver = SaveCanvasIfMatch(nameRgx, ext, getOutputDir(fn, outdir))
        filename = json["input_path"] + fn
        if args.verbosity > 0:
            print('Now processing {}'.format(filename))

        f = r.TFile.Open(filename)
        if f != None:
            recurseOnFile(f, canSaver, lambda o: canSaver.setPath(o))
        # else:
        #     print('Could not open file: {}. Not processing it'.format(filename)) # already printed by ROOT
