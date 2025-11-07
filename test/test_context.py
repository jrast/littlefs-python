import pytest

from littlefs import LittleFS
from littlefs.context import UserContextFile


def test_user_context_file_requires_existing(tmp_path):
    missing = tmp_path / "missing.bin"

    with pytest.raises(FileNotFoundError):
        UserContextFile(str(missing))


def test_user_context_file_persists_between_mounts(tmp_path):
    block_size = 128
    block_count = 32
    backing = tmp_path / "littlefs.bin"

    ctx = UserContextFile(str(backing), create=True)
    fs = LittleFS(context=ctx, block_size=block_size, block_count=block_count)

    with fs.open("hello.txt", "w") as fh:
        fh.write("hello world")

    with fs.open("data.bin", "wb") as fh:
        fh.write(bytes.fromhex("de ad be ef"))

    fs.unmount()
    ctx.close()

    ctx2 = UserContextFile(str(backing))
    fs2 = LittleFS(context=ctx2, block_size=block_size, block_count=block_count)

    with fs2.open("hello.txt", "r") as fh:
        assert fh.read() == "hello world"

    with fs2.open("data.bin", "rb") as fh:
        assert fh.read() == bytes.fromhex("de ad be ef")

    fs2.unmount()
    ctx2.close()
