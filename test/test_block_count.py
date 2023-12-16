import pytest
from littlefs import LittleFS, LittleFSError
from littlefs.context import UserContext


def test_block_count_autodetect():
    block_size = 256
    block_count = 57
    context = UserContext(block_size * block_count)

    # Create the filesystem with 57 blocks
    fs = LittleFS(
        context=context,
        block_size=block_size,
        block_count=block_count,
    )
    assert fs.block_count == 57

    fs = LittleFS(
        context=context,
        block_size=block_size,
        block_count=0,  # infer from superblock
    )

    assert fs.block_count == 57


def test_block_count_autodetect_format_fail():
    with pytest.raises(LittleFSError) as e:
        fs = LittleFS(block_count=0)
    assert e.value.code == LittleFSError.Error.LFS_ERR_INVAL


def test_fs_stat_block_count_autodetect():
    block_size = 256
    block_count = 57
    context = UserContext(block_size * block_count)

    # Create the filesystem with 57 blocks
    fs = LittleFS(
        context=context,
        block_size=block_size,
        block_count=block_count,
    )
    assert fs.block_count == 57

    fs = LittleFS(
        context=context,
        block_size=block_size,
        block_count=0,  # infer from superblock
    )

    # Note: filesystem has to be mounted for fs_stat to work.
    info = fs.fs_stat()
    assert info.block_count == 57
    assert info.block_size == 256
