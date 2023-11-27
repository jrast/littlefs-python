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



# if the user has win32file installed then define this class
try:
    import ctypes
    import win32file
    class UserContextWinDisk(UserContext):
        def __init__(self, disk_path:str) -> None:
            
            self.device = win32file.CreateFile(disk_path, win32file.GENERIC_READ, win32file.FILE_SHARE_READ, None, win32file.OPEN_EXISTING, 0, None)
            if self.device == win32file.INVALID_HANDLE_VALUE:
                raise Exception("Error opening disk")
            

        
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
            win32file.SetFilePointer(self.device, start, win32file.FILE_BEGIN)
            buffer = ctypes.create_string_buffer(size)
            win32file.ReadFile(self.device, buffer)
            # store the data in the buffer and close the buffer
            data = buffer.raw
            return data
        
        def prog(self, cfg: 'LFSConfig', block: int, off: int, data: bytes) -> int:
        
            logging.getLogger(__name__).debug('LFS Prog : Block: %d, Offset: %d, Data=%r' % (block, off, data))
            start = block * cfg.block_size + off
            end = start + len(data)
            win32file.SetFilePointer(self.device, start, win32file.FILE_BEGIN)
            win32file.WriteFile(self.device, data)
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
            win32file.SetFilePointer(self.device, start, win32file.FILE_BEGIN)
            win32file.WriteFile( self.device, [0xFF] * cfg.block_size)
            return 0
        
        def sync(self, cfg: 'LFSConfig') -> int:
            win32file.FlushFileBuffers(self.device)
            return 0
        
        def __del__(self):
            win32file.CloseHandle(self.device)
        
except ImportError:
     class UserContextWinDisk:
        def __init__(self, disk_path: str) -> None:
            raise ImportError("win32file module is not installed. You might need to install pywin32 or not in Windows")