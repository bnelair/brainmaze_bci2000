
import pytest
import os
import tempfile

from mef_tools import MefReader

from brainmaze_bci2000.bids import bci2000_to_mefd

from .conftest import test_file_bci2000_stim, test_file_bci2000_accl

def test_bci2000_to_mefd(test_file_bci2000_stim):
    fid_bci2000, tmpdir = test_file_bci2000_stim

    if not os.path.exists(fid_bci2000):
        raise FileNotFoundError(f"Test file {fid_bci2000} does not exist.")

    bci2000 = bci2000_to_mefd(fid_bci2000)

    path_mefd = fid_bci2000.replace(".dat", ".mefd")
    assert os.path.exists(path_mefd)
    assert os.path.isfile(os.path.join(path_mefd, 'data_description.json'))

    rdr = MefReader(path_mefd)

    assert rdr.get_property('fsamp')[0] == 1000, "Sample rate should be 1000 Hz"
    assert 'state_ImplantStimulation' in rdr.channels, "ImplantStimulation channel should be present"
    assert 'state_StimulusCode' in rdr.channels, "StimulusCode channel should be present"
    assert 'state_PhaseInSequence' in rdr.channels, "PhaseInSequence channel should be present"
    assert 'state_ImplantLostSample' in rdr.channels, "ImplantLostSample channel should be present"



def test_bci2000_acc_to_mefd(test_file_bci2000_accl):
    fid_bci2000, tmpdir = test_file_bci2000_accl

    if not os.path.exists(fid_bci2000):
        raise FileNotFoundError(f"Test file {fid_bci2000} does not exist.")

    bci2000 = bci2000_to_mefd(fid_bci2000)

    path_mefd = fid_bci2000.replace(".dat", ".mefd")
    assert os.path.exists(path_mefd)
    assert os.path.isfile(os.path.join(path_mefd, 'data_description.json'))

    rdr = MefReader(path_mefd)

    assert rdr.get_property('fsamp')[0] == 1000, "Sample rate should be 1000 Hz"
    assert 'state_ImplantStimulation' in rdr.channels, "ImplantStimulation channel should be present"
    assert 'state_StimulusCode' in rdr.channels, "StimulusCode channel should be present"
    assert 'state_PhaseInSequence' in rdr.channels, "PhaseInSequence channel should be present"
    assert 'state_ImplantLostSample' in rdr.channels, "ImplantLostSample channel should be present"

    for ach in ['accl_MTw1X', 'accl_MTw1Y', 'accl_MTw1Z']:
        assert ach in rdr.channels, f"Accelerometer channel {ach} should be present"


