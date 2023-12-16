import pytest
from littlefs import LittleFS, LittleFSError


@pytest.fixture(scope="function")
def fs():
    fs = LittleFS(block_size=128, block_count=64)
    with fs.open("/file.txt", "w") as fh:
        fh.write("Sample Text")
    yield fs


def test_attr(fs):
    # Test if 2 attributes can be set without impacting each other.
    fs.setattr("/file.txt", "f", b"foo")
    fs.setattr("/file.txt", "b", b"bar")

    assert b"foo" == fs.getattr("/file.txt", "f")
    assert b"bar" == fs.getattr("/file.txt", "b")

    fs.removeattr("/file.txt", "f")
    with pytest.raises(LittleFSError):
        fs.getattr("/file.txt", "f")

    # Make sure "b" wasn't impacted
    assert b"bar" == fs.getattr("/file.txt", "b")
