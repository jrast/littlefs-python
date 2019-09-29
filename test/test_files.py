import pytest
from littlefs import LittleFS


@pytest.fixture(scope='function')
def fs():
    fs = LittleFS(block_size=128, block_count=64)
    yield fs


def test_write_zero_file(fs):
    """Writing a empty file should report zero bytes written"""
    with fs.open('test.txt', 'w') as fh:
        assert fh.write(b'') == 0

def test_write_normal_file(fs):
    """Writing a small file should report the written bytes"""
    with fs.open('test.txt', 'w') as fh:
        assert fh.write(b'abc' * 10) == 30


@pytest.mark.xfail(reason='Currently not implemented as intended', strict=True)
def test_write_to_big_file(fs):
    """Writing a file which is to big should result in a exception"""
    with fs.open('test.txt', 'w') as fh:
        assert fh.write(b'x' * (128 * 64)) == 1234

