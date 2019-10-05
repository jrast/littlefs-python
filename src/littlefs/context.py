import logging

class UserContext:
    """Basic User Context Implementation"""

    def __init__(self, buffsize):
        self.buffer = bytearray([0xFF] * buffsize)

    def read(self, cfg, block, off, size):
        logging.getLogger(__name__).debug('LFS Read : Block: %d, Offset: %d, Size=%d' % (block, off, size))
        start = block * cfg.block_size + off
        end = start + size
        return self.buffer[start:end]

    def prog(self, cfg, block, off, data):
        logging.getLogger(__name__).debug('LFS Prog : Block: %d, Offset: %d, Data=%s' % (block, off, data))
        start = block * cfg.block_size + off
        end = start + len(data)
        self.buffer[start:end] = data
        return 0

    def erase(self, cfg, block):
        logging.getLogger(__name__).debug('LFS Erase: Block: %d' % block)
        start = block * cfg.block_size
        end = start + cfg.block_size
        self.buffer[start:end] = [0xFF] * cfg.block_size
        return 0

    def sync(self, cfg):
        return 0