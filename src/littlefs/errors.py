from enum import IntEnum


class LittleFSError(Exception):
    class Error(IntEnum):
        LFS_ERR_OK = 0  # No error
        LFS_ERR_IO = -5  # Error during device operation
        LFS_ERR_CORRUPT = -84  # Corrupted
        LFS_ERR_NOENT = -2  # No directory entry
        LFS_ERR_EXIST = -17  # Entry already exists
        LFS_ERR_NOTDIR = -20  # Entry is not a dir
        LFS_ERR_ISDIR = -21  # Entry is a dir
        LFS_ERR_NOTEMPTY = -39  # Dir is not empty
        LFS_ERR_BADF = -9  # Bad file number
        LFS_ERR_FBIG = -27  # File too large
        LFS_ERR_INVAL = -22  # Invalid parameter
        LFS_ERR_NOSPC = -28  # No space left on device
        LFS_ERR_NOMEM = -12  # No more memory available
        LFS_ERR_NOATTR = -61  # No data/attr available
        LFS_ERR_NAMETOOLONG = -36  # File name too long

    def __init__(self, code: int):
        super().__init__()
        self.code = code

    @property
    def name(self) -> str:
        try:
            return self.Error(self.code).name
        except ValueError:
            return "ERR_UNKNOWN"

    def __repr__(self) -> str:
        return "<%s(%d)>" % (self.__class__.__name__, self.code)

    def __str__(self) -> str:
        return "LittleFSError %d: %s" % (self.code, self.name)
