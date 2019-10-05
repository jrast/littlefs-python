from littlefs import lfs


def test_file_open(mounted_fs):
    fh = lfs.file_open(mounted_fs, 'test.txt', 'w')


def test_file_close(mounted_fs):
    fh = lfs.file_open(mounted_fs, 'test.txt', 'w')
    lfs.file_close(mounted_fs, fh)


def test_file_sync(mounted_fs):
    fh = lfs.file_open(mounted_fs, 'test.txt', 'w')
    lfs.file_sync(mounted_fs, fh)


def test_file_read(mounted_fs):
    fh = lfs.file_open(mounted_fs, 'test.txt', 'w')
    lfs.file_write(mounted_fs, fh, b'0123456789')
    lfs.file_close(mounted_fs, fh)

    fh = lfs.file_open(mounted_fs, 'test.txt', 'r')
    data = lfs.file_read(mounted_fs, fh, 10)
    assert data == b'0123456789'


def test_file_write(mounted_fs):
    fh = lfs.file_open(mounted_fs, 'test.txt', 'w')
    lfs.file_write(mounted_fs, fh, b'0123456789')


def test_file_seek(mounted_fs):
    fh = lfs.file_open(mounted_fs, 'test.txt', 'w')
    # Seek whenece:
    #   0: Absolute
    #   1: Relative to Current Position
    #   2: Relative to EOF
    new_pos = lfs.file_seek(mounted_fs, fh, 10, 0)
    assert new_pos == 10


def test_file_truncate(mounted_fs):
    fh = lfs.file_open(mounted_fs, 'test.txt', 'w')
    assert lfs.file_truncate(mounted_fs, fh, 10) == 0


def test_file_tell(mounted_fs):
    fh = lfs.file_open(mounted_fs, 'test.txt', 'w')
    assert lfs.file_tell(mounted_fs, fh) == 0


def test_file_rewind(mounted_fs):
    fh = lfs.file_open(mounted_fs, 'test.txt', 'w')
    assert lfs.file_rewind(mounted_fs, fh) == 0


def test_file_size(mounted_fs):
    fh = lfs.file_open(mounted_fs, 'test.txt', 'w')
    assert lfs.file_size(mounted_fs, fh) == 0