import pytest
from littlefs import lfs


@pytest.fixture(scope="function")
def fs():
    """Littlefs filesystem fixture"""
    fs = lfs.LFSFilesystem()
    yield fs


@pytest.fixture(scope="function")
def cfg():
    """Littlefs configuration fixture"""
    cfg = lfs.LFSConfig(block_size=128, block_count=4)
    yield cfg


@pytest.fixture(scope="function")
def formated_fs(fs, cfg):
    """fixutre for a formatted filesystem"""
    lfs.format(fs, cfg)
    yield fs


@pytest.fixture(scope="function")
def mounted_fs(formated_fs, cfg):
    """fixture for a formatted and mounted filesystem"""
    lfs.mount(formated_fs, cfg)
    yield formated_fs
