

class LittleFSError(Exception):

    def __init__(self, code):
        super().__init__()
        self.code = code

    def __repr__(self):
        return '<%s(%d)>' % (
            self.__class__.__name__,
            self.code
        )

    def __str__(self):
        return 'LittleFSError Code %d' % self.code



