import FWCore.ParameterSet.Config as cms

## setup cl_arg parsing
import FWCore.ParameterSet.VarParsing as VarParsing

cl_args = VarParsing.VarParsing()
cl_args.register('fileList', 'list.txt',
                 VarParsing.VarParsing.multiplicity.singleton,
                 VarParsing.VarParsing.varType.string,
                 'File containing the list of files to process')
cl_args.register('outputDir', '',
                 VarParsing.VarParsing.multiplicity.singleton,
                 VarParsing.VarParsing.varType.string,
                 'Output directory')
cl_args.register('inputRgx', '',
                 VarParsing.VarParsing.multiplicity.singleton,
                 VarParsing.VarParsing.varType.string,
                 'Regex to select only a subset of all files in the passed fileList')
cl_args.register('numCPU', 1,
                 VarParsing.VarParsing.multiplicity.singleton,
                 VarParsing.VarParsing.varType.int,
                 'Number of CPUs to use while fitting')
cl_args.register('scenario', 'data',
                 VarParsing.VarParsing.multiplicity.singleton,
                 VarParsing.VarParsing.varType.string,
                 'scenario: data or MC')
cl_args.register('ID', 'Soft2016',
                 VarParsing.VarParsing.multiplicity.singleton,
                 VarParsing.VarParsing.varType.string,
                 'Muon ID to run')
cl_args.register('binning', 'pt_abseta',
                 VarParsing.VarParsing.multiplicity.singleton,
                 VarParsing.VarParsing.varType.string,
                 'Binning to run')

cl_args.parseArguments()

def createInputFileList(fileList, nameRgx=''):
    """
    Create a sanitized list of files that can be passed ot the TagProbeFitTreeAnalyzer
    """
    import re
    with open(fileList, 'r') as f:
        rawlist = f.read().splitlines()

    prependXrd = lambda x : '/'.join(['root://cms-xrd-global.cern.ch', x]) if x.startswith('/store') else ':'.join(['file', x])
    return [prependXrd(f) for f in rawlist if re.search(nameRgx, f)]


def sanitizeInputs(cl_args):
    """
    Chech if command-line inputs can be handled
    """
    def checkValid(arg, valid_args, argname=''):
        if not arg in valid_args:
            print('{} is \'{}\', but has to be one of the following: {}'.format(argname, arg, valid_args))

    checkValid(cl_args.binning, ['eta', 'vtx', 'pt_abseta'], 'binning')
    checkValid(cl_args.ID, ['Soft2016', 'Medium2016', 'Loose2016', 'Tight2016', 'Loose2015'], 'ID')


def defineAndRunFitModule(process, **kwargs):
    """
    Define the fit module

    kwargs:
    - scenario
    - ID
    - name (i.e. binning)
    - ptmin
    - tagReq (tag requirement, string)
    - probeReq (probe requirement, None, or string)
    - UnbinnedVariables (cms.vstring)
    """
    ID = kwargs.pop('ID')
    name = kwargs.pop('name')
    scenario = kwargs.pop('scenario', 'data')

    outdir = kwargs.pop('outdir', './')
    if outdir and not outdir.endswith('/'): outdir += '/'

    outputfile = '{}TnP_MuonID_{}_{}_{}.root'.format(outdir, scenario, ID, name)
    print('Writing output to {} for ID \'{}\' on {} using binning \'{}\'.'.format(outputfile, ID, scenario, name))

    module = process.TnP_MuonID.clone(
        OutputFileName = cms.string(outputfile)
    )

    # binning = kwargs.pop('binning')
    from binnings import getBinning
    binning = getBinning(name)

    den_binning = binning.clone()
    ptmin = kwargs.pop('ptmin')

    if hasattr(den_binning, 'pt'):
        den_binning.pt = cms.vdouble(*[v for v in binning.pt if v >= ptmin])
        if len(den_binning.pt) == 0:
            raise RuntimeError('Make sure \'ptmin\' is less than at least one element of binning.pt')
        if len(den_binning.pt) == 1: den_binning.pt = cms.vdouble(ptmin, den_binning.pt[0])

    tagReq = kwargs.pop('tagReq') # fail if there is no tag requirement
    setattr(den_binning, tagReq, cms.vstring('pass'))
    print('Tag requirement: \'{}\''.format(tagReq))
    probeReq = kwargs.pop('probeReq', None) # don't necessarily need a probe requirement
    if probeReq is not None:
        setattr(den_binning, probeReq, cms.vstring('pass'))
        print('Probe requirement: \'{}\''.format(probeReq))
    else:
        print('No requirements on probe')


    setattr(module.Efficiencies, '{}_{}'.format(ID, name),
            cms.PSet(
                EfficiencyCategoryAndState = cms.vstring(ID, 'above'),
                UnbinnedVariables = kwargs.pop('UnbinnedVariables'),
                BinnedVariables = den_binning,
                BinToPDFmap = cms.vstring('signalPlusBkg')
            ))

    if (kwargs.pop('run', False)):
        print('========== End of Definitions. Following is fitting output ==========\n\n')
        setattr(process, 'TnP_MuonID_{}_{}'.format(ID, name), module)
        setattr(process, 'run_{}_{}'.format(ID, name), cms.Path(module))



# setup the rest
process = cms.Process('TagProbe')
process.load('Configuration.StandardSequences.Services_cff')
process.load('FWCore.MessageService.MessageLogger_cfi')

# necessary for cmssw
process.source = cms.Source('EmptySource')
process.maxEvents = cms.untracked.PSet(input=cms.untracked.int32(1))

print('Defining TagProbeFitAnalyzerTemplate')
tnpAnalyzerVars = cms.PSet(
    mass = cms.vstring("Tag-muon Mass", "2.9", "3.3", "GeV/c^{2}"), #2.8-3.35
    pt = cms.vstring("muon p_{T}", "0", "1000", "GeV/c"),
    eta = cms.vstring("muon #eta", "-2.5", "2.5", ""),
    abseta = cms.vstring("muon |#eta|", "0", "2.5", ""),
    # tag_pt = cms.vstring("Tag p_{T}", "0", "1000", "GeV/c"),
    # tag_abseta = cms.vstring("Tag |#eta|", "0", "2.5", ""),
    tag_nVertices = cms.vstring("Number of vertices", "0", "999", ""),

    # pair_pt = cms.vstring("dimuon p_{T}", "0", "1000", "GeV/c"),

    pair_dphiVtxTimesQ = cms.vstring("q1 * (#phi1-#phi2)", "-6", "6", ""),
    pair_drM1   = cms.vstring("#Delta R(Station 1)", "-99999", "999999", "rad"),
    # pair_distM1 = cms.vstring("dist(Station 1)", "-99999", "999999", "cm"),
    # pair_dz = cms.vstring("dz","-5","5",""),
    pair_probeMultiplicity = cms.vstring("multiplicity","0","99",""),
    dB = cms.vstring("dB", "-1000", "1000", ""),
    dzPV = cms.vstring("dzPV", "-1000", "1000", ""),

    tkTrackerLay = cms.vstring("track.hitPattern.trackerLayersWithMeasurement", "-1", "999", ""),
    tkValidPixelHits = cms.vstring("track.hitPattern.numberOfValidPixelHits", "-1", "999", ""), # unused?
    tkPixelLay = cms.vstring("track.hitPattern.pixelLayersWithMeasurement", "-1", "999", ""),
    # tkChi2 = cms.vstring("track.normalizedChi2", "-1", "999", ""),
    numberOfMatchedStations = cms.vstring("numberOfMatchedStations", "-1", "99", ""), # unused?
    glbChi2 = cms.vstring("global.normalizedChi2", "-9999", "9999", ""),
    glbValidMuHits = cms.vstring("globalTrack.numberOfValidMuonHits", "-1", "9999", ""), # unused?

    # Added for mediumVar
    tkHitFract = cms.vstring("innerTrack.validFraction", "-9999", "9999" ,""),

    chi2LocPos = cms.vstring("combinedQuality.chi2LocalPosition", "-9999", "9999", ""), # renamed in 2016 TnP
    tkKink = cms.vstring("combinedQuality.trkKink","-9999","9999",""),

    segmentCompatibility = cms.vstring("segmentCompatibility", "-1", "5", ""), # renamed in 2016 TnP

    # tracking efficiency
    # tk_deltaR   = cms.vstring("Match #Delta R",    "0", "1000", ""),
    # tk_deltaEta = cms.vstring("Match #Delta #eta", "0", "1000", ""),

    # There is no problem by defining more variables and categories than are present in the TTree as long as they are not used in the Efficiency calculations.
    weight = cms.vstring("weight","0","10","")
)

tnpAnalyzerCats = cms.PSet(
    # TM   = cms.vstring("Tracker muon", "dummy[pass=1,fail=0]"),
    # TMA   = cms.vstring("Tracker muon", "dummy[pass=1,fail=0]"),
    Glb   = cms.vstring("Global", "dummy[pass=1,fail=0]"),
    Loose   = cms.vstring("Loose", "dummy[pass=1,fail=0]"),
    VBTF  = cms.vstring("VBTFLike", "dummy[pass=1,fail=0]"),
    TMOST = cms.vstring("TMOneStationTight", "dummy[pass=1,fail=0]"),
    PF = cms.vstring("PF", "dummy[pass=1,fail=0]"),
    Track_HP = cms.vstring("Track_HP", "dummy[pass=1,fail=0]"),
    Tight2012 = cms.vstring("Tight Id. Muon", "dummy[pass=1,fail=0]"),
    Medium = cms.vstring("Medium Id. Muon", "dummy[pass=1,fail=0]"),

    # 2015 triggers
    tag_Mu7p5_MU = cms.vstring("ProbeTrigger_Track0", "dummy[pass=1,fail=0]"),
    Mu7p5_Track2_Jpsi_TK = cms.vstring("ProbeTrigger_Track0", "dummy[pass=1,fail=0]"),
    tag_Mu7p5_Track2_Jpsi_MU = cms.vstring("ProbeTrigger_Track0", "dummy[pass=1,fail=0]"),
    Mu7p5_Track3p5_Jpsi_TK = cms.vstring("ProbeTrigger_Track0", "dummy[pass=1,fail=0]"),
    tag_Mu7p5_Track3p5_Jpsi_MU = cms.vstring("ProbeTrigger_Track0", "dummy[pass=1,fail=0]"),
    Mu7p5_Track7_Jpsi_TK = cms.vstring("ProbeTrigger_Track0", "dummy[pass=1,fail=0]"),
    tag_Mu7p5_Track7_Jpsi_MU = cms.vstring("ProbeTrigger_Track0", "dummy[pass=1,fail=0]"),
    #
    Mu7p5_L2Mu2_Jpsi_L2 = cms.vstring("ProbeTrigger_Track0", "dummy[pass=1,fail=0]"),
    tag_Mu7p5_L2Mu2_Jpsi_MU = cms.vstring("ProbeTrigger_Track0", "dummy[pass=1,fail=0]"),
    Mu7p5_L2Mu2_L2 = cms.vstring("ProbeTrigger_Track0", "dummy[pass=1,fail=0]"),
    # # Onia triggers
    # Dimuon16_L1L2 = cms.vstring("ProbeTrigger_Track0", "dummy[pass=1,fail=0]"),
    # Dimuon10_L1L2 = cms.vstring("ProbeTrigger_Track0", "dummy[pass=1,fail=0]"),
    # #
    # Mu_L3 = cms.vstring("ProbeTrigger_Track0", "dummy[pass=1,fail=0]"),

    # # vertexing efficiency
    # Dimuon6_Jpsi_NoVertexing = cms.vstring("ProbeTrigger_Track0", "dummy[pass=1,fail=0]"),
    # tag_Dimuon6_Jpsi_NoVertexing = cms.vstring("ProbeTrigger_Track0", "dummy[pass=1,fail=0]"),
    # Dimuon0er16_Jpsi_NoVertexing = cms.vstring("ProbeTrigger_Track0", "dummy[pass=1,fail=0]"),
    # tag_Dimuon0er16_Jpsi_NoVertexing = cms.vstring("ProbeTrigger_Track0", "dummy[pass=1,fail=0]"),
    # Dimuon16_Jpsi = cms.vstring("ProbeTrigger_Track0", "dummy[pass=1,fail=0]"),
    # Dimuon10_Jpsi_Barrel = cms.vstring("ProbeTrigger_Track0", "dummy[pass=1,fail=0]"),
    #
    # mcTrue = cms.vstring("MC true", "dummy[true=1,false=0]"),
    # # test
    # DoubleMu17TkMu8_TkMu8leg = cms.vstring("ProbeTrigger_Track0", "dummy[pass=1,fail=0]"),
    # tag_DoubleMu17TkMu8_TkMu8leg = cms.vstring("ProbeTrigger_Track0", "dummy[pass=1,fail=0]"),
    Mu8 = cms.vstring("ProbeTrigger_Track0", "dummy[pass=1,fail=0]"),
    tag_Mu8 = cms.vstring("ProbeTrigger_Track0", "dummy[pass=1,fail=0]"),
    # # Mu25
    # Mu25TkMu0Onia_TM = cms.vstring("ProbeTrigger_Track0", "dummy[pass=1,fail=0]"),
    # tag_Mu25TkMu0Onia_L3_MU = cms.vstring("ProbeTrigger_Track0", "dummy[pass=1,fail=0]"),
    # # Mu16
    # Mu16TkMu0Onia_TM = cms.vstring("ProbeTrigger_Track0", "dummy[pass=1,fail=0]"),
    # tag_Mu16TkMu0Onia_L3_MU = cms.vstring("ProbeTrigger_Track0", "dummy[pass=1,fail=0]"),
)

tnpAnalyzerExprs = cms.PSet(
    Loose2015Var = cms.vstring("Loose2015Var", "PF==1", "PF"),
    Loose2016Var = cms.vstring("Loose2016Var", "Loose == 1", "Loose"), # Loose is present in TTrees! Doing it this way, in order to have a consistent definition of the IDs (cuts) below
    Medium2016Var = cms.vstring("Medium2016Var", "Loose == 1 && tkHitFract > 0.49 && ((Glb == 1 && glbChi2 < 3 && chi2LocPos < 12. && tkKink < 20. && segmentCompatibility > 3.03) || segmentCompatibility > 0.451)",
                                "Loose", "tkHitFract", "Glb", "glbChi2", "chi2LocPos", "tkKink", "segmentCompatibility"),
    Soft2016Var = cms.vstring("Soft2016Var", "TMOST == 1 && tkTrackerLay > 5 && tkPixelLay > 0 && abs(dzPV) < 20. && abs(dB) < 0.3",
                              "TMOST", "tkTrackerLay", "tkPixelLay", "dzPV", "dB"),
    Tight2016Var = cms.vstring("Tight2016Var", "Glb == 1 && PF == 1 && glbChi2 < 10 && glbValidMuHits > 0 && numberOfMatchedStations > 1 && dB < 0.2 && dzPV < 0.5 && tkValidPixelHits > 0 && tkTrackerLay > 5",
                               "Glb", "PF", "glbChi2", "glbValidMuHits", "numberOfMatchedStations", "dB", "dzPV", "tkValidPixelHits", "tkTrackerLay")
)

tnpAnalyzerCuts = cms.PSet(
    Loose2015 = cms.vstring("Loose2015", "Loose2015Var", "0.5"),
    Loose2016 = cms.vstring("Loose2016", "Loose2016Var", "0.5"),
    Medium2016 = cms.vstring("Medium2016", "Medium2016Var", "0.5"),
    Soft2016 = cms.vstring("Soft2016", "Soft2016Var", "0.5"),
    Tight2016 = cms.vstring("Tight2016", "Tight2016Var", "0.5"),
)

tnpAnalyzerPDFs = cms.PSet(
    signalPlusBkg = cms.vstring(
        "CBShape::signal(mass, mean[3.1,3.0,3.2], sigma[0.05,0.02,0.06], alpha[3., 0.5, 5.], n[1, 0.1, 100.])",
        #"Chebychev::backgroundPass(mass, {cPass[0,-0.5,0.5], cPass2[0,-0.5,0.5]})",
        #"Chebychev::backgroundFail(mass, {cFail[0,-0.5,0.5], cFail2[0,-0.5,0.5]})",
        #"Gaussian::signal(mass, mean[3.1,3.0,3.2], sigma[0.05,0.02,0.1])",
        "Exponential::backgroundPass(mass, lp[0,-5,5])",
        "Exponential::backgroundFail(mass, lf[0,-5,5])",
        "efficiency[0.9,0,1]",
        "signalFractionInPassing[0.9]"
    )
)

tnpAnalyzerTmplt = cms.EDAnalyzer('TagProbeFitTreeAnalyzer',
    WeightVariable = cms.string('weight'),
    NumCPU = cms.uint32(cl_args.numCPU),
    SaveWorkspace = cms.bool(False),

    Variables = tnpAnalyzerVars,
    Categories = tnpAnalyzerCats,
    Expressions = tnpAnalyzerExprs,
    Cuts = tnpAnalyzerCuts,
    PDFs = tnpAnalyzerPDFs,

    binnedFit = cms.bool(True),
    binsForFit = cms.uint32(40),

    Efficiencies = cms.PSet() # will be filled later
)
print('Analyzer defined')

# create module and define it in process
process.TnP_MuonID = tnpAnalyzerTmplt.clone(
    InputFileNames = cms.vstring(createInputFileList(cl_args.fileList, cl_args.inputRgx)),
    InputDirectoryName = cms.string('tpTree'),
    InputTreeName = cms.string('fitter_tree'),
    OutputFileName = cms.string('TnP_MuonID_{}.root'.format(cl_args.scenario)),
    Efficiencies = cms.PSet()
)



UnbinnedVariables = cms.vstring('mass') # for data
if 'mc' in cl_args.scenario:
    UnbinnedVariables = cms.vstring('mass', 'weight')


defineAndRunFitModule(process, ID=cl_args.ID, ptmin=2,
                      # tagReq='tag_{}_MU'.format('Mu7p5_Track2_Jpsi'),
                      # probeReq='{}_TK'.format('Mu7p5_Track2_Jpsi'),
                      tagReq='tag_Mu8',
                      name=cl_args.binning, scenario=cl_args.scenario,
                      UnbinnedVariables=UnbinnedVariables, run=True, outdir=cl_args.outputDir)
