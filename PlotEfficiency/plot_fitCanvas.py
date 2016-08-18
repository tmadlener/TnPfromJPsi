# script that prints all fit_canvas that can be found in all the passed root files and stores them with
# hopefully reasonable names
#
# TODO: this works quite nicely for the vtx and eta scenario already, however the pt_abseta scenario is
# currently a bit of a mess at the moment.

import os
import subprocess
import glob
import re

def saveCanvasOfFile(_file, _regex="fit_canvas"):
    """
    Saves all the TCanvas found in the file matching the passed regex via a call to the saveCanvas exectuable
    """
    path_to_exe="/afs/hephy.at/work/t/tmadlener/CMSSW_8_0_12/src/TnPfromJPsi/PlotEfficiency/utils/saveCanvas"
    DEVNULL = open(os.devnull, 'w') # needed to dump the output of TCanvas::Save into /dev/null
    print("Saving TCanvas matching \'{}\' from file \'{}\'".format(_regex, _file))
    status = subprocess.call([path_to_exe, _file, _regex], stdout=DEVNULL, stderr=subprocess.STDOUT)
    return status


def commonFileNameCleanup(_filename, _ID, _scenario, _trigRgx):
    """
    Do the cleanup that is common to both mvAndRename functions below:
    Remove trigger stuff and the TDirectory information from the pdf filename
    """
    fn = _trigRgx.sub('', _filename)
    fn = fn.replace(":tpTree:", "").replace("{}_{}:".format(_ID, _scenario), "")
    fn = fn.replace("_pair_drM1_bin0_", "").replace("_pair_probeMultiplicity_bin0_", "")
    return fn


def mvAndRename(_ID, _scenario, _targetdir="fitCanvasPdfs"):
    """
    The output of saveCanvas is not that nice and has to be cleaned up.
    Mainly doing some replacing of the trigger parts and moving the created files to a separate directory
    """
    triggerRegex = re.compile('(_tag)?_Mu7p5_Track2_Jpsi(_(TK|MU)_pass_)?')
    for filename in glob.glob(":tpTree:{}_{}*:*.pdf".format(_ID, _scenario)):
        filenameTo = commonFileNameCleanup(filename, _ID, _scenario, triggerRegex)
        dirTo = "{}/{}_{}".format(_targetdir, _ID, _scenario)
        if not os.path.exists(dirTo):
            os.makedirs(dirTo)
        filenameTo = "/".join([dirTo, filenameTo])
        os.rename(filename, filenameTo)


def mvAndRenamePt(_ID, _scenario, _file, _targetdir="fitCanvasPdfs"):
    """
    The output of saveCanvas is not that nice and has to be cleaned up.
    Mainly doing some replacing of the trigger parts and moving the created files to a separate directory.
    For pt we currently run into a memory problem and have to split the input into abseta different bins.
    However this is not reflected in the names of the produced pdfs (since the .root files do not "know"
    about this splitting, so we have to define a special version for renaming the pt scenario that uses
    some more information that can be obtained from the root file (_file)
    """
    # compute some additional info from the filename (that follows at least for the moment a common pattern)
    addInfo = _file.replace(".root", "")
    addInfo = addInfo.replace("{}_{}_".format(_ID, _scenario), "")
    addInfo = addInfo.replace("TnP_MuonID_","").replace("_data_all_", "").replace("_signal_mc_", "")

    triggerRegex = re.compile('(_tag)?_Mu7p5_Track2_Jpsi(_(TK|MU)_pass_)?')
    for filename in glob.glob(":tpTree:{}_{}*:*.pdf".format(_ID, _scenario)):
        filenameTo = commonFileNameCleanup(filename, _ID, _scenario, triggerRegex)

        dirTo = "{}/{}_{}_{}".format(_targetdir, _ID, _scenario, addInfo)
        if not os.path.exists(dirTo):
            os.makedirs(dirTo)
        filenameTo = "/".join([dirTo, filenameTo])
        os.rename(filename, filenameTo)


def processAllFiles(_dir, _ID, _scenario,
                    _targetdir="fitCanvasPdfs",
                    _canvasRegex="fit_canvas"):
    """
    Process all .root files matching the _ID AND _scenario in _dir.
    """
    os.chdir(_dir)
    for f in glob.glob("TnP_MuonID_*_{0}_{1}*.root".format(_ID, _scenario)):
        saveCanvasOfFile(f, _canvasRegex)
        if "pt_abseta" in _scenario:
            mvAndRenamePt(_ID, _scenario, f, _targetdir)
        else:
            mvAndRename(_ID, _scenario, _targetdir)


# Define on what to run
IDs = ["Loose2016", "Medium2016", "Tight2016", "Soft2016"]
scenarios = ["eta", "vtx", "pt_abseta"]
basedir="/afs/hephy.at/work/t/tmadlener/CMSSW_8_0_12/src/mc_rootfiles"
targetdir="/afs/hephy.at/work/t/tmadlener/CMSSW_8_0_12/src/outputfiles/Figures/FitCanvasPdfs/mc"

for ID in IDs:
    for scen in scenarios:
        print("Currently processing ID: {}, scenario: {}".format(ID, scen))
        processAllFiles(basedir, ID, scen, targetdir, "fit_canvas")
