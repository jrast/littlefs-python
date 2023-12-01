import pytest
from littlefs import lfs, LittleFS


def test_name_max_gt_1022():
    """Don't allow a `name_max > 1022`.

    From the LittleFS documentation:

        // Maximum name size in bytes, may be redefined to reduce the size of the
        // info struct. Limited to <= 1022. Stored in superblock and must be
        // respected by other littlefs drivers.

    Originally reported:
        https://github.com/jrast/littlefs-python/issues/61
    """

    with pytest.raises(ValueError):
        LittleFS(name_max=1023)


def test_name_max_0():
    """Ensures that defaulting to ``LFS_NAME_MAX`` is valid.

    Originally reported:
        https://github.com/jrast/littlefs-python/issues/61
    """
    fs = LittleFS(name_max=0)
    stat = fs.fs_stat()
    assert stat.name_max == 1022
