
import os
import shutil
import tempfile
import time

import pytest


@pytest.fixture
def test_file_bci2000_stim():
    path_bci2000 = os.path.abspath(__file__)
    path_bci2000 = path_bci2000.split(os.sep)[:-1] + ['files', 'test_stim_file.dat'] # Navigate to the parent directory of the test file
    path_bci2000 = os.sep.join(path_bci2000)

    tmpdir = tempfile.mkdtemp()

    tmp_bci2000 = os.path.join(tmpdir, 'test_stim_file.dat')
    shutil.copyfile(path_bci2000, tmp_bci2000)

    orig_file_size = os.path.getsize(path_bci2000)
    new_file_size = 0
    while not os.path.exists(tmp_bci2000) or new_file_size < orig_file_size:
        time.sleep(0.1)
        if os.path.exists(tmp_bci2000):
            new_file_size = os.path.getsize(tmp_bci2000)


    yield tmp_bci2000, tmpdir

    shutil.rmtree(tmpdir)

@pytest.fixture
def test_file_bci2000_accl():
    path_bci2000 = os.path.abspath(__file__)
    path_bci2000 = path_bci2000.split(os.sep)[:-1] + ['files', 'test_accl_file.dat'] # Navigate to the parent directory of the test file
    path_bci2000 = os.sep.join(path_bci2000)

    tmpdir = tempfile.mkdtemp()

    tmp_bci2000 = os.path.join(tmpdir, 'test_accl_file.dat')
    shutil.copyfile(path_bci2000, tmp_bci2000)

    orig_file_size = os.path.getsize(path_bci2000)
    new_file_size = 0
    while not os.path.exists(tmp_bci2000) or new_file_size < orig_file_size:
        time.sleep(0.1)
        if os.path.exists(tmp_bci2000):
            new_file_size = os.path.getsize(tmp_bci2000)


    yield tmp_bci2000, tmpdir

    shutil.rmtree(tmpdir)



