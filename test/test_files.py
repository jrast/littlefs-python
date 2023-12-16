import pytest
from littlefs import LittleFS, FileHandle


@pytest.fixture(scope="function")
def fs():
    fs = LittleFS(block_size=128, block_count=64)
    fs.mkdir("mydir")

    with fs.open("test.txt", "w") as f:
        f.write("1234567890")

    with fs.open("test.bin", "wb") as f:
        contents = bytes.fromhex("11 22 33 44 aa bb cc dd ee ff")
        f.write(contents)

    yield fs


def test_open_notfound(fs):
    with pytest.raises(FileNotFoundError):
        with fs.open("test2.txt") as f:
            pass


def test_open_isdir(fs):
    with pytest.raises(IsADirectoryError):
        with fs.open("mydir") as f:
            pass


def test_open_exists(fs):
    with pytest.raises(FileExistsError):
        with fs.open("test.txt", "x") as f:
            pass


def test_open_invalid_mode(fs):
    with pytest.raises(ValueError) as excinfo:
        with fs.open("test.txt", "c") as fh:
            pass

    assert str(excinfo.value) == "invalid mode: 'c'"


def test_open_binary_and_text(fs):
    with pytest.raises(ValueError) as excinfo:
        with fs.open("test.txt", "bt") as fh:
            pass

    assert str(excinfo.value) == "can't have text and binary mode at once"


def test_bin_read(fs):
    with fs.open("test.txt", "rb") as f:
        data = f.read()

    assert data == b"1234567890"


def test_text_read(fs):
    with fs.open("test.txt", "rt") as f:
        data = f.read()

    assert data == "1234567890"


def test_bin_append(fs):
    with fs.open("test.txt", "ab") as f:
        f.write(b"1234567890")

    info = fs.stat("test.txt")
    assert info.size == 20


def test_text_encoding(fs):
    txt_data = "abcdefghijklmnopqrstuvwxyz" "αβγδεζηθικλμνξοπρστυφχψω"
    bin_data = txt_data.encode("utf8")

    with fs.open("test2.txt", "w", encoding="utf8") as f:
        f.write(txt_data)

    info = fs.stat("test2.txt")
    assert info.size == len(bin_data)

    with fs.open("test2.txt", "rb") as f:
        data = f.read()
        assert data == bin_data

    with fs.open("test2.txt", "r", encoding="utf8") as f:
        data = f.read()
        assert data == txt_data

    offset = 30
    file_offset = len(txt_data[:offset].encode("utf8"))

    with fs.open("test2.txt", "r", encoding="utf8") as f:
        f.seek(file_offset)
        data = f.read(4)
        assert data == txt_data[offset : offset + 4]


def test_text_lines(fs):
    fname = "test2.txt"
    lipsum = (
        "Lorem ipsum dolor sit amet, consectetur adipiscing elit, \n"
        "sed do eiusmod tempor incididunt ut labore et dolore magna aliqua.\n"
        "Ut enim ad minim veniam, quis nostrud exercitation ullamco laboris \n"
        "nisi ut aliquip ex ea commodo consequat."
    )

    with fs.open(fname, "w") as f:
        f.write(lipsum)

    num_lines = 0

    with fs.open(fname, "r") as f:
        for _ in f:
            num_lines += 1

    assert num_lines == len(lipsum.splitlines())


def test_bin_read_update(fs):
    with fs.open("test.bin", "r+b") as f:
        f.seek(2)
        a = f.read(2)
        b = f.read(2)

        assert a == bytes.fromhex("33 44")
        assert b == bytes.fromhex("aa bb")
        assert f.tell() == 6

        f.seek(2)
        f.write(b)
        f.write(a)

    expected = bytes.fromhex("11 22 aa bb 33 44 cc dd ee ff")

    with fs.open("test.bin", "rb") as f:
        data = f.read()
        assert data == expected


def test_bin_write_update(fs):
    contents = bytes.fromhex("11 aa 22 bb 33 cc 44 dd")

    with fs.open("test.bin", "w+b") as f:
        data = f.read()
        assert data == b""

        f.write(contents)
        f.seek(4)
        data = f.read(4)
        assert data == contents[4:8]


def test_bin_append_update(fs):
    fname = "test2.bin"
    contents = bytes.fromhex("11 aa 22 bb 33 cc 44 dd")

    with fs.open(fname, "wb") as f:
        f.write(contents[0:6])

    with fs.open(fname, "a+b") as f:
        f.write(contents[6:])
        f.seek(0)

        data = f.read()
        assert data == contents


def test_text_read_update(fs):
    with fs.open("test.txt", "r+") as f:
        f.seek(2)
        a = f.read(2)
        b = f.read(2)

        assert a == "34"
        assert b == "56"
        assert f.tell() == 6

        f.seek(2)
        f.write(b)
        f.write(a)

    expected = "1256347890"

    with fs.open("test.txt", "r") as f:
        data = f.read()
        assert data == expected


def test_text_write_update(fs):
    contents = "1a2b3c4d"

    with fs.open("test.txt", "w+") as f:
        data = f.read()
        assert data == ""

        f.write(contents)
        f.seek(4)
        data = f.read(4)
        assert data == contents[4:8]


def test_text_append_update(fs):
    fname = "test2.txt"
    contents = "1a2b3c4d"

    with fs.open(fname, "w") as f:
        f.write(contents[0:6])

    with fs.open(fname, "a+") as f:
        f.write(contents[6:])
        f.seek(0)

        data = f.read()
        assert data == contents


def test_text_truncate(fs: LittleFS):
    with fs.open("trunc.txt", "w") as f:
        f.write("Some Content")

    with fs.open("trunc.txt", "r+") as f:
        f.truncate()

    assert fs.open("trunc.txt", "r").read() == ""
