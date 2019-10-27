

ERROR_MAP = {
    -5: 'ERR_IO',
    -84: 'ERR_CORRUPT',
    -2: 'ERR_NOENT',
    -17: 'ERR_EXIST',
    -20: 'ERR_NOTDIR',
    -21: 'ERR_ISDIR',
    -39: 'ERR_NOTEMPTY',
    -9: 'ERR_BADF',
    -27: 'ERR_FBIG',
    -22: 'ERR_INVAL',
    -28: 'ERR_NOSPC',
    -12: 'ERR_NOMEM',
    -61: 'ERR_NOATTR',
    -36: 'ERR_NAMETOOLONG',
}

class LittleFSError(Exception):

    def __init__(self, code):
        super().__init__()
        self.code = code

    @property
    def name(self):
        return ERROR_MAP.get(self.code, 'ERR_UNKNOWN')

    def __repr__(self):
        return '<%s(%d)>' % (
            self.__class__.__name__,
            self.code
        )

    def __str__(self):
        return 'LittleFSError %d: %s' % (self.code, self.name)



