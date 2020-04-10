import logging
import typing

if typing.TYPE_CHECKING:
    from .lfs import LFSConfig

class UserContext:
    """Basic User Context Implementation"""

    def __init__(self, buffsize: int) -> None:
        self.buffer = bytearray([0xFF] * buffsize)

    def read(self, cfg: 'LFSConfig', block: int, off: int, size: int) -> bytearray:
        """read data

        Parameters
        ----------
        cfg : ~littlefs.lfs.LFSConfig
            Filesystem configuration object
        block : int
            Block number to read
        off : int
            Offset from start of block
        size : int
            Number of bytes to read.
        """
        logging.getLogger(__name__).debug('LFS Read : Block: %d, Offset: %d, Size=%d' % (block, off, size))
        start = block * cfg.block_size + off
        end = start + size
        return self.buffer[start:end]

    def prog(self, cfg: 'LFSConfig', block: int, off: int, data: bytes) -> int:
        """program data

        Parameters
        ----------
        cfg : ~littlefs.lfs.LFSConfig
            Filesystem configuration object
        block : int
            Block number to program
        off : int
            Offset from start of block
        data : bytes
            Data to write
        """
        logging.getLogger(__name__).debug('LFS Prog : Block: %d, Offset: %d, Data=%r' % (block, off, data))
        start = block * cfg.block_size + off
        end = start + len(data)
        self.buffer[start:end] = data
        return 0

    def erase(self, cfg: 'LFSConfig', block: int) -> int:
        """Erase a block

        Parameters
        ----------
        cfg : ~littlefs.lfs.LFSConfig
            Filesystem configuration object
        block : int
            Block number to read
        """
        logging.getLogger(__name__).debug('LFS Erase: Block: %d' % block)
        start = block * cfg.block_size
        end = start + cfg.block_size
        self.buffer[start:end] = [0xFF] * cfg.block_size
        return 0

    def sync(self, cfg: 'LFSConfig') -> int:
        """Sync cached data

        Parameters
        ----------
        cfg : ~littlefs.lfs.LFSConfig
            Filesystem configuration object
        """
        return 0
