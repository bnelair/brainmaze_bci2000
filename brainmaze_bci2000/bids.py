
import json
import os

import numpy as np

from tqdm import tqdm
from datetime import datetime
from mef_tools import MefWriter
from BCI2kReader import BCI2kReader as b2k

from brainmaze_bci2000.bci2000 import BCI2000Reader

def bci2000_to_mefd(path_bci: str, path_mefd: str =None):
    """
    Converts a BCI2000 `.dat` file to a MEF (Multiscale Electrophysiology Format) directory.

    This function reads data from a BCI2000 `.dat` file, processes it, and writes the data
    into a MEF directory format. The output includes EEG data, accelerometer data (if available),
    state variables, and metadata such as sampling rate, amplification factor, and stimulus annotations.

    Args:
        path_bci (str): Path to the input BCI2000 `.dat` file. Must be a valid file path.
        path_mefd (str, optional): Path to the output MEF directory. If not provided,
            the output path will be derived from the input file by replacing the `.dat`
            extension with `.mefd`.

    Raises:
        ValueError: If the input file does not have a `.dat` extension.
        TypeError: If the input path is not a string.
        FileNotFoundError: If the input file does not exist or is inaccessible.

    Returns:
        None: The function writes the output to the specified MEF directory and does not return any value.
    """


    write_states = [
        'ImplantLostSample',
        'ImplantStimulation',
        'PhaseInSequence',
        'StimulusCode'
    ]


    if not path_bci.endswith('.dat'):
        raise ValueError("The provided path must point to a '.dat' file.")

    if not isinstance(path_bci, str):
        raise TypeError("The provided path must be a string.")

    if not os.path.isfile(path_bci):
        raise FileNotFoundError(f"The file {path_bci} does not exist or is not accessible.")

    if path_mefd is None:
        path_mefd = path_bci.replace('.dat', '.mefd')


    rdr_bci = BCI2000Reader(path_bci)

    rdr_bci.stimulation

    Wrt = MefWriter(
            path_mefd,
            overwrite=True,
        )
    Wrt.mef_block_len = int(rdr_bci.fs * 10)
    Wrt.max_nans_written = 0

    stimulus_code = rdr_bci.get_state('StimulusCode')

    stim_annotations = []
    if np.nansum(stimulus_code) > 0:
        for idx, code in enumerate(stimulus_code):
            if idx == 0 and code == 0:
                continue

            if idx == 0 and code == 1:
                continue

            start_flag = stimulus_code[idx-1] == 0 and stimulus_code[idx] == 1
            end_flag = stimulus_code[idx-1] == 1 and stimulus_code[idx] == 0

            if start_flag:
                stim_annotations.append(
                    {
                        'start_idx': idx / rdr_bci.fs,
                    }
                )
                stim_annotations[-1].update(rdr_bci.stimulation)

            if end_flag:
                stim_annotations[-1]['end_idx'] = idx / rdr_bci.fs


    for chname, x in tqdm(list(rdr_bci.data_eeg.items()), desc='Writing channels'):
        Wrt.data_units = 'uV'
        Wrt.write_data(x, chname, rdr_bci.start_time * 1e6, rdr_bci.fs, precision=3)

    accl_data = rdr_bci.data_accelerometry
    if accl_data is not None:
        for chname, x in tqdm(list(accl_data.items()), desc='Writing accelerometer channels'):
            Wrt.data_units = 'g'
            Wrt.write_data(x, f'accl_{chname}', rdr_bci.start_time * 1e6, rdr_bci.fs, precision=3)

    for state in tqdm(write_states, desc='Writing states'):
        Wrt.data_units = '-'
        Wrt.write_data(rdr_bci.get_state(state), f"state_{state}", rdr_bci.start_time * 1e6, rdr_bci.fs, precision=0)

    Wrt.session.close()

    path_info = os.path.join(path_mefd, 'data_description.json')

    meta_info = {
        'amplification_factor': rdr_bci.amplification_factor,
        'sampling_rate': rdr_bci.fs,
        'start_time': rdr_bci.start_time,
        'stimulus_annotations': stim_annotations,
        'reference_channels': rdr_bci.reference_channels,
        'duration_seconds': rdr_bci.recording_duration_seconds,
    }

    with open(path_info, 'w') as f:
        json.dump(meta_info, f, indent=4)







