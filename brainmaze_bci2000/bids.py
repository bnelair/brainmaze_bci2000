
import json
import os

import pandas as pd
import numpy as np

from tqdm import tqdm
from datetime import datetime

from brainmaze_utils.files import get_files

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

    for chname, x in tqdm(list(rdr_bci.data_eeg.items()), desc='Writing channels'):
        Wrt.data_units = 'uV'
        Wrt.write_data(x, chname, rdr_bci.start_time * 1e6, rdr_bci.fs, precision=3)

    accl_data = rdr_bci.data_accelerometry
    if accl_data is not None:
        for chname, x in tqdm(list(accl_data.items()), desc='Writing accelerometer channels'):
            Wrt.data_units = 'g'
            Wrt.write_data(x, f'accl_{chname}', rdr_bci.start_time * 1e6, rdr_bci.fs, precision=3)


    for state in tqdm(write_states, desc='Writing states'):
        if state not in rdr_bci.states:
            continue

        Wrt.data_units = '-'
        Wrt.write_data(rdr_bci.get_state(state), f"state_{state}", rdr_bci.start_time * 1e6, rdr_bci.fs, precision=0)

    stim_annotations = []
    if 'StimulusCode' in rdr_bci.states:
        stimulus_code = rdr_bci.get_state('StimulusCode')

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
                            'start_time': idx / rdr_bci.fs,
                        }
                    )
                    stim_annotations[-1].update(rdr_bci.stimulation)

                if end_flag:
                    stim_annotations[-1]['end_time'] = idx / rdr_bci.fs

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


def capitalize_words(input_string):
    """
    Capitalizes the first letter of each word in the input string.
    Words are defined as being separated by spaces, hyphens, or underscores.
    Removes spaces, hyphens, and underscores in the process.

    Args:
        input_string (str): The input string to process.

    Returns:
        str: The processed string with words capitalized and separators removed.
    """
    return ''.join(word.capitalize() for word in input_string.replace('-', ' ').replace('_', ' ').split()).capitalize()


def convert_sourcedata_bci2000_to_bids(
    path_source: str,
    path_bids: str,
):
    """
    The structure has to contain subject/session/task/acquisition/run directories.
    """

    dat_files = get_files(path_source, 'dat')

    df_dirs = []

    for path_fid in tqdm(dat_files, desc='Identifying BIDS sessions'):
        filename = os.path.basename(path_fid)
        if filename.startswith('.'):
            continue

        subdirs = os.path.dirname(path_fid.replace(path_source + '/', '')).split(os.sep)

        sub = 'sub-' + subdirs[0].replace('sub-', '')
        ses = 'ses-' + capitalize_words(subdirs[1].replace('ses-', ''))

        task = 'task-rec'
        acq = 'acq-rec'

        if len(subdirs) > 2:
            task = 'task-' + capitalize_words(subdirs[2].replace('task-', ''))

        if len(subdirs) > 3:
            acq = 'acq-' + capitalize_words(subdirs[3].replace('acq-', ''))

        print(subdirs.__len__(), sub, ses, task, acq)

        entry =  {
                'sub': sub,
                'ses': ses,
                'task': task,
                'acq': acq,
                'path_orig': os.path.dirname(path_fid),
                'path_bids': os.path.join(path_bids, sub, ses, 'ieeg'),
            }

        if not entry in df_dirs:
            df_dirs.append(entry)

    df_dirs = pd.DataFrame(df_dirs)

    df_files = []
    for idx, row in tqdm(df_dirs.iterrows(),  total=df_dirs.shape[0], desc='Identifying files for conversion'):
        path_bids_ieeg = row['path_bids']
        path_orig = row['path_orig']

        files = [f for f in get_files(path_orig, '.dat') if not '.-' in f]
        files.sort()

        for idx, fid in enumerate(files):
            filename = os.path.basename(fid)
            if filename.startswith('.'):
                continue

            run = f"run-{idx+1}"  # Ensure run number is two digits

            fid_bids = f"{row['sub']}_{row['ses']}"

            for vol in ['task', 'acq']:
                if row[vol]:
                    fid_bids += f"_{row[vol]}"

            fid_bids += f"_{run}_ieeg.mefd"


            entry = {
                'sub': row['sub'],
                'ses': row['ses'],
                'task': row['task'],
                'acq': row['acq'],
                'run': run,
                'path_source': fid,
                'path_destination': os.path.join(path_bids_ieeg, fid_bids),
            }
            if os.path.exists(entry['path_destination']):
                continue
            df_files.append(entry)

    df_files = pd.DataFrame(df_files)

    for idx, row in tqdm(df_files.iterrows(), total=df_files.shape[0], desc='Converting files'):
        path_src = row['path_source']
        path_dst = row['path_destination']

        print('\n Processing ', path_src, '->', path_dst)
        # if idx == 15:
        #     break

        path_dst_dir = os.path.dirname(path_dst)

        os.makedirs(os.path.dirname(path_dst_dir), exist_ok=True)

        bci2000_to_mefd(path_src, path_dst)

        if not os.path.exists(path_dst):
            raise FileNotFoundError(f"Conversion failed: {path_src} to {path_dst} does not exist after conversion.")


    files_mefd = get_files(path_bids, '.mefd')
    files_mefd = [f for f in files_mefd if not '.-' in f]

    for fid in files_mefd:
        path_ddescr = os.path.join(fid, 'data_description.json')

        if not os.path.exists(path_ddescr):
            continue

        data_description = json.load(open(path_ddescr))

        path_json_sidecar = fid.replace('.mefd', '.json')

        sidecar = {
            'iEEGReference': str(data_description['reference_channels']),
            'SamplingFrequency': data_description['sampling_rate'],
            'PowerLineFrequency': 60,
            'SoftwareFilters': 'n/a',
            'AmplificationFactor': data_description['amplification_factor'],
            'RecordingDurationSeconds': data_description['duration_seconds'],
        }

        with open(path_json_sidecar, 'w') as fid_out:
            json.dump(sidecar, fid_out, indent=4)

        df_events = []
        for ev in data_description.get('stimulus_annotations', []):
            df_events += [
                {
                    'onset': ev['start_time'],
                    'duration': ev.get('end_time', 0) - ev['start_time'],
                    'stim_frequency': ev.get('frequency_Hz', 'n/a'),
                    'stim_amplitude': ev.get('amplitude_mA', 'n/a'),
                    'pulse_width': ev.get('pulsewidth_us', 'n/a'),
                    'stim_anodes': str(ev.get('stim_anode', [])),
                    'stim_cathodes': str(ev.get('stim_cathode', [])),
                }
            ]
        df_events = pd.DataFrame(df_events)

        path_events = fid.replace('_ieeg.mefd', '_events.tsv')
        if df_events.__len__() > 0:
            df_events.to_csv(path_events, sep='\t', index=False)

            path_events_json = fid.replace('_ieeg.mefd', '_events.json')
            metadata_events = {
                'onset': 'Time of the event onset in seconds.',
                'duration': 'Duration of the event in seconds.',
                'stim_frequency': 'Frequency of the stimulation in Hz.',
                'stim_amplitude': 'Amplitude of the stimulation in mA.',
                'pulse_width': 'Width of the stimulation pulse in microseconds.',
                'stim_anodes': 'List of anode channels used for stimulation.',
                'stim_cathodes': 'List of cathode channels used for stimulation.',
            }

            with open(path_events_json, 'w') as outfile:
                json.dump(metadata_events, outfile, indent=4)

        os.remove(path_ddescr)




    #
    # for idx, row in df_dirs.iterrows():
    #
    #


        # if files_mefd.__len__() > 0:
        #     break

        # df_scans = []
        # for fid in files_mefd:

        #     scans_field = {
        #         'filename': os.path.basename(fid),
        #         'acq_time': 'n/a',
        #         'amplification_factor': data_description['amplification_factor'],
        #         'sampling_rate': data_description['sampling_rate'],
        #         'reference_channels'
        #     }
        #
        #     df_scans.append(scans_field)


