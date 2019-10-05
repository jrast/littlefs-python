

class LittleFSException(Exception):

    def __init__(self, code):
        super().__init__()
        self.code = code



