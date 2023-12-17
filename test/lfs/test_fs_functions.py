import pytest
from littlefs import lfs
from littlefs.errors import LittleFSError


def test_mount_unformatted(fs, cfg):
    """Mounting a unformatted filesystem should lead to an error -84
    which means the filesystem is corrupted
    """
    with pytest.raises(LittleFSError) as excinfo:
        lfs.mount(fs, cfg)

    assert excinfo.value.code == -84


def test_mount_formatted(fs, cfg):
    """Mounting a formatted filesystem should work as expected"""
    lfs.format(fs, cfg)
    assert lfs.mount(fs, cfg) == 0


def test_format(fs, cfg):
    """Test if filesystem formatting works as expected"""
    assert lfs.format(fs, cfg) == 0


def test_unmount(mounted_fs):
    """Test if the filesystem can be unmounted"""
    assert lfs.unmount(mounted_fs) == 0


def test_stat_root_directory(mounted_fs):
    """Test if stat works"""
    stat = lfs.stat(mounted_fs, "/")
    assert stat.type == 2, "Expected a directory type"
    assert stat.name == "/"


def test_stat_file(mounted_fs):
    fh = lfs.file_open(mounted_fs, "test.txt", "w")
    lfs.file_write(mounted_fs, fh, b"0123456789")
    lfs.file_close(mounted_fs, fh)

    stat = lfs.stat(mounted_fs, "test.txt")

    assert stat.size == 10
    assert stat.type == 1
    assert stat.name == "test.txt"

    # Double checking that these constant got passed through.
    assert stat.TYPE_REG == 0x001
    assert stat.TYPE_DIR == 0x002


def test_fs_stat(mounted_fs):
    """Test if fs stat works"""
    stat = lfs.fs_stat(mounted_fs)
    # The following values are defaults in littlefs.
    assert stat.disk_version == 0x00020001
    assert stat.name_max == 255
    assert stat.file_max == 2147483647
    assert stat.attr_max == 1022
