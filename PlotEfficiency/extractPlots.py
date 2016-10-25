import ROOT as r
import json
import argparse
from utils.TGA_utils import *

def getGraphFromFile(infile, ID, scenario, canvasName, graphName="hxy_fit_eff"):
    """
    Get the efficiency TGraphAsymmErrors from the passed infile (i.e. TFileDirectory) by trying to find the
    subdirectory 'fit_eff_plots' in any subdirectory matching 'ID_scenario'.
    NOTE: Only checks top-level directories
    """
    dirMatchName = "_".join([ID, scenario])
    # print(dirMatchName)

    keys = infile.GetListOfKeys()
    nKeys = keys.GetEntries()
    keyIter = keys.MakeIterator()

    graph = None
    for i in range(0, nKeys):
        key = keyIter.Next()
        dirName = key.GetName()

        if dirMatchName in dirName:
            canvasDir = infile.Get(dirName).Get("fit_eff_plots")
            # print(canvasName)
            canvas = canvasDir.Get(canvasName)
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

    return "_".join([prep, "PLOT", trigger, "TK", "pass", "&", "tag", trigger, "MU", "pass"])



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
            dataFile = r.TFile.Open(inp["data_file"])
            dataDir = dataFile.GetDirectory(inp["basedir"])
            mcFile = r.TFile.Open(inp["mc_file"])
            mcDir = mcFile.GetDirectory(inp["basedir"])

            ID = inp["ID"]
            scenario = inp["scenario"]
            canvasName = getCanvasName(scenario, inp["trigger"]).encode('ascii')
            dataGraph = getGraphFromFile(dataDir, ID, scenario, canvasName, "hxy_fit_eff")
            cleanUpGraph(dataGraph)
            mcGraph = getGraphFromFile(mcDir, ID, scenario, canvasName, "hxy_fit_eff")

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
