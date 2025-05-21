import littlefs


def test_version():
    """Test if the versions of littlefs can be imported"""
    assert littlefs.__LFS_VERSION__ == (2, 11)
    assert littlefs.__LFS_DISK_VERSION__ == (2, 1)
