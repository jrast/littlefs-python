import pytest
from littlefs import lfs


@pytest.fixture(scope="function")
def testfs(mounted_fs):
    lfs.mkdir(mounted_fs, "testdir")
    yield mounted_fs


def test_mkdir(mounted_fs):
    assert lfs.mkdir(mounted_fs, "directory") == 0


def test_dir_open(testfs):
    dh = lfs.dir_open(testfs, "testdir")
    assert dh != None


def test_dir_close(testfs):
    dh = lfs.dir_open(testfs, "testdir")
    lfs.dir_close(testfs, dh)


def test_dir_read(testfs):
    dh = lfs.dir_open(testfs, "/")
    info = lfs.dir_read(testfs, dh)
    assert info.name == "."

    info = lfs.dir_read(testfs, dh)
    assert info.name == ".."

    info = lfs.dir_read(testfs, dh)
    assert info.name == "testdir"


def test_dir_read_overflow(testfs):
    dh = lfs.dir_open(testfs, "/")

    # There are three directories: ., .., testdir
    for _ in range(3):
        info = lfs.dir_read(testfs, dh)
        assert info is not None

    # If we read one more, we should get None
    info = lfs.dir_read(testfs, dh)
    assert info is None


def test_dir_rewind(testfs):
    dirs = [".", "..", "testdir"]
    dh = lfs.dir_open(testfs, "/")

    for name in dirs:
        info = lfs.dir_read(testfs, dh)
        assert info.name == name

    lfs.dir_rewind(testfs, dh)

    for name in dirs:
        info = lfs.dir_read(testfs, dh)
        assert info.name == name
