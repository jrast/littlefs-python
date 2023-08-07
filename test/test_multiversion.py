import pytest
from littlefs import LittleFS, FileHandle

@pytest.fixture(scope='function')
def fs20():
    fs = LittleFS(block_size=128, block_count=64, disk_version=0x00020000)
    fs.mkdir('mydir')

    with fs.open('test.txt', 'w') as f:
        f.write('1234567890')

    yield fs

@pytest.fixture(scope='function')
def fs21():
    fs = LittleFS(block_size=128, block_count=64, disk_version=0x00020001)
    fs.mkdir('mydir')

    with fs.open('test.txt', 'w') as f:
        f.write('1234567890')

    yield fs

def test_lfs20(fs20):
    assert fs20.fs_stat().disk_version == 0x00020000

def test_lfs21(fs21):
    assert fs21.fs_stat().disk_version == 0x00020001
