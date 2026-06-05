import pytest

from littlefs import LittleFS

# A mix of Latin-1, CJK and astral-plane (emoji) characters to exercise
# multi-byte UTF-8 sequences.
UNICODE_NAMES = ["café.txt", "日本語.bin", "emoji_😀.dat"]


@pytest.fixture(scope="function")
def fs():
    yield LittleFS(block_size=128, block_count=64)


@pytest.mark.parametrize("name", UNICODE_NAMES)
def test_open_write_read_roundtrip(fs, name):
    payload = name.encode("utf-8")
    with fs.open(name, "wb") as f:
        f.write(payload)
    with fs.open(name, "rb") as f:
        assert f.read() == payload


@pytest.mark.parametrize("name", UNICODE_NAMES)
def test_stat_preserves_name(fs, name):
    with fs.open(name, "wb") as f:
        f.write(b"x")
    assert fs.stat(name).name == name


def test_listdir_roundtrips_unicode(fs):
    for name in UNICODE_NAMES:
        with fs.open(name, "wb") as f:
            f.write(b"x")
    assert set(fs.listdir("/")) == set(UNICODE_NAMES)


@pytest.mark.parametrize("name", UNICODE_NAMES)
def test_mkdir_and_nested_file(fs, name):
    fs.mkdir(name)
    assert name in fs.listdir("/")
    nested = name + "/inner_£.txt"
    with fs.open(nested, "wb") as f:
        f.write(b"x")
    assert fs.stat(nested).name == "inner_£.txt"


@pytest.mark.parametrize("name", UNICODE_NAMES)
def test_rename_and_remove(fs, name):
    with fs.open(name, "wb") as f:
        f.write(b"x")
    renamed = "renamed_" + name
    fs.rename(name, renamed)
    assert renamed in fs.listdir("/")
    assert name not in fs.listdir("/")
    fs.remove(renamed)
    assert renamed not in fs.listdir("/")


def test_ascii_names_still_work(fs):
    """ASCII is a strict subset of UTF-8: existing names must be unaffected."""
    with fs.open("plain.txt", "wb") as f:
        f.write(b"hello")
    with fs.open("plain.txt", "rb") as f:
        assert f.read() == b"hello"
    assert fs.stat("plain.txt").name == "plain.txt"


def test_per_instance_encoding_roundtrips():
    """A non-UTF-8 ``filename_encoding`` is honored for both encode and decode."""
    fs = LittleFS(block_size=128, block_count=64, filename_encoding="latin-1")
    # "ÿ" is 0xFF in latin-1 but a 2-byte sequence in utf-8.
    name = "naïveÿ.txt"
    with fs.open(name, "wb") as f:
        f.write(b"x")
    assert fs.stat(name).name == name
    assert name in fs.listdir("/")
    fs.rename(name, "renamed_ÿ.txt")
    assert "renamed_ÿ.txt" in fs.listdir("/")


def test_per_instance_encoding_writes_expected_bytes():
    """The on-disk name bytes reflect the chosen encoding, not the default UTF-8."""
    fs = LittleFS(block_size=128, block_count=64, filename_encoding="latin-1")
    with fs.open("ÿ.txt", "wb") as f:
        f.write(b"x")
    # Re-mount the same backing store with latin-1: names decode cleanly.
    same = LittleFS(context=fs.context, filename_encoding="latin-1", block_size=128, block_count=64)
    assert "ÿ.txt" in same.listdir("/")
    # The byte written was 0xFF, which is invalid standalone UTF-8, so a UTF-8
    # instance over the same store fails loudly rather than silently mis-decoding.
    utf8_view = LittleFS(context=fs.context, block_size=128, block_count=64)
    with pytest.raises(UnicodeDecodeError):
        utf8_view.listdir("/")


def test_default_encoding_is_utf8():
    fs = LittleFS(block_size=128, block_count=64)
    from littlefs import lfs

    assert fs.filename_encoding == lfs.FILENAME_ENCODING == "utf-8"
