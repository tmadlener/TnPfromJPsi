import FWCore.ParameterSet.Config as cms


_separated = cms.PSet(
    pair_drM1 = cms.vdouble(0.5, 10),
    pair_probeMultiplicity = cms.vdouble(0.5, 1.5)
)

vtx_bins = cms.PSet(
    _separated,
    abseta = cms.vdouble(0.0, 2.4),
    pt = cms.vdouble(8.0, 500),
    tag_nVertices = cms.vdouble(*[v + 0.5 for v in range(0, 31, 2)])
)

eta_bins = cms.PSet(
    _separated,
    pt = cms.vdouble(8.0, 20.0),
    eta = cms.vdouble(-2.1, -1.6, -1.2, -0.9, -0.6, -0.3, -0.2, 0, 0.2, 0.3, 0.6, 0.9, 1.2, 1.6, 2.1)
)
