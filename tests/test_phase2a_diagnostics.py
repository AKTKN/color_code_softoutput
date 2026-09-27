from pathlib import Path
import sys
import numpy as np
import pytest
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
from phase2a_diagnostics import wilson,retained_curve,binned_ler,validate_pairing,paired_detector_shots
from color_code_stim import ColorCode
from color_code_stim.noise_model import NoiseModel


def test_known_counts_and_ties():
    scores = np.array([4,3,2,1])
    failures = np.array([False,False,True,True])
    curve = retained_curve(scores,failures,[.5,1])
    assert [(x['accepted'],x['failures'],x['ler']) for x in curve] == [(2,0,0),(4,2,.5)]
    assert wilson(0,4)[0] == 0
    assert wilson(2,4)[0] == pytest.approx(1-wilson(2,4)[1])
    tied = retained_curve(np.ones(4),failures,[.5])
    assert tied[0]['failures'] == 0
    assert sum(x['failures'] for x in binned_ler(scores,failures,2)) == 2
    assert sum(x['shots'] for x in binned_ler(scores,failures,2)) == 4


@pytest.mark.parametrize('d',[3,5,7])
def test_pairing_uses_identical_measurement_records(d):
    ordinary, comparative = [ColorCode(d=d,rounds=1,noise_model=NoiseModel(bitflip=.05),
                                     comparative_decoding=c) for c in (False,True)]
    validate_pairing(ordinary.circuit,comparative.circuit)
    # Sample the physical measurements once and convert that same array twice.
    records = ordinary.circuit.compile_sampler(seed=3197).sample(64)
    dets,obs = ordinary.circuit.compile_m2d_converter().convert(measurements=records,separate_observables=True)
    cmpdets,cmpobs = comparative.circuit.compile_m2d_converter().convert(measurements=records,separate_observables=True)
    np.testing.assert_array_equal(obs,cmpobs)
    np.testing.assert_array_equal(paired_detector_shots(dets,obs),cmpdets)
    pred,extra = comparative.decode(cmpdets,full_output=True)
    # Forced-class decoding must not use the measured actual observable as input.
    cmpdets[:,-1] ^= True
    pred2,extra2 = comparative.decode(cmpdets,full_output=True)
    np.testing.assert_array_equal(pred,pred2)
    np.testing.assert_array_equal(extra['logical_gaps'],extra2['logical_gaps'])


def test_wilson_extreme_counts_have_exact_endpoints():
    for n in range(1,100):
        assert wilson(0,n)[0] == 0.
        assert wilson(n,n)[1] == 1.
