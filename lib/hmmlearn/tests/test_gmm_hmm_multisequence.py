import itertools

import numpy as np
from numpy.testing import assert_allclose
import pytest

from hmmlearn import hmm, vhmm
from hmmlearn.base import ConvergenceMonitor


# Example multi-sequence data, arranged as shape
# (n_sequences, n_samples, n_features)
#
# This data is a reduced subset of data_training.npy
# from issue https://github.com/hmmlearn/hmmlearn/issues/410
# illustrating GMMHMM fit diverging during EM iterations.
#
# Transformations to reduce data volume:
# - keep only first 3 of many sequences, discard rest
# - keep only first 50 of many samples per sequence, discard rest
# - keep only first 4 of 17 features per sample, discard rest
EXAMPLE_SEQUENCES_ISSUE_410_PRUNED = np.array(
    [
        np.array(
            [
                [0.00992058, 0.44151747, 0.5395124, 0.40644765],
                [0.00962487, 0.45613006, 0.52375835, 0.3899082],
                [0.00915721, 0.47111648, 0.5103008, 0.3846845],
                [0.00916073, 0.4749602, 0.5241155, 0.39899495],
                [0.0090966, 0.47398633, 0.53792244, 0.41295874],
                [0.00953476, 0.47201437, 0.5322343, 0.41661483],
                [0.00916542, 0.4455471, 0.55598766, 0.40831617],
                [0.00906925, 0.43173638, 0.56246823, 0.39109665],
                [0.00826067, 0.4136997, 0.58712745, 0.39158684],
                [0.00828806, 0.41975173, 0.60497123, 0.38206288],
                [0.00788883, 0.397979, 0.63639283, 0.3627324],
                [0.00765208, 0.38908702, 0.65764546, 0.3516956],
                [0.00738148, 0.38130987, 0.6522844, 0.36725503],
                [0.00717299, 0.37383446, 0.6722188, 0.37951013],
                [0.0073711, 0.37058228, 0.6799041, 0.3860375],
                [0.00728311, 0.37892842, 0.65606904, 0.39165357],
                [0.00730301, 0.39218283, 0.6332023, 0.3976117],
                [0.00713718, 0.38652796, 0.6423802, 0.34927416],
                [0.00683423, 0.3656172, 0.68119335, 0.2912439],
                [0.00663389, 0.34920084, 0.68535674, 0.28290597],
                [0.00625478, 0.3525497, 0.6658849, 0.30369937],
                [0.00614696, 0.35593832, 0.65440905, 0.3450122],
                [0.00611069, 0.35073754, 0.6559732, 0.33597857],
                [0.00635504, 0.3360095, 0.6800729, 0.32301348],
                [0.00617533, 0.3444746, 0.6745925, 0.34155408],
                [0.00592057, 0.35373318, 0.66947186, 0.32476413],
                [0.00564618, 0.36178407, 0.6560819, 0.3297305],
                [0.00572176, 0.37058342, 0.6551206, 0.2967357],
                [0.00578371, 0.39031005, 0.64601576, 0.33421013],
                [0.00577161, 0.41922286, 0.6089396, 0.3717376],
                [0.00579954, 0.41518527, 0.60426843, 0.38774568],
                [0.00578072, 0.40165138, 0.6203536, 0.34574744],
                [0.00583212, 0.42201585, 0.60890085, 0.38103116],
                [0.00572761, 0.40093482, 0.63888615, 0.36249077],
                [0.00594841, 0.3804375, 0.6576098, 0.37927687],
                [0.0059343, 0.34200934, 0.693946, 0.3007063],
                [0.00591482, 0.3709248, 0.66136825, 0.32304856],
                [0.0055425, 0.41159946, 0.62043166, 0.3460799],
                [0.00548492, 0.40038764, 0.6440804, 0.33333993],
                [0.00552325, 0.36867827, 0.6703099, 0.30612737],
                [0.00553349, 0.35795027, 0.67543924, 0.27393535],
                [0.00558642, 0.4015568, 0.62600005, 0.31275502],
                [0.00565522, 0.40925154, 0.6178226, 0.3131643],
                [0.0058172, 0.42638385, 0.6077434, 0.33476466],
                [0.00585697, 0.40742254, 0.6218038, 0.37967283],
                [0.00591527, 0.4296229, 0.6016123, 0.3985932],
                [0.00604816, 0.43141186, 0.59317786, 0.42083132],
                [0.00621391, 0.4110697, 0.6092669, 0.38827285],
                [0.00656536, 0.39309287, 0.60035396, 0.41596898],
                [0.00693208, 0.37821782, 0.59813255, 0.4394344],
            ],
            dtype=np.float32,
        ),
        np.array(
            [
                [0.00318667, 0.48804316, 0.52020603, 0.36232004],
                [0.00322638, 0.48808283, 0.5341949, 0.37973505],
                [0.00329762, 0.47688982, 0.5563834, 0.4047565],
                [0.00321911, 0.48151806, 0.54239404, 0.38407174],
                [0.00400121, 0.5309283, 0.49719027, 0.40301552],
                [0.00461331, 0.5856188, 0.44557935, 0.40280044],
                [0.0048873, 0.59214115, 0.4330637, 0.43839055],
                [0.00411017, 0.53695357, 0.49013752, 0.3832056],
                [0.00357234, 0.48548815, 0.54152006, 0.3475358],
                [0.00341532, 0.46990934, 0.57406586, 0.33449954],
                [0.00345838, 0.50714695, 0.51190466, 0.38789546],
                [0.00341552, 0.526225, 0.48219037, 0.41689718],
                [0.0034434, 0.5293161, 0.47968563, 0.4379618],
                [0.00342251, 0.49587825, 0.53558546, 0.4021806],
                [0.00329584, 0.5082987, 0.52165693, 0.4086313],
                [0.0031443, 0.519554, 0.49245426, 0.3961157],
                [0.0030792, 0.5455676, 0.45203313, 0.423718],
                [0.00320465, 0.5504491, 0.43865028, 0.45784852],
                [0.00329045, 0.52342314, 0.48308045, 0.455756],
                [0.00342623, 0.50302553, 0.495605, 0.45614803],
                [0.00347294, 0.48462915, 0.52492356, 0.41467494],
                [0.00352737, 0.45118907, 0.53679097, 0.38664353],
                [0.00349953, 0.40440804, 0.59128445, 0.3342833],
                [0.00343233, 0.385624, 0.61139005, 0.29829293],
                [0.00333838, 0.4443106, 0.55629146, 0.3360141],
                [0.00341689, 0.47139308, 0.5338217, 0.34617022],
                [0.00349784, 0.49085665, 0.5179333, 0.38301566],
                [0.00354852, 0.45714432, 0.5581238, 0.3514836],
                [0.00336909, 0.4432368, 0.5735479, 0.37587976],
                [0.00334855, 0.42174804, 0.60338825, 0.36684743],
                [0.00340526, 0.4299499, 0.5964124, 0.38658547],
                [0.00355591, 0.44496518, 0.5775449, 0.37693518],
                [0.00368621, 0.4641773, 0.54175687, 0.38873497],
                [0.00392683, 0.48638234, 0.52129495, 0.40342456],
                [0.00444013, 0.5311254, 0.4699971, 0.41572142],
                [0.00559078, 0.5725662, 0.42817408, 0.42607802],
                [0.00651121, 0.60758656, 0.3687854, 0.45583618],
                [0.00731191, 0.60793436, 0.36194792, 0.46369436],
                [0.0075791, 0.56968933, 0.409531, 0.40896642],
                [0.00813889, 0.5602184, 0.43285215, 0.35258207],
                [0.00887025, 0.5855726, 0.40227312, 0.35542902],
                [0.00897418, 0.609533, 0.35594714, 0.3942479],
                [0.01022383, 0.6129873, 0.3352133, 0.47778368],
                [0.0095141, 0.5595026, 0.4162315, 0.45395738],
                [0.00841102, 0.49951875, 0.48765272, 0.4517436],
                [0.00826918, 0.45066664, 0.5471808, 0.3476721],
                [0.01868482, 0.39936644, 0.55312306, 0.43391562],
                [0.04211371, 0.3675188, 0.56271124, 0.53548455],
                [0.07297403, 0.3576941, 0.57314515, 0.6578705],
                [0.10756538, 0.413695, 0.5337025, 0.653491],
            ],
            dtype=np.float32,
        ),
        np.array(
            [
                [0.00302289, 0.47364405, 0.53537434, 0.45129624],
                [0.00311589, 0.45328405, 0.5570029, 0.42494437],
                [0.00315774, 0.44939527, 0.5723259, 0.4117937],
                [0.00314883, 0.46795434, 0.54135257, 0.3953221],
                [0.00309122, 0.49266115, 0.5156292, 0.4080569],
                [0.00312682, 0.49728185, 0.51451075, 0.41902116],
                [0.00323118, 0.49948877, 0.5244724, 0.45043528],
                [0.00325324, 0.47703367, 0.5608516, 0.42876282],
                [0.00322127, 0.4831656, 0.5520302, 0.43367508],
                [0.00314415, 0.5081604, 0.5305388, 0.47354758],
                [0.00307265, 0.51409185, 0.5208431, 0.46550223],
                [0.00312928, 0.5049119, 0.5267695, 0.44442567],
                [0.00313668, 0.47089654, 0.55917096, 0.37248307],
                [0.00320294, 0.45442477, 0.57189673, 0.38878405],
                [0.00317113, 0.43952465, 0.59469926, 0.3535012],
                [0.00323172, 0.46230638, 0.5713085, 0.39267808],
                [0.00323527, 0.50055844, 0.52773774, 0.4445253],
                [0.00322912, 0.5141386, 0.501789, 0.488796],
                [0.00312394, 0.53217465, 0.47047156, 0.49383518],
                [0.00305265, 0.5208433, 0.50014937, 0.459741],
                [0.00305853, 0.51386, 0.5120822, 0.43915167],
                [0.00311382, 0.47278965, 0.57036394, 0.45423037],
                [0.00318763, 0.46807718, 0.5674287, 0.43843716],
                [0.00318154, 0.47042188, 0.5779207, 0.44580007],
                [0.00303793, 0.46571356, 0.5818657, 0.4107192],
                [0.00299003, 0.44406536, 0.60040486, 0.38005733],
                [0.00296462, 0.44092676, 0.59199274, 0.3560812],
                [0.00307418, 0.45244223, 0.56540257, 0.33132356],
                [0.00302929, 0.47221994, 0.5470938, 0.36822143],
                [0.00301338, 0.47062206, 0.54911035, 0.3680197],
                [0.00291349, 0.45564204, 0.5619591, 0.3808152],
                [0.00295025, 0.47307628, 0.54229873, 0.35219967],
                [0.00289911, 0.4725018, 0.54288876, 0.38314143],
                [0.00291358, 0.45272404, 0.5728319, 0.37214962],
                [0.00294044, 0.4570347, 0.5649049, 0.42110214],
                [0.00298315, 0.4561437, 0.55468136, 0.40142712],
                [0.00303691, 0.49613172, 0.52464443, 0.42899716],
                [0.00300609, 0.49105296, 0.5310325, 0.41341364],
                [0.00305483, 0.532239, 0.485052, 0.46893936],
                [0.00298801, 0.51202387, 0.49897632, 0.45285705],
                [0.0030795, 0.5070261, 0.5062058, 0.44057184],
                [0.00303104, 0.47002167, 0.56080073, 0.40074068],
                [0.00308184, 0.4575324, 0.56803167, 0.3928257],
                [0.00291516, 0.44490653, 0.58391964, 0.40129626],
                [0.00289649, 0.4531514, 0.5818511, 0.407385],
                [0.00284487, 0.4488143, 0.5850243, 0.41675568],
                [0.00291576, 0.4616304, 0.57469726, 0.40793785],
                [0.00287342, 0.46473294, 0.54888374, 0.41002542],
                [0.00303153, 0.4966541, 0.5055506, 0.4316879],
                [0.00327755, 0.45762977, 0.529044, 0.4493881],
            ],
            dtype=np.float32,
        ),
    ]
)


class StrictMonitor(ConvergenceMonitor):
    @property
    def converged(self):
        # The default ConvergenceMonitor regards some scenarios
        # as "converged" when they have not necessarily converged:
        #
        # 1. exhausting max iterations
        # 2. decreases in log_prob between successive EM iterations
        #
        # This second behaviour should (ignoring numerical problems)
        # never happen if the EM implementation is correct. EM is a
        # local optimisation method, it may not find a global maxima,
        # but log_prob should always be non-decreasing between each
        # pair of successive iterations.

        assert not np.isnan(self.history[-1]), "log_prob must not be nan"

        if len(self.history) < 2:
            return False

        assert self.history[-1] >= self.history[-2] - self.tol, \
            "log_prob must be non-decreasing"

        return self.history[-1] - self.history[-2] < self.tol


def make_permutations(items):
    sequence_indices = list(range(len(items)))
    return [list(p) for p in itertools.permutations(sequence_indices)]


def setup_em(covariance_type, implementation, init_params, verbose):
    model = hmm.GMMHMM(
        n_components=2,
        n_mix=2,
        n_iter=100,
        covariance_type=covariance_type,
        verbose=verbose,
        init_params=init_params,
        random_state=1234,
        implementation=implementation
    )

    # don't use random parameters for testing
    init = 1. / model.n_components
    model.startprob_ = np.full(model.n_components, init)
    model.transmat_ = \
        np.full((model.n_components, model.n_components), init)

    model.monitor_ = StrictMonitor(
        model.monitor_.tol,
        model.monitor_.n_iter,
        model.monitor_.verbose,
    )
    return model

def setup_vi(covariance_type, implementation, init_params, verbose, lengths):
    model = vhmm.VariationalGMMHMM(
        n_components=2,
        n_mix=2,
        n_iter=100,
        covariance_type=covariance_type,
        verbose=verbose,
        init_params=init_params,
        random_state=1234,
        implementation=implementation
    )
    # don't use random parameters for testing
    prior_init = 1. / model.n_components
    model.startprob_prior_ = np.full(model.n_components, prior_init)
    model.transmat_prior_= \
        np.full((model.n_components, model.n_components), prior_init)
    model.startprob_posterior_ = np.full(model.n_components, len(lengths) * prior_init)
    model.transmat_prior_= \
        np.full((model.n_components, model.n_components), sum(lengths) * prior_init)
    model.monitor_ = StrictMonitor(
        model.monitor_.tol,
        model.monitor_.n_iter,
        model.monitor_.verbose,
    )
    return model

@pytest.mark.parametrize("hmm_type",
                         ["em", "vi"])
@pytest.mark.parametrize("covariance_type",
                         ["diag", "spherical", "tied", "full"])
@pytest.mark.parametrize("implementation", ["scaling", "log"])
def test_gmmhmm_multi_sequence_fit_invariant_to_sequence_ordering(
    hmm_type, covariance_type, implementation, init_params='mcw', verbose=False
):
    """
    Sanity check GMM-HMM fit behaviour when run on multiple sequences
    aka multiple frames.

    Training data consumed during GMM-HMM fit is packed into a single
    array X containing one or more sequences. In the case where
    there are two or more input sequences, the ordering that the
    sequences are packed into X should not influence the results
    of the fit. Major differences in convergence during EM
    iterations by merely permuting sequence order in the input
    indicates a likely defect in the fit implementation.

    Note: the ordering of samples inside a given sequence
    is very meaningful, permuting the order of samples would
    destroy the the state transition structure in the input data.

    See issue 410 on github:
    https://github.com/hmmlearn/hmmlearn/issues/410
    """
    sequence_data = EXAMPLE_SEQUENCES_ISSUE_410_PRUNED

    scores = []
    for p in make_permutations(sequence_data):
        sequences = sequence_data[p]
        X = np.concatenate(sequences)
        lengths = [len(seq) for seq in sequences]
        if hmm_type == "em":
            model = setup_em(covariance_type, implementation, init_params, verbose)
            # Choice of rtol value is ad-hoc, no theoretical motivation.
            rtol = 5e-3
        else:
            model = setup_vi(covariance_type, implementation, init_params, verbose, lengths)
            # In General, the EM solution can use a smaller rtol, while the VI
            # solution needs a bit larger
            rtol = 5e-2

        model.fit(X, lengths)
        assert model.monitor_.converged
        scores.append(model.score(X, lengths))

    assert_allclose(scores, np.mean(scores), rtol=rtol)
