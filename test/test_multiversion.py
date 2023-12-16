import pytest
from littlefs import LittleFS, FileHandle, LittleFSError


def create_image(version):
    fs = LittleFS(block_size=128, block_count=64, disk_version=version)
    fs.mkdir("testdir")
    with fs.open("file.txt", "w") as f:
        f.write("Sample Content")

    return fs.context.buffer


@pytest.fixture(scope="function")
def fs20():
    fs = LittleFS(block_size=128, block_count=64, disk_version=0x00020000)
    fs.mkdir("mydir")

    with fs.open("test.txt", "w") as f:
        f.write("1234567890")

    yield fs


@pytest.fixture(scope="function")
def fs21():
    fs = LittleFS(block_size=128, block_count=64, disk_version=0x00020001)
    fs.mkdir("mydir")

    with fs.open("test.txt", "w") as f:
        f.write("1234567890")

    yield fs


def test_lfs20(fs20):
    assert fs20.fs_stat().disk_version == 0x00020000


def test_lfs21(fs21):
    assert fs21.fs_stat().disk_version == 0x00020001


@pytest.mark.parametrize("version", [0x00020000, 0x00020001], ids=["FS2.0", "FS2.1"])
def test_load_images(version):
    fs = LittleFS(block_size=128, block_count=64, disk_version=0x00020001)
    fs.context.buffer = create_image(version)
    fs.mount()
    stat = fs.fs_stat()
    assert stat.disk_version == version


def test_load_incompatible_image():
    fs = LittleFS(block_size=128, block_count=64, disk_version=0x00020000)
    fs.context.buffer = create_image(0x00020001)
    with pytest.raises(LittleFSError, match="-22: LFS_ERR_INVAL"):
        assert fs.mount()
