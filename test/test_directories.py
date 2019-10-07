import pytest
from littlefs import LittleFS


@pytest.fixture(scope='function')
def fs():
    fs = LittleFS(block_size=128, block_count=64)
    yield fs


def test_listdir(fs):
    dirs = fs.listdir('/')
    assert dirs == []

    dirs = fs.listdir('.')
    assert dirs == []

    fs.mkdir('test')
    assert 'test' in fs.listdir('/')


def test_mkdir(fs):
    fs.mkdir('/test')
    assert 'test' in fs.listdir('/')

    fs.mkdir('./test1')
    assert 'test1' in fs.listdir('/')


def test_mkdir_if_dir_exists(fs):
    fs.mkdir('test')
    with pytest.raises(FileExistsError) as excinfo:
        fs.mkdir('test')
    assert '[LittleFSError -17]' in str(excinfo.value)