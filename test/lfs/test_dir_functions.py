import pytest
from littlefs import lfs


@pytest.fixture(scope='function')
def testfs(mounted_fs):
    lfs.mkdir(mounted_fs, 'testdir')
    yield mounted_fs


def test_mkdir(mounted_fs):
    assert lfs.mkdir(mounted_fs, 'directory') == 0


def test_dir_open(testfs):
    dh = lfs.dir_open(testfs, 'testdir')


def test_dir_close(testfs):
    dh = lfs.dir_open(testfs, 'testdir')
    lfs.dir_close(testfs, dh)


def test_dir_read(testfs):
    dh = lfs.dir_open(testfs, '')
    info = lfs.dir_read(testfs, dh)
    assert info.name == '.'

    info = lfs.dir_read(testfs, dh)
    assert info.name == '..'

    info = lfs.dir_read(testfs, dh)
    assert info.name == 'testdir'


def test_dir_rewind(testfs):
    dh = lfs.dir_open(testfs, '')
    info = lfs.dir_read(testfs, dh)
    assert info.name == '.'

    lfs.dir_rewind(testfs, dh)

    info = lfs.dir_read(testfs, dh)
    assert info.name == '.'
