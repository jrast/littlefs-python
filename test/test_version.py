import littlefs

def test_version():
    assert littlefs.__LFS_VERSION__ == (2, 1)
    assert littlefs.__LFS_DISK_VERSION__ == (2, 0)
    