from littlefs import LittleFS, LittleFSError


def test_fs_grow_basic():
    fs = LittleFS(block_count=32)
    fs.fs_grow(40)
    assert fs.block_count == 40
