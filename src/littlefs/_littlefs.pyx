import logging
# Import all definitions
from littlefs._littlefs_c cimport *


# Export LFS version and disk version to python
__LFS_VERSION__ = (LFS_VERSION_MAJOR, LFS_VERSION_MINOR)
__LFS_DISK_VERSION__ = (LFS_DISK_VERSION_MAJOR, LFS_DISK_VERSION_MINOR)


cdef int _lfs_read(const lfs_config *c, lfs_block_t block, lfs_off_t off, void * buffer, lfs_size_t size):
    fs = <object>c.context
    data = fs.user_context.read(fs, block, off, size)
    memcpy(buffer, <char *>data, size)
    return 0
    

cdef int _lfs_prog(const lfs_config *c, lfs_block_t block, lfs_off_t off, const void * buffer, lfs_size_t size):
    fs = <object>c.context
    data = (<char*>buffer)[:size]
    return fs.user_context.prog(fs, block, off, data)


cdef int _lfs_erase(const lfs_config *c, lfs_block_t block):
    fs = <object>c.context
    return fs.user_context.erase(fs, block)


cdef int _lfs_sync(const lfs_config *c):
    fs = <object>c.context
    return fs.user_context.sync(fs)


cdef int _raise_on_error(int code):
    if code < 0:
        raise RuntimeError('Operation Failed. Error %d' % code)
    return code


class UserContext:
    """Basic User Context Implementation"""

    def __init__(self, buffsize):
        self.buffer = bytearray([0xFF] * buffsize)

    def read(self, fs, block, off, size):
        logging.getLogger(__name__).debug('LFS Read : Block: %d, Offset: %d, Size=%d' % (block, off, size))
        start = block * fs.block_size + off
        end = start + size
        return self.buffer[start:end]

    def prog(self, fs, block, off, data):
        logging.getLogger(__name__).debug('LFS Prog : Block: %d, Offset: %d, Data=%s' % (block, off, data))
        start = block * fs.block_size + off
        end = start + len(data)
        self.buffer[start:end] = data
        return 0

    def erase(self, fs, block):
        logging.getLogger(__name__).debug('LFS Erase: Block: %d' % block)
        start = block * fs.block_size
        end = start + fs.block_size
        self.buffer[start:end] = [0xFF] * fs.block_size
        return 0

    def sync(self, fs):
        return 0


cdef class LittleFS:
    """Littlefs file system"""

    cdef dict __dict__
    cdef lfs_config cfg
    cdef lfs_t lfs

    
    FILENAME_ENCODING = 'ascii'
    """Encoding used for file and directory names"""

    def __init__(self, context=None, **kwargs):
        self.cfg.read = &_lfs_read
        self.cfg.prog = &_lfs_prog
        self.cfg.erase = &_lfs_erase
        self.cfg.sync = &_lfs_sync

        block_size = kwargs.get('block_size', 128)
        block_count = kwargs.get('block_count', 64)

        if block_size < 128:
            raise ValueError('Minimal block size is 128')

        self.cfg.read_size = kwargs.get('read_size', block_size)
        self.cfg.prog_size = kwargs.get('prog_size', block_size)
        self.cfg.block_size = block_size
        self.cfg.block_count = block_count
        self.cfg.block_cycles = kwargs.get('block_cycles', -1)
        # Cache size, at least as big as read / prog size
        self.cfg.cache_size = kwargs.get('cache_size', max(self.cfg.read_size, self.cfg.prog_size))
        # Lookahead buffer size in bytes
        self.cfg.lookahead_size = kwargs.get('lookahead_size', 8)

        if context is None:
            context = UserContext(self.block_size * self.block_count)

        self.user_context = context
        self.cfg.context = <void *>self

        error = lfs_mount(&self.lfs, &self.cfg)
        if error:
            _raise_on_error(lfs_format(&self.lfs, &self.cfg))
            _raise_on_error(lfs_mount(&self.lfs, &self.cfg))

    # Expose interesting part of the configuration as read only properties
    @property
    def read_size(self):
        return self.cfg.read_size

    @property
    def prog_size(self):
        return self.cfg.prog_size
    
    @property
    def block_size(self):
        return self.cfg.block_size

    @property
    def block_count(self):
        return self.cfg.block_count
        
    @property
    def cache_size(self):
        return self.cfg.cache_size

    @property
    def lookahead_size(self):
        return self.cfg.lookahead_size

    @property
    def size(self):
        """Current size of the filesystem
        
        Notes
        -----
        This is a "best effort", the actual size might be different
        smaller than reported by this property.
        
        """
        return _raise_on_error(lfs_fs_size(&self.lfs))

    def open(self, fname, mode='r'):
        """Open a file
        
        Parameters
        ----------
        fname : str
            Name of the file which should be openend.
        mode : str
            The mode in which the file should be openend. Currently only 'r' and 'w'
            is supported.
        """
        if mode == 'w':
            mode = LFS_O_WRONLY | LFS_O_CREAT
        elif mode == 'r':
            mode = LFS_O_RDONLY
        else:
            raise NotImplementedError

        cdef lfs_file_t * fh = <lfs_file_t *>malloc(sizeof(lfs_file_t))
        _raise_on_error(lfs_file_open(&self.lfs, fh, fname.encode(self.FILENAME_ENCODING), mode))
        return LFSFileHandle.create(&self.lfs, fh)

    def mkdir(self, path):
        pass
        


cdef class LFSFileHandle:
    """File handle for littlefs files"""

    cdef lfs_t * fs
    cdef lfs_file_t * fh

    @staticmethod
    cdef create(lfs_t * fs, lfs_file_t * fh):
        obj = LFSFileHandle()
        obj.fs = fs
        obj.fh = fh
        return obj

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()

    def write(self, data):
        assert isinstance(data, (bytes, bytearray))
        assert self.fh != NULL
        pdata = <char *>data
        code =_raise_on_error(lfs_file_write(self.fs, self.fh, <char *>data, len(data)))
        if code != len(data):
            raise RuntimeError("Not all data written")
        return code

    def read(self, size):
        assert self.fh != NULL
        assert size >= 0
        data = b'\0xff' * size
        rsize = _raise_on_error(lfs_file_read(self.fs, self.fh, <char *>data, size))
        return data[:rsize]

    def close(self):
        assert self.fh != NULL, 'File already closed'
        _raise_on_error(lfs_file_close(self.fs, self.fh))
        free(self.fh)
        self.fh = NULL
