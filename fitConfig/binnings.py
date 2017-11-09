import FWCore.ParameterSet.Config as cms

import re

_separated = cms.PSet(
    pair_drM1 = cms.vdouble(0.5, 10),
    pair_probeMultiplicity = cms.vdouble(0.5, 1.5)
)

_vtx_bins = cms.PSet(
    _separated,
    abseta = cms.vdouble(0.0, 2.4),
    pt = cms.vdouble(8.0, 500),
    tag_nVertices = cms.vdouble(*[v + 0.5 for v in range(0, 31, 2)])
)

_eta_bins = cms.PSet(
    _separated,
    pt = cms.vdouble(8.0, 20.0),
    eta = cms.vdouble(-2.4, -2.1, -1.6, -1.2, -0.9, -0.6, -0.3, -0.2, 0, 0.2, 0.3, 0.6, 0.9, 1.2, 1.6, 2.1, 2.4)
)

_pt_abseta_bins = cms.PSet(
    _separated,
    pt = cms.vdouble(2.0, 2.5, 2.75, 3.0, 3.25, 3.5, 3.75, 4.0, 4.5, 5.0, 6.0, 8.0, 10.0, 15.0, 20.0, 30.0, 40.0),
    abseta = cms.vdouble(0, 0.9, 1.2, 2.1, 2.4)
)


def getBinning(name):
    """
    Get the binning PSet corresponding to the passed name
    """
    if name == 'eta': return _eta_bins
    if name == 'vtx': return _vtx_bins
    if name == 'pt_abseta': return _pt_abseta_bins

    def get_bins_from_name(name, binvar, bin_vector):
        bin_rgx = r''.join([binvar, r'_([0-9]+)', r'_?([0-9]+)?'])
        m = re.search(bin_rgx, name)
        bin_inds = []
        if m:
            bin_inds = [int(i) for i in m.groups() if i is not None]
        else:
            print('not matched {} to {}'.format(bin_rgx, name))

        if len(bin_inds) == 1: # only one bin
            return cms.vdouble([bin_vector[bin_inds[0]], bin_vector[bin_inds[0] + 1]])

        if len(bin_inds) == 2: # range of bins
            bin_inds[-1] += 1 # use correct upper bound of last bin
            return cms.vdouble([bin_vector[i] for i in range(bin_inds[0], bin_inds[1])])


    if name.startswith('eta_'):
        return _eta_bins.clone(eta = get_bins_from_name(name, 'eta', _eta_bins.eta))

    if name.startswith('vtx_'):
        return _vtx_bins.clone(tag_nVertices = get_bins_from_name(name, 'vtx', _vtx_bins.tag_nVertices))

    if name.startswith('pt_abseta_'):
        var_bins = _pt_abseta_bins.clone()
        if 'pt' in name[len('pt_abseta_'):]:
            var_bins.pt = get_bins_from_name(name, 'pt', _pt_abseta_bins.pt)

        if 'abseta' in name[len('pt_abseta_'):]:
            var_bins.abseta = get_bins_from_name(name, 'abseta', _pt_abseta_bins.abseta)

        return var_bins

    return None
