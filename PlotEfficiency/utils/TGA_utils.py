import math
import ROOT as r

from miscHelpers import getOverlappingBins


class TGAPoint:
    """
    simple struct storing all the information from a point in a TGraphAsymmErrors.
    At the moment only errors in y-direction are stored
    """
    def __init__(self, x, y, eh, el, exh, exl):
        """
        construct from (x,y) coordinates and high and low error on y
        """
        self.x = x
        self.y = y
        self.eh_y = eh
        self.el_y = el
        self.eh_x = exh
        self.el_x = exl


    def __str__(self):
        """
        Print point
        """
        return " x = {:6.4f}, y = {:6.4f} (+{:6.4f} -{:6.4f})".format(self.x, self.y, self.eh_y, self.el_y)


def getPoint(graph, index):
    """
    get the point index from the passed graph
    """
    x = r.Double(0)
    y = r.Double(0)
    graph.GetPoint(index, x, y)
    return TGAPoint(x, y, graph.GetErrorYhigh(index), graph.GetErrorYlow(index),
                    graph.GetErrorXhigh(index), graph.GetErrorXlow(index))


def getXBinning(graph):
    """
    Get the binning of the x-axis from the passed graph.
    The binning is calculated from the x-central value and the errors of it
    """
    bins = []
    if graph.GetN() < 1: # can't have bins if there are no points in the graph
        return bins

    # loop over all points and always add only the lower edge of the bin (which in turn serves for the upper edge
    # of the last bin)
    N = graph.GetN()
    for i in range(0, N):
        point = getPoint(graph, i)
        bins.append(point.x - point.el_x)

    # point is still in scope here (thanks Python)
    # We can add the upper edge of the last bin without retrieving the point again
    bins.append(point.x + point.eh_x)

    return bins


def divideGraphs(gNum, gDenom):
    """
    Divide the y-values of graph gNum by graph gDenom and return a new graph with the result.
    NOTE: It is assumed that both TGraphAsymmErrors are binned in the same way along the x-direction
    and the returned graph only has as many points as there are (exactly) overlapping bins in the input graphs.
    The x-values are taken from the numerator graph
    """
    graph = None

    if min(gNum.GetN(), gDenom.GetN()) < 1:
        print("Cannot divide graphs when one graph has zero points")
        return None

    bins = getOverlappingBins(getXBinning(gNum), getXBinning(gDenom))

    graph = r.TGraphAsymmErrors()
    iPoint = 0
    for i in range(0, len(bins[0]) - 1): # both lists in bins should have the same length!
        pNum = getPoint(gNum, bins[0][i])
        pDenom = getPoint(gDenom, bins[1][i])

        if pDenom.y == 0: continue # Still can't divide by 0

        ratio = pNum.y / pDenom.y

        err_low_ratio = ratio * math.sqrt((pNum.el_y/pNum.y)**2 + (pDenom.el_y/pDenom.y)**2)
        err_high_ratio = ratio * math.sqrt((pNum.eh_y/pNum.y)**2 + (pDenom.eh_y/pDenom.y)**2)

        graph.SetPoint(iPoint, pNum.x, ratio)
        graph.SetPointError(iPoint, pNum.el_x, pNum.eh_x, err_low_ratio, err_high_ratio)

        iPoint += 1
        # print("{} {} {}".format(pNum.y, pDenom.y, ratio))

    return graph
