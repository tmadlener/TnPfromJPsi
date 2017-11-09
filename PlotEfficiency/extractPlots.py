import ROOT as r
import json
import argparse
import re
import sys
from utils.TGA_utils import *

def getCanvas(infile, dir_name, scenario, trigger):
    """
    Get the canvas on which the graph is stored
    """
    canv_dir = infile.Get(dir_name).Get('fit_eff_plots')
    # first try if we can get it in a simple way
    canv_name = getCanvasName(scenario, trigger).encode('ascii') # ascii encoding due to '&'
    canvas = canv_dir.Get(canv_name)
    if canvas:
        return canvas

    # if this fails, we ask for an input
    print('Could not get the desired canvas from the file for scenario: {}'.format(scenario))
    print('Requested name was {}'.format(canv_name))
    key_names = [k.GetName() for k in canv_dir.GetListOfKeys()]
    for (i, k) in enumerate(key_names):
        print('[{}]: {}'.format(i, k))

    while True:
        inp = raw_input('Choose one of the following or \'q\' to quit: ')
        if inp.upper() == 'Q':
            sys.exit(1)
        else:
            try:
                dec = int(inp)
                if dec >= len(key_names): raise ValueError
                break
            except ValueError:
                print('Enter number between 0 and {} or \'q\' to quit'.format(len(key_names) - 1))

    canvas = canv_dir.Get(key_names[dec])
    return canvas



def getGraphFromFile(infile, ID, scenario, trigger, graphName="hxy_fit_eff"):
    """
    Get the efficiency TGraphAsymmErrors from the passed infile (i.e. TFileDirectory) by trying to find the
    subdirectory 'fit_eff_plots' in any subdirectory matching 'ID_scenario'.
    NOTE: Only checks top-level directories
    """
    dirMatchName = "_".join([ID, scenario])
    # print(dirMatchName)

    keys = [k.GetName() for k in infile.GetListOfKeys()]
    graph = None
    for dirName in keys:
        if dirMatchName in dirName:
            canvas = getCanvas(infile, dirName, scenario, trigger)
            graph = canvas.GetPrimitive(graphName)

    return graph


def cleanUpGraph(graph):
    """
    Do some clean-up to the graph.
    *) If the efficiency plus the high error are above one, correct the high_error to reach to exactly one.
    """
    for i in range(0, graph.GetN()):
        p = getPoint(graph, i)
        if p.y + p.eh_y > 1:
            graph.SetPointError(i, p.el_x, p.eh_x, p.el_y, 1 - p.eh_y)


def getCanvasName(scenario, trigger, b="0"):
    """
    Build the name of the Canvas on which the graphs are stored
    """
    prep = ""
    if "vtx" in scenario:
        prep = "tag_nVertices"
    else:
        prep = scenario

    # for the pt_abseta scenario some more care has to be taken, since there are
    # two binnings (pt, and abseta) in play and we are mainly interested in the pt dependency
    if "pt_abseta_" in scenario:
        bin_rgx = r'pt_abseta_([0-9])'
        prep = re.sub(bin_rgx, r'pt_PLOT_abseta_bin\1', scenario)
    else:
        prep = '_'.join([prep, 'PLOT'])

    return "_".join([prep, trigger, "TK", "pass", "&", "tag", trigger, "MU", "pass"])


def processJsonFile(filename):
    """
    Process one json input file
    """
    print('Now processing JSON file: {}'.format(filename))

    with open(filename, 'r') as f:
        jsonInput = json.loads(f.read())

        """
        process all inputs in the jsonInput file
        """
        for inp in jsonInput["inputs"]:
            # print(inp)
            print('Now processing:\ndata file: {}\n'
                  'mc file: {}'.format(inp['data_file'], inp['mc_file']))
            dataFile = r.TFile.Open(inp["data_file"])
            dataDir = dataFile.GetDirectory(inp["basedir"])
            mcFile = r.TFile.Open(inp["mc_file"])
            mcDir = mcFile.GetDirectory(inp["basedir"])

            ID = inp["ID"]
            scenario = inp["scenario"]
            dataGraph = getGraphFromFile(dataDir, ID, scenario, inp['trigger'], "hxy_fit_eff")
            mcGraph = getGraphFromFile(mcDir, ID, scenario, inp['trigger'], "hxy_fit_eff")

            cleanUpGraph(dataGraph)
            cleanUpGraph(mcGraph)

            ratioGraph = divideGraphs(dataGraph, mcGraph)

            outfilename = "".join([inp["output_path"], "MuonID_", inp["ID"], "_", inp["scenario"], inp["outfile_add"], ".root"])
            outfile = r.TFile.Open(outfilename, "recreate")
            outfile.cd()
            dataGraph.SetName("DATA")
            dataGraph.Write()
            mcGraph.SetName("MC")
            mcGraph.Write()
            ratioGraph.SetName("RATIO")
            ratioGraph.Write()

            outfile.Write()
            outfile.Close()



"""
Arg parsing and json read-in
"""
parser = argparse.ArgumentParser(description="This script takes a JSON file as input and extracts plots from TnP r files. It produces an output ROOT file containing a DATA an MC as well as a RATIO TGraphAsymmErrors that can be read and processed by the makePklFile.py script as well as the plotting scripts")
parser.add_argument("jsonFiles", nargs='*', help="Path(s) to the JSON file(s)")
args = parser.parse_args()



"""
Process all the json files that have been passed
"""
if len(args.jsonFiles) != 0:
    for jsonFile in args.jsonFiles:
        processJsonFile(jsonFile)
else:
    print('Need at least on json file to process')
