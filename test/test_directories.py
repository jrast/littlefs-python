import pytest
from littlefs import LittleFS


@pytest.fixture(scope="function")
def fs():
    fs = LittleFS(block_size=128, block_count=64)
    yield fs


def test_listdir(fs):
    dirs = fs.listdir("/")
    assert dirs == []

    dirs = fs.listdir(".")
    assert dirs == []

    fs.mkdir("test")
    assert fs.listdir("/") == ["test"]

    fs.mkdir("test/sub")
    assert fs.listdir("/") == ["test"]
    assert fs.listdir("/test") == ["sub"]


def test_mkdir(fs):
    fs.mkdir("/test")
    assert "test" in fs.listdir("/")

    fs.mkdir("./test1")
    assert fs.listdir("/") == ["test1", "test"]


def test_mkdir_if_dir_exists(fs):
    fs.mkdir("test")
    with pytest.raises(FileExistsError) as excinfo:
        fs.mkdir("test")
    assert "[LittleFSError -17]" in str(excinfo.value)


def test_makedirs(fs):
    # Simple invocation. Here the filesystem contains no folders yet.
    fs.makedirs("/dir/sub/subsub")
    assert fs.listdir("/") == ["dir"]
    assert fs.listdir("/dir") == ["sub"]
    assert fs.listdir("/dir/sub") == ["subsub"]

    # Create the same folder again. Do not rise if the directory exists.
    fs.makedirs("/dir/sub/subsub", exist_ok=True)
    assert fs.listdir("/") == ["dir"]
    assert fs.listdir("/dir") == ["sub"]
    assert fs.listdir("/dir/sub") == ["subsub"]

    # Create again, but raise if the directory exits
    with pytest.raises(FileExistsError) as excinfo:
        fs.makedirs("/dir/sub/subsub", exist_ok=False)
    assert "[LittleFSError -17]" in str(excinfo.value)
    assert "/dir/sub/subsub" in str(excinfo.value)
    assert fs.listdir("/") == ["dir"]
    assert fs.listdir("/dir") == ["sub"]
    assert fs.listdir("/dir/sub") == ["subsub"]

    # Create another directory on the third level
    fs.makedirs("/dir/sub/abc")
    assert fs.listdir("/") == ["dir"]
    assert fs.listdir("/dir") == ["sub"]
    assert fs.listdir("/dir/sub") == ["abc", "subsub"]
