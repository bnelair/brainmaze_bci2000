import os

from datetime import datetime

from BCI2kReader import BCI2kReader as b2k

class BCI2000Reader:
    """
    A class to read and process BCI2000 `.dat` files.

    This class provides methods and properties to extract EEG data, accelerometer data,
    state variables, and metadata from BCI2000 files. It validates the input file,
    parses its contents, and exposes the data in a structured format.

    Attributes:
        _accl_channels (list): List of accelerometer channel names.
        _amplification_factor_values (dict): Mapping of amplification factor codes to their descriptions.

    Methods:
        __init__(path_bci_file):
            Initializes the reader, validates the input file, and loads its data.

        fs:
            Returns the sampling rate of the recording.

        reference_channels:
            Returns the list of reference channels used in the recording.

        start_time:
            Returns the start time of the recording as a UNIX timestamp.

        stimulation:
            Returns stimulation parameters if stimulation is enabled, otherwise an empty dictionary.

        data_accelerometry:
            Returns accelerometer data if available, otherwise `None`.

        channels:
            Returns the list of channel names in the recording.

        data_eeg:
            Returns EEG data as a dictionary with channel names as keys.

        amplification_factor:
            Returns the amplification factor used in the recording.

        recording_duration_seconds:
            Returns the duration of the recording in seconds.

        states:
            Returns the list of state variable names in the recording.

        get_state(state_name):
            Returns the data for a specific state variable.

    Raises:
        ValueError: If the input file is not a `.dat` file or a requested state does not exist.
        TypeError: If the input file path is not a string.
        FileNotFoundError: If the input file does not exist or is inaccessible.
        RuntimeError: If an error occurs while reading the BCI2000 file.
    """

    _accl_channels = [
        'MTw1X',
        'MTw1Y',
        'MTw1Z',
    ]

    _amplification_factor_values = {
        0: '57.5dB',
        1: '51.5dB',
        2: '45.5dB',
        3: '39.5dB',
    }

    def __init__(self, path_bci_file):

        if not path_bci_file.endswith('.dat'):
            raise ValueError("The provided path must point to a '.dat' file.")

        if not isinstance(path_bci_file, str):
            raise TypeError("The provided path must be a string.")

        if not os.path.isfile(path_bci_file):
            raise FileNotFoundError(f"The file {path_bci_file} does not exist or is not accessible.")


        self.path_bci_file = path_bci_file

        try:
            with b2k.BCI2kReader(path_bci_file) as b2kRdr:
                self._data, self._states = b2kRdr.readall()
                self._params = b2kRdr.parameters
                self._fs = b2kRdr.samplingrate

        except Exception as e:
            raise RuntimeError(f"An error occurred while reading the BCI2000 file: {e}")


    @property
    def fs(self):
        return self._fs

    @property
    def reference_channels(self):
        return [
            self.channels[int(ch)-1] for ch in self._params['ReferenceCh']
        ]

    @property
    def start_time(self):
        storage_timestamp = datetime.strptime(self._params['StorageTime'], '%Y-%m-%dT%H:%M:%S').timestamp()
        return datetime.fromtimestamp(storage_timestamp).timestamp()

    @property
    def stimulation(self):
        stimulation_enabled = bool(self._params['EnableStimulation'])
        if not stimulation_enabled:
            return {}

        stim_amplitude_mA = float(self._params['StimulationPulses'][1][0]) / 1000
        stim_pulsewidth = float(self._params['StimulationPulses'][2][0])
        stim_frequency = 5*float(self._params['StimulationPulses'][1][0]) + 2*float(self._params['StimulationPulses'][3][0]) + float(self._params['StimulationPulses'][4][0])
        stim_frequency = 1 / (stim_frequency / 1000)
        # print("\nanodes", self._params['StimulationTriggers'][2], 'cathodes', self._params['StimulationTriggers'][3])

        anodes_list = self._params['StimulationTriggers'][2][0]
        cathodes_list = self._params['StimulationTriggers'][3][0]

        if anodes_list == '{':
            anodes_list = self._params['StimulationTriggers'][4][0]
            cathodes_list = self._params['StimulationTriggers'][5][0]

        anodes_list = [int(i)-1 for i in anodes_list.split(',')]
        cathodes_list = [int(i)-1 for i in cathodes_list.split(',')]

        anodes = [self.channels[i] for i in anodes_list]
        cathodes = [self.channels[i] for i in cathodes_list]

        return {
            'amplitude_mA': stim_amplitude_mA,
            'frequency_Hz': stim_frequency,
            'pulsewidth_us': stim_pulsewidth,
            'stim_anode': anodes,
            'stim_cathode': cathodes,
        }

    @property
    def data_accelerometry(self):
        states = self._states.keys()
        has_accelerometer = all(ch in states for ch in self._accl_channels)
        if not has_accelerometer:
            None

        data = {}
        for ch in self._accl_channels:
            if ch in self._states:
                data[ch] = self._states[ch].squeeze()

        return data

    @property
    def channels(self):
        return self._params['ChannelNames']

    @property
    def data_eeg(self):
        eeg_data = {}
        for idx, ch in enumerate(self.channels):
            eeg_data[ch] = self._data[idx].squeeze()
        return eeg_data

    @property
    def amplification_factor(self):
        if not 'AmplificationFactor' in self._params:
            return 'n/a'

        return self._amplification_factor_values[self._params['AmplificationFactor']]

    @property
    def recording_duration_seconds(self):
        return self._data.shape[1] / self.fs

    @property
    def states(self):
        return list(self._states.keys())

    def get_state(self, state_name):
        if state_name not in self._states:
            raise ValueError(f"State '{state_name}' does not exist in the BCI2000 data.")
        return self._states[state_name].squeeze()


