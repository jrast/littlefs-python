import pytest
from littlefs import LittleFS
from littlefs import errors


@pytest.fixture(scope='function')
def fs():
    fs = LittleFS(block_size=128, block_count=64)
    fs.mkdir('/dir')
    fs.mkdir('/dir/emptyA')
    fs.mkdir('/dir/emptyB')
    fs.mkdir('/dir/sub')
    with fs.open('/dir/sub/file.txt', 'w') as fh:
        fh.write('Sample Text')
    with fs.open('/dir/file.txt', 'w') as fh:
        fh.write('Sample Text')
    yield fs


def test_remove(fs):
    # Remove empty directory, without leading slash
    fs.remove('/dir/emptyA')

    # Remove empty directory, with leading slash
    fs.remove('/dir/emptyB/')

    # Remove a file
    fs.remove('/dir/file.txt')

    # Remove a folder which is not empty
    with pytest.raises(errors.LittleFSError) as excinfo:
        fs.remove('/dir')
    assert 'LittleFSError' in str(excinfo.value)
    assert excinfo.value.code == -39

    # Remove a file which does not exist
    with pytest.raises(FileNotFoundError) as excinfo:
        fs.remove('/dir/fileB.txt')
    assert 'LittleFSError -2' in str(excinfo.value)
    assert '/dir/fileB.txt' in str(excinfo.value)

    # Remove a directory which does not exist (without leading slash)
    with pytest.raises(FileNotFoundError) as excinfo:
        fs.remove('/dir/directroy')
    assert 'LittleFSError -2' in str(excinfo.value)
    assert '/dir/directroy' in str(excinfo.value)

    # Remove a directory which does not exist (with leading slash)
    with pytest.raises(FileNotFoundError) as excinfo:
        fs.remove('/dir/directroy/')
    assert 'LittleFSError -2' in str(excinfo.value)
    assert '/dir/directroy/' in str(excinfo.value)


def test_removedirs(fs):
    fs.removedirs('/dir/sub/file.txt')
    assert set(fs.listdir('/dir')) == {'emptyA', 'emptyB', 'file.txt'}
    fs.removedirs('/dir/emptyA')
    fs.removedirs('/dir/emptyB')
    assert set(fs.listdir('/dir')) == {'file.txt'}
    fs.removedirs('/dir/file.txt')
    assert fs.listdir('/') == [ ]

