import math
import ROOT

class TGAPoint:
    """
    simple struct storing all the information from a point in a TGraphAsymmErrors.
    At the moment only errors in y-direction are stored
    """
    def __init__(self, x, y, eh, el, exh, elh):
        """
        construct from (x,y) coordinates and high and low error on y
        """
        self.x = x
        self.y = y
        self.eh_y = eh
        self.el_y = el
        self.eh_x = exh
        self.el_x = elh


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
    return TGAPoint(x, y, graph.GetErrorYhigh(index), graph.GetErrorYlow(index),
                    graph.GetErrorXhigh(index), graph.GetErrorXlow(index))


def divideGraphs(gNum, gDenom):
    """
    Divide the y-values of graph gNum by graph gDenom and return a new graph with the result.
    Use the x information from the gNum graph
    """
    graph = None

    nPoints = gNum.GetN()
    if nPoints != gDenom.GetN() or nPoints < 1:
        print("Cannot divide graphs with different numbers of points or zero points")
    else:
        graph = ROOT.TGraphAsymmErrors(nPoints)
        for i in range(0, nPoints):
            pNum = getPoint(gNum, i)
            pDenom = getPoint(gDenom, i)

            ratio = pNum.y / pDenom.y
            err_low_ratio = ratio * math.sqrt((pNum.el_y/pNum.y)**2 + (pDenom.el_y/pNum.y)**2)
            err_high_ratio = ratio * math.sqrt(pNum.eh_y**2 + pDenom.eh_y**2)

            graph.SetPoint(i, pNum.x, ratio)
            graph.SetPointError(i, pNum.el_x, pNum.eh_x, err_low_ratio, err_high_ratio)

            # print("{} {} {}".format(pNum.y, pDenom.y, ratio))

    return graph
