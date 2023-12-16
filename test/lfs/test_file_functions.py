import pytest
from littlefs import lfs
from littlefs.errors import LittleFSError


def test_file_open(mounted_fs):
    fh = lfs.file_open(mounted_fs, "test.txt", "w")


def test_file_open_wb(mounted_fs):
    fh = lfs.file_open(mounted_fs, "test.txt", "wb")


def test_file_open_a(mounted_fs):
    fh = lfs.file_open(mounted_fs, "test.txt", "w")
    lfs.file_write(mounted_fs, fh, b"0123456789")
    lfs.file_close(mounted_fs, fh)

    fh = lfs.file_open(mounted_fs, "test.txt", "a")
    lfs.file_write(mounted_fs, fh, b"0123456789")
    lfs.file_close(mounted_fs, fh)

    info = lfs.stat(mounted_fs, "test.txt")
    assert info.size == 20


def test_file_open_flags(mounted_fs):
    flags = lfs.LFSFileFlag.wronly | lfs.LFSFileFlag.creat
    fh = lfs.file_open(mounted_fs, "test.txt", flags)


def test_file_open_exist(mounted_fs):
    fh = lfs.file_open(mounted_fs, "test.txt", "wb")
    lfs.file_write(mounted_fs, fh, b"0123456789")
    lfs.file_close(mounted_fs, fh)

    with pytest.raises(LittleFSError) as excinfo:
        fh = lfs.file_open(mounted_fs, "test.txt", "x")

    assert excinfo.value.code == LittleFSError.Error.LFS_ERR_EXIST


def test_file_open_noent(mounted_fs):
    with pytest.raises(LittleFSError) as excinfo:
        flags = lfs.LFSFileFlag.rdonly
        fh = lfs.file_open(mounted_fs, "test.txt", flags)

    assert excinfo.value.code == LittleFSError.Error.LFS_ERR_NOENT


def test_file_open_isdir(mounted_fs):
    lfs.mkdir(mounted_fs, "testdir")

    with pytest.raises(LittleFSError) as excinfo:
        fh = lfs.file_open(mounted_fs, "testdir", "r")

    assert excinfo.value.code == LittleFSError.Error.LFS_ERR_ISDIR


def test_file_close(mounted_fs):
    fh = lfs.file_open(mounted_fs, "test.txt", "w")
    lfs.file_close(mounted_fs, fh)


def test_file_sync(mounted_fs):
    fh = lfs.file_open(mounted_fs, "test.txt", "w")
    lfs.file_sync(mounted_fs, fh)


def test_file_read(mounted_fs):
    fh = lfs.file_open(mounted_fs, "test.txt", "w")
    lfs.file_write(mounted_fs, fh, b"0123456789")
    lfs.file_close(mounted_fs, fh)

    fh = lfs.file_open(mounted_fs, "test.txt", "r")
    data = lfs.file_read(mounted_fs, fh, 10)
    assert data == b"0123456789"


def test_file_read_rb(mounted_fs):
    fh = lfs.file_open(mounted_fs, "test.txt", "w")
    lfs.file_write(mounted_fs, fh, b"0123456789")
    lfs.file_close(mounted_fs, fh)

    fh = lfs.file_open(mounted_fs, "test.txt", "rb")
    data = lfs.file_read(mounted_fs, fh, 10)
    assert data == b"0123456789"


def test_file_write(mounted_fs):
    fh = lfs.file_open(mounted_fs, "test.txt", "w")
    lfs.file_write(mounted_fs, fh, b"0123456789")


def test_file_seek(mounted_fs):
    fh = lfs.file_open(mounted_fs, "test.txt", "w")
    # Seek whenece:
    #   0: Absolute
    #   1: Relative to Current Position
    #   2: Relative to EOF
    new_pos = lfs.file_seek(mounted_fs, fh, 10, 0)
    assert new_pos == 10


def test_file_truncate(mounted_fs):
    fh = lfs.file_open(mounted_fs, "test.txt", "w")
    assert lfs.file_truncate(mounted_fs, fh, 10) == 0


def test_file_tell(mounted_fs):
    fh = lfs.file_open(mounted_fs, "test.txt", "w")
    assert lfs.file_tell(mounted_fs, fh) == 0


def test_file_rewind(mounted_fs):
    fh = lfs.file_open(mounted_fs, "test.txt", "w")
    assert lfs.file_rewind(mounted_fs, fh) == 0


def test_file_size(mounted_fs):
    fh = lfs.file_open(mounted_fs, "test.txt", "w")
    assert lfs.file_size(mounted_fs, fh) == 0
