import array
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


@pytest.mark.parametrize(
    "data",
    [b"abc", bytearray(b"abc"), memoryview(b"abc"), array.array("B", b"abc"), memoryview(b"aXbXcX")[::2]],
    ids=["bytes", "bytearray", "memoryview", "array", "strided-memoryview"],
)
def test_attr_bytes_like(fs, data):
    # Any bytes-like object can be stored; it always reads back as bytes.
    fs.setattr("/file.txt", "a", data)
    value = fs.getattr("/file.txt", "a")
    assert value == b"abc"
    assert type(value) is bytes


@pytest.mark.parametrize("data", [3, "abc", [97, 98, 99]], ids=["int", "str", "list"])
def test_attr_not_bytes_like(fs, data):
    with pytest.raises(TypeError):
        fs.setattr("/file.txt", "a", data)


def test_attr_multibyte_items(fs):
    # Wider items would be stored in the host's byte order, so they are refused.
    with pytest.raises(ValueError):
        fs.setattr("/file.txt", "a", array.array("H", [1]))


def test_attr_empty(fs):
    fs.setattr("/file.txt", "e", b"")
    assert fs.getattr("/file.txt", "e") == b""
