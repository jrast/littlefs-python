import pytest
from littlefs import LittleFS


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


def test_walk(fs):
    data = []
    for root, dirs, files in fs.walk("/"):
        data.append((root, dirs, files))
    assert data == [
        ("/", ["dir"], []),
        ("/dir", ["emptyA", "emptyB", "sub"], ["file.txt"]),
        ("/dir/emptyA", [], []),
        ("/dir/emptyB", [], []),
        ("/dir/sub", [], ["file.txt"]),
    ]


def test_walk_size(fs):
    sizes = []
    for root, dirs, files in fs.walk("/"):
        sizes.append((root, sum(fs.stat("/".join((root, name))).size for name in files)))

    assert sizes == [
        ("/", 0),
        ("/dir", 11),
        ("/dir/emptyA", 0),
        ("/dir/emptyB", 0),
        ("/dir/sub", 11),
    ]
