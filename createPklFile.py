#!/usr/bin/env python
import ROOT
import pickle
import json
import argparse

"""
Definitions of helper functions
"""
def getBin(binning, x):
    """
    get the upper and lower border of the bin in which x can be found.
    If x is not in any bin, the range of the binning is returned in reverse order
    """
    for i in range(len(binning)):
        if x > binning[i] and x < binning[i+1]:
            return [binning[i], binning[i+1]]

    return[binning[-1], binning[0]]


class TGAPoint:
    """
    simple struct storing all the information from a point in a TGraphAsymmErrors.
    At the moment only errors in y-direction are stored
    """
    def __init__(self, x, y, eh, el):
        """
        construct from (x,y) coordinates and high and low error on y
        """
        self.x = x
        self.y = y
        self.eh_y = eh
        self.el_y = el

    def __str__(self):
        """
        Print point
        """
        return " x = {:6.4f}, y = {:6.4f} (+{:6.4f} -{:6.4f})".format(self.x, self.y, self.eh_y, self.el_y)


def getPoint(graph, index):
    """
    get the point index from the passed graph
    """
    x = ROOT.Double(0)
    y = ROOT.Double(0)
    graph.GetPoint(index, x, y)
    return TGAPoint(x, y, graph.GetErrorYhigh(index), graph.GetErrorYlow(index))


def checkKeyPresent(d, key):
    """
    Check if the key is present in dictionary d and add empty value if not.
    """
    if not d.has_key(key):
        d[key] = {}


def cleanGraph(graph, binning, valdict, ID, scenario, category):
    """
    Check the passed graphs for any entries with zero efficiency and zero errors. If a point has zero efficiency
    and zero errors, remove it from the graph.

    Function also adds all values to the passed dictionary with the according keys. For removed points all values
    are set to nan.
    """
    nan = float('nan')

    checkKeyPresent(valdict, ID)
    checkKeyPresent(valdict[ID], scenario)

    badPoints = []
    for i in range(graph.GetN()):
        point = getPoint(graph, i)
        # print(point)

        binStr = "_".join(str(b) for b in getBin(binning, point.x.real))
        checkKeyPresent(valdict[ID][scenario], binStr)
        checkKeyPresent(valdict[ID][scenario][binStr], category)

        if point.y != 0 or point.eh_y != 0 or point.el_y != 0:
            valdict[ID][scenario][binStr][category][scenario] = point.x.real
            valdict[ID][scenario][binStr][category]["efficiency"] = point.y.real
            valdict[ID][scenario][binStr][category]["err_low"] = point.el_y
            valdict[ID][scenario][binStr][category]["err_high"] = point.eh_y
        else:
            badPoints.append(i)
            valdict[ID][scenario][binStr][category][scenario] = nan
            valdict[ID][scenario][binStr][category]["efficiency"] = nan
            valdict[ID][scenario][binStr][category]["err_low"] = nan
            valdict[ID][scenario][binStr][category]["err_high"] = nan

    ## remove points in reverse order as the indices of all points after the reomved point are changed
    for i in reversed(badPoints):
        graph.RemovePoint(i)


def setNameTitle(graph, cat, ID, scenario, scenario_add):
    """
    Set Name and Title of graph to '_' separated string of all input arguments
    """
    graph.SetName("_".join([cat, ID, scenario, scenario_add]))
    graph.SetTitle("_".join([cat, ID, scenario, scenario_add]))


def getFile(fn, valdict, outfile, binnings, ID = "Loose", scenario = "eta", scenario_add = ""):
    """
    Process the file with the filename fn
    """

    f = ROOT.TFile.Open(fn)
    print("opened file {}".format(fn))

    graph_data = f.Get("DATA")
    cleanGraph(graph_data, binnings[scenario], valdict, ID, scenario, "data")
    graph_mc = f.Get("MC")
    cleanGraph(graph_mc, binnings[scenario], valdict, ID, scenario, "mc")
    graph_ratio = f.Get("RATIO")
    cleanGraph(graph_ratio, binnings[scenario], valdict, ID, scenario, "data/mc")

    outfile.cd()
    setNameTitle(graph_data, "DATA", ID, scenario, scenario_add)
    setNameTitle(graph_mc, "MC", ID, scenario, scenario_add)
    setNameTitle(graph_ratio, "DATA/MC", ID, scenario, scenario_add)

    graph_data.Write()
    graph_mc.Write()
    graph_ratio.Write()


"""
Setup argument parser
"""
parser = argparse.ArgumentParser(description="This script generates a pkl file from all files specified in the JSON file")
parser.add_argument("jsonFile", help="Path to the JSON file")
args = parser.parse_args()


"""
Read JSON file
"""
with open(args.jsonFile, 'r') as f:
    json = json.loads(f.read())


"""
Create pickle file
"""
valdict = {}
outfile = ROOT.TFile.Open(json["root_output_filename"], "recreate")

path = json["input_files"]["path"]
for fileInfo in json["input_files"]["files"]:
    fn = "".join([path, fileInfo[0]])
    getFile(fn, valdict, outfile, json["binnings"], fileInfo[1], fileInfo[2], fileInfo[3])

with open(json["pickle_filename"], "w") as pklFile:
    pickle.dump(valdict, pklFile)

outfile.Close()
