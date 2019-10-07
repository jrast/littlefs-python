import pytest
from littlefs import lfs
from littlefs.errors import LittleFSError


def test_mount_unformatted(fs, cfg):
    """Mounting a unformated filesystem should lead to an error -84
    which means the filesystem is corrupted
    """
    with pytest.raises(LittleFSError) as excinfo:
        lfs.mount(fs, cfg)

    assert excinfo.value.code == -84


def test_mount_formatted(fs, cfg):
    """Mounting a formated filesystem should work as expected"""
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
    stat = lfs.stat(mounted_fs, '/')
    assert stat.type == 2, 'Expected a directory type'
    assert stat.name == '/'


def test_stat_file(mounted_fs):
    fh = lfs.file_open(mounted_fs, 'test.txt', 'w')
    lfs.file_write(mounted_fs, fh, b'0123456789')
    lfs.file_close(mounted_fs, fh)

    stat = lfs.stat(mounted_fs, 'test.txt')

    assert stat.size == 10
    assert stat.type == 1
    assert stat.name == 'test.txt'
