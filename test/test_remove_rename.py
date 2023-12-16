import pytest
from littlefs import LittleFS
from littlefs import errors


@pytest.fixture(scope="function")
def fs():
    fs = LittleFS(block_size=128, block_count=64)
    fs.mkdir("/dir")
    fs.mkdir("/dir/emptyA")
    fs.mkdir("/dir/emptyB")
    fs.mkdir("/dir/sub")
    with fs.open("/dir/sub/file.txt", "w") as fh:
        fh.write("Sample Text")
    with fs.open("/dir/file.txt", "w") as fh:
        fh.write("Sample Text")
    yield fs


def test_remove(fs):
    # Remove empty directory, without leading slash
    fs.remove("/dir/emptyA")

    # Remove empty directory, with leading slash
    fs.remove("/dir/emptyB/")

    # Remove a file
    fs.remove("/dir/file.txt")

    # Remove a folder which is not empty
    with pytest.raises(errors.LittleFSError) as excinfo:
        fs.remove("/dir")
    assert "LittleFSError" in str(excinfo.value)
    assert excinfo.value.code == -39

    # Remove a file which does not exist
    with pytest.raises(FileNotFoundError) as excinfo:
        fs.remove("/dir/fileB.txt")
    assert "LittleFSError -2" in str(excinfo.value)
    assert "/dir/fileB.txt" in str(excinfo.value)

    # Remove a directory which does not exist (without leading slash)
    with pytest.raises(FileNotFoundError) as excinfo:
        fs.remove("/dir/thisdirdoesnotexist")
    assert "LittleFSError -2" in str(excinfo.value)
    assert "/dir/thisdirdoesnotexist" in str(excinfo.value)

    # Remove a directory which does not exist (with leading slash)
    with pytest.raises(FileNotFoundError) as excinfo:
        fs.remove("/dir/directory/")
    assert "LittleFSError -2" in str(excinfo.value)
    assert "/dir/directory/" in str(excinfo.value)


def test_remove_recursive(fs):
    fs.remove("/dir", recursive=True)
    with pytest.raises(errors.LittleFSError) as excinfo:
        fs.stat("/dir")
    assert "LittleFSError -2" in str(excinfo.value)


def test_removedirs(fs):
    fs.removedirs("/dir/sub/file.txt")
    assert set(fs.listdir("/dir")) == {"emptyA", "emptyB", "file.txt"}
    fs.removedirs("/dir/emptyA")
    fs.removedirs("/dir/emptyB")
    assert set(fs.listdir("/dir")) == {"file.txt"}
    fs.removedirs("/dir/file.txt")
    assert fs.listdir("/") == []


def test_rename(fs: LittleFS):
    # File rename
    fs.rename("/dir/file.txt", "/dir/file_renamed.txt")
    files_in_dir = fs.listdir("/dir")

    assert "file.txt" not in files_in_dir
    assert "file_renamed.txt" in files_in_dir

    # Directory Rename
    fs.rename("/dir/sub", "/dir/sub_renamed")
    files_in_dir = fs.listdir("/dir")

    assert "sub" not in files_in_dir
    assert "sub_renamed" in files_in_dir
