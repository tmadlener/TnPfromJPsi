import argparse
import json
from copy import deepcopy
from random import choice
from string import ascii_uppercase
from utils.structFromDict import *

"""
Arg parsing
"""
parser = argparse.ArgumentParser(description="This script can be used to produce plots from the root files produced with the extractPlots.py script")
parser.add_argument("jsonFile", help="path to the json file containing the settings")
args = parser.parse_args()

# import ROOT after doing the argparsing, to not mess it up
import ROOT as r

def createFrame(pad, xlow, xhigh, ylow, yhigh, yOffset):
    """
    Create a TH1F as frame to draw TGraphAsymmErrors into on the passed pad.
    NOTE: Only the 'default' settings are set here
    """
    frame = pad.DrawFrame(xlow, ylow, xhigh, yhigh)
    frame.GetYaxis().SetTitleOffset(yOffset)
    frame.GetXaxis().SetLabelSize(0)
    frame.GetXaxis().SetLabelFont(63)
    frame.GetXaxis().SetLabelSize(16)
    frame.GetYaxis().SetLabelFont(63)
    frame.GetYaxis().SetLabelSize(16)
    frame.GetYaxis().SetTitleFont(69)
    frame.GetYaxis().SetTitleSize(16)
    # frame.GetYaxis().SetNdivisions(510) # set this explicitly later
    frame.GetYaxis().SetDecimals()

    return frame


def drawGrid(pad, binning, ylow, yhigh):
    """
    Draw the grid according to the binning in x
    """
    line = r.TLine()
    line.SetLineStyle(3)
    for x in binning:
        line.DrawLine(x, ylow, x, yhigh)

    pad.SetGridy()


def createPad(name, low, high):
    """
    Create a TPad with the 'default' settings
    """
    pad = r.TPad(name, name, 0, low, 1, high)
    pad.SetBottomMargin(0.05)
    pad.SetTickx()
    pad.SetTicky()
    pad.Draw()
    pad.cd()

    return pad


def drawRatioPad(canvas, plotSettings, ratioGraph, binning, axislabel):
    """
    Draw the lower part of the whole figure, containing the ratio graph onto the passed canvas
    """
    canvas.cd()
    pad = createPad("pad2", 0, 0.3)
    pad.SetBottomMargin(0.28)

    frame = createFrame(pad, plotSettings.xlow, plotSettings.xhigh, plotSettings.rlow,
                        plotSettings.rhigh, plotSettings.yOffset)
    frame.GetYaxis().SetNdivisions(5,5,0)
    frame.GetXaxis().SetTitleOffset(3.5)
    frame.GetXaxis().SetTitleFont(63)
    frame.GetXaxis().SetTitleSize(16)
    frame.SetXTitle(axislabel)
    frame.SetYTitle("DATA/MC")

    drawGrid(pad, binning, plotSettings.rlow, plotSettings.rhigh)

    ratioGraph.Draw("P SAME")
    ratioGraph.SetMarkerColor(r.kBlue)
    ratioGraph.SetLineColor(r.kBlue)
    ratioGraph.SetMarkerStyle(21)


def makePlot(dataGraph, mcGraph, ratioGraph, plotSet, title, xAxis, padText, binning, outfile_base,
             fileEndings):
    """
    Create and save the plot into each format that is demanded by the fileEndings parameter.
    The name of the output file(s) is simply the outfile_base + a file ending.
    """
    # Use randomly generated canvas name to avoid seg-faults and run-time warnings
    canvas = r.TCanvas(''.join(choice(ascii_uppercase) for _ in range(6)), "c",
                       500, 500)
    effPad = createPad("pad1", 0.3, 1)

    frame = createFrame(effPad, plotSet.xlow, plotSet.xhigh, plotSet.elow,
                        plotSet.ehigh, plotSet.yOffset)
    frame.GetYaxis().SetNdivisions(510)
    frame.SetYTitle("#epsilon")

    legend = r.TLegend(plotSet.lright, 0.13, 0.9, 0.35, padText)
    legend.SetTextSize(0.05)
    legend.SetFillColor(r.kWhite)
    legend.SetShadowColor(0)

    latex = r.TLatex()
    latex.SetNDC(True)
    latex.SetTextSize(0.05)
    latex.DrawLatex(0.12, 0.92, "CMS preliminary             Run 2016")
    latex.DrawLatex(0.8, 0.92, "#sqrt{s} = 13 TeV")

    drawGrid(effPad, binning, plotSet.elow, plotSet.ehigh)

    dataGraph.Draw("P SAME")
    dataGraph.SetMarkerStyle(20)
    legend.AddEntry(dataGraph, "Data", "PL")

    mcGraph.Draw("P SAME")
    mcGraph.SetMarkerColor(r.kRed)
    mcGraph.SetLineColor(r.kRed)
    mcGraph.SetMarkerStyle(22)
    legend.AddEntry(mcGraph, "MC", "PL")
    legend.Draw()

    text = r.TPaveText(plotSet.tleft, plotSet.tlow, plotSet.tright, plotSet.tup, "NDC")
    text.SetFillColor(r.kWhite)
    text.SetTextSize(0.05)
    text.AddText(title)
    text.Draw()

    drawRatioPad(canvas, plotSet, ratioGraph, binning, xAxis)

    for ending in fileEndings:
        filename = ".".join([outfile_base, ending])
        canvas.SaveAs(filename)


"""
General root settings
"""
r.gROOT.ProcessLine("gErrorIgnoreLevel = 1001") # avoid stdout pollution of ROOT
r.gROOT.SetStyle("Plain")
r.gStyle.SetOptStat(0)
r.gStyle.SetPadRightMargin(0.03)
r.gStyle.SetPadTopMargin(0.09)
r.gStyle.SetPadLeftMargin(2.0)
r.gROOT.SetBatch()


"""
Read json input
"""
with open(args.jsonFile, 'r') as f:
    json = json.loads(f.read())


plotDefaults = StructFromDict(**json["plotting_defaults"])

for finfo in json["input_files"]:
    # json is structured as follows: [0] - filename (relative to input_path), [1] - title, [2] - x-axis label
    # [3] - fixed paramters to be put on plot, [4] - dict containing values to be changed compared to default for plotting
    # [5] - binning in x-axis
    filename = "".join([json["input_path"], finfo[0]])
    outfilebase = "".join([json["output_path"], finfo[0].replace(".root", "")])

    plotSet = deepcopy(plotDefaults) # want to start from the same defaults in every run
    plotSet.setValues(**finfo[4])

    f = r.TFile.Open(filename)
    makePlot(f.Get("DATA"), f.Get("MC"), f.Get("RATIO"), plotSet, finfo[1], finfo[2], finfo[3], finfo[5],
             outfilebase, json["file_endings"])
