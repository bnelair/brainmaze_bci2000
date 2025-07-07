
import os
import shutil
import tempfile
import time

import pytest

@pytest.fixture
def tmp_dir():
    tmpdir = tempfile.mkdtemp()

    yield tmpdir

    shutil.rmtree(tmpdir)
    while os.path.exists(tmpdir):
        time.sleep(0.1)


@pytest.fixture
def test_file_bci2000_stim(tmp_dir):
    path_bci2000 = os.path.abspath(__file__)
    path_bci2000 = path_bci2000.split(os.sep)[:-1] + ['files', 'test_stim_file.dat'] # Navigate to the parent directory of the test file
    path_bci2000 = os.sep.join(path_bci2000)

    tmp_bci2000 = os.path.join(tmp_dir, 'test_stim_file.dat')
    shutil.copyfile(path_bci2000, tmp_bci2000)

    orig_file_size = os.path.getsize(path_bci2000)
    new_file_size = 0
    while not os.path.exists(tmp_bci2000) or new_file_size < orig_file_size:
        time.sleep(0.1)
        if os.path.exists(tmp_bci2000):
            new_file_size = os.path.getsize(tmp_bci2000)

    yield tmp_bci2000, tmp_dir

@pytest.fixture
def test_file_bci2000_accl(tmp_dir):
    path_bci2000 = os.path.abspath(__file__)
    path_bci2000 = path_bci2000.split(os.sep)[:-1] + ['files', 'test_accl_file.dat'] # Navigate to the parent directory of the test file
    path_bci2000 = os.sep.join(path_bci2000)

    tmp_bci2000 = os.path.join(tmp_dir, 'test_accl_file.dat')
    shutil.copyfile(path_bci2000, tmp_bci2000)

    orig_file_size = os.path.getsize(path_bci2000)
    new_file_size = 0
    while not os.path.exists(tmp_bci2000) or new_file_size < orig_file_size:
        time.sleep(0.1)
        if os.path.exists(tmp_bci2000):
            new_file_size = os.path.getsize(tmp_bci2000)

    yield tmp_bci2000, tmp_dir



