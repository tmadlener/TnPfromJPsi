# TnPfromJPsi - Utilities used in the TnP from JPsi

This repository holds some python scripts facilitating the tasks necessary for doing Tag-and-Probe (TnP) studies. This repository is somewhat tailerd to the use cases that emerge in TnP studies on JPsis.

All scripts make use of pythons `argparse` package and should thus support the `--help` argument for a short description.
The following sections explain the usage in the most basic cases. All of them should work with python >= 2.7 and ROOT 6 (Basically a setup CMSSW environment).

## Other useful repositories of the Muon POG

The Muon POG currently has more utilities in other repositories on [github](https://github.com/cms-MuonPOG):
-   [TnPUtils](https://github.com/cms-MuonPOG/TnPUtils): Some general purpose utilities for working with TnP ntuples.
-   [TnPfromZ](https://github.com/cms-MuonPOG/TnPfromZ): Repository with the same purpose as this one, but for TnP studies on Z samples.

## Extract Fit Canvas from TnPTreeAnalyzer output file

The script `PlotEfficiency/extractFitCanvas.py` can be used to extract **all** canvases that are stored in the passed input file(s).
The basic configuration is done via a JSON file (see `examples/extractFitcanvas.json`) but some of the options can be overridden via arguments.
The script recursively traverses all the TDirectories in an input file and stores all TCanvas that are found, if they match the passed regex.
The plots appear in a new folder under the passed `--output_dir` option that is computed from the input file name.

#### Example usage:
```bash
# use everything as is in the JSON file
python PlotEfficiency/extractFitCanvas.py examples/extractFitCanvas.json
```

## Extract Efficiency plots form TnPTreeAnalyzer output file

The script `PlotEfficiency/extractPlots.py` extracts the efficiency graphs from **two** input files: One MC file and one DATA file. It calculates the ratio of the two and stores the DATA, MC and RATIO graph into a new ROOT file.
It is intended as some sort of intermediate step to disentangle plotting and retrieving data from the TnPTreeAnalyzer output files.
It expects at least one JSON file (see `examples/extractPlots.json`), but it is also possible to pass more than one JSON file, which will then be processed one by one.

#### Example usage:
```bash
# pretty useless, but possible passing of the same JSON file twice
python PlotEfficiency/extractPlots.py examples/extractPlots.json examples/extractPlots.json
```

## Make Efficiency plots

Once the plots have been extracted from the TnPTreeAnalyzer output file(s) via `PlotEfficiency/extractPlots.py`, the `PlotEfficiency/makeEfficiencyPlots.py` can be used to actually produce the efficiency plots. All configuration is done via a JSON file (see `examples/makePlots.json`). The JSON file defines some default settings, which can be changed individually for each input file.

The parameters are:

| parameter                        | meaning                                                                         |
| -------------------------------- | ------------------------------------------------------------------------------- |
| `xlow` (`xhigh`)                 | lower (upper) bound of x-axis                                                   |
| `elow` (`ehigh`)                 | lower (upper) bound of efficiency                                               |
| `rlow` (`rhigh`)                 | lower (upper) bound of ratio                                                    |
| `tleft` (`tright`, `low`, `tup`) | left (right, lower, upper) corner coords of the text field containing the title |
| `lright`                         | lower right corner coord of the legend                                          |
| `yOffset`                        | title offset of the y-axis                                                      |

The list of parameters of each input file is the following:
0. Path to the file relative to *input_path*
1. The ID (resp. title) that will get printed onto the plot
2. The x-Axis label
3. The string of fixed parameters, that will be added to the legend
4. Dictionary of changes to be made to the default plotting settings (see parameters above)
5. The binning used for the given scenario (only used to plot a grid)

#### Example usage:
```bash
# run this only after the appropriate root file(s) has been created with extractPlots.py
python PlotEfficiency/makeEfficiencyPlots.py examples/makePlots.json
```

## Create a Pickle and a ROOT file

Create a .pkl and .root file containing all efficiencies of all passed files. All configuration is done via JSON file (see `examples/createPickleFile.json`).

The list of parameters of each input file is the following:
0. Path to the file relative to *path*
1. The ID
2. The scenario (i.e. which variable has been binned)
3. An additional string to differentiate between different bins of one scenario (e.g. when looking at pt binned efficiencies, this is normally also done in |eta| bins.)

#### Example usage:
```bash
# run this only after the appropriate root file(s) have been created with extractPlots.py
python createPklFile.py examples/createPickleFile.json
```

## A complete walkthrough

If you have cloned the repository everything should work out of the box (i.e. the example JSON files are set such, that you can executed the following commands one after the other, so that in the end you have a full set of plots as well as a .pkl and a .root file containing the results)

```bash
# first let's have a look at the fit results
python PlotEfficiencies/extractFitCanvas.py examples/extractFitCanvas.py

# you should now have a new folder 'Results/Figures/FitCanvas/' containing some .pdfs
# ls Results/Figures/FitCanvas
# you will notice that the generated file-names are the same for MC and DATA input, so that you are left with only the
# MC files in this case.

# in order to plot the results we have to extract them from the TnP Analyzer Tree first
python PlotEfficiency/extractPlots.py examples/extractPlots.json

# you should now have a Results/MuonID_Loose2016_vtx.root file

# now create the plots
python PlotEfficiency/makeEfficiencyPlots.py examples/makePlots.json   

# this should yield the Results/Figures/MuonID_Loose2016_vtx.pdf

# finally we can create a .pkl and a .root file (although it's rather useless with only one input)
python createPklFile.py examples/createPicklefile.json

# this should give the files Results/example_Loose_vtx.{pkl,root}
```
