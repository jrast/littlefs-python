import logging
from collections import namedtuple
# Import all definitions
# from littlefs._lfs cimport *

from littlefs.context import UserContext
from littlefs import errors


FILENAME_ENCODING = 'ascii'
LFSStat = namedtuple('LFSStat', ['type', 'size', 'name'])


# Export LFS version and disk version to python
__LFS_VERSION__ = (LFS_VERSION_MAJOR, LFS_VERSION_MINOR)
__LFS_DISK_VERSION__ = (LFS_DISK_VERSION_MAJOR, LFS_DISK_VERSION_MINOR)


cdef int _lfs_read(const lfs_config *c, lfs_block_t block, lfs_off_t off, void * buffer, lfs_size_t size):
    ctx = <object>c.context
    data = ctx.user_context.read(ctx, block, off, size)
    memcpy(buffer, <char *>data, size)
    return 0


cdef int _lfs_prog(const lfs_config *c, lfs_block_t block, lfs_off_t off, const void * buffer, lfs_size_t size):
    ctx = <object>c.context
    data = (<char*>buffer)[:size]
    return ctx.user_context.prog(ctx, block, off, data)


cdef int _lfs_erase(const lfs_config *c, lfs_block_t block):
    ctx = <object>c.context
    return ctx.user_context.erase(ctx, block)


cdef int _lfs_sync(const lfs_config *c):
    ctx = <object>c.context
    return ctx.user_context.sync(ctx)


cdef int _raise_on_error(int code) except -1:
    if code < 0:
        raise errors.LittleFSError(code)
    return code



cdef class LFSConfig:

    cdef lfs_config _impl
    cdef dict __dict__

    def __cinit__(self):
        self._impl.read = &_lfs_read
        self._impl.prog = &_lfs_prog
        self._impl.erase = &_lfs_erase
        self._impl.sync = &_lfs_sync


    def __init__(self, context=None, **kwargs):
        # If the block size and count is not given, create a
        # small memory with minimal block size and 8KB size
        block_size = kwargs.get('block_size', 128)
        block_count = kwargs.get('block_count', 64)

        if block_size < 128:
            raise ValueError('Minimal block size is 128')

        self._impl.read_size = kwargs.get('read_size', block_size)
        self._impl.prog_size = kwargs.get('prog_size', block_size)
        self._impl.block_size = block_size
        self._impl.block_count = block_count
        self._impl.block_cycles = kwargs.get('block_cycles', -1)
        # Cache size, at least as big as read / prog size
        self._impl.cache_size = kwargs.get('cache_size', max(self._impl.read_size, self._impl.prog_size))
        # Lookahead buffer size in bytes
        self._impl.lookahead_size = kwargs.get('lookahead_size', 8)

        if context is None:
            context = UserContext(self._impl.block_size * self._impl.block_count)

        self.user_context = context
        self._impl.context = <void *>self

    @property
    def read_size(self):
        return self._impl.read_size

    @property
    def prog_size(self):
        return self._impl.prog_size

    @property
    def block_size(self):
        return self._impl.block_size

    @property
    def block_count(self):
        return self._impl.block_count

    @property
    def cache_size(self):
        return self._impl.cache_size

    @property
    def lookahead_size(self):
        return self._impl.lookahead_size


cdef class LFSFilesystem:
    cdef lfs_t _impl


cdef class LFSFile:
    cdef lfs_file_t _impl


cdef class LFSDirectory:
    cdef lfs_dir_t _impl


def fs_size(LFSFilesystem fs):
    return _raise_on_error(lfs_fs_size(&fs._impl))


def format(LFSFilesystem fs, LFSConfig cfg):
    """Format the filesystem"""
    return _raise_on_error(lfs_format(&fs._impl, &cfg._impl))


def mount(LFSFilesystem fs, LFSConfig cfg):
    """Mount the filesystem"""
    return _raise_on_error(lfs_mount(&fs._impl, &cfg._impl))


def unmount(LFSFilesystem fs):
    """Unmount the filesystem

    This does nothing beside releasing any allocated resources
    """
    return _raise_on_error(lfs_unmount(&fs._impl))


def remove(LFSFilesystem fs, path):
    """Remove a file or directory

    If removing a direcotry, the directory must be empty.
    """
    return _raise_on_error(lfs_remove(&fs._impl, path.encode(FILENAME_ENCODING)))

def rename(LFSFilesystem fs, oldpath, newpath):
    """Rename or move a file or directory

    If the destination exists, it must match the source in type.
    If the destination is a directory, the directory must be empty.
    """
    return _raise_on_error(lfs_rename(&fs._impl, oldpath.encode(FILENAME_ENCODING),
                                        newpath.encode(FILENAME_ENCODING)))


def stat(LFSFilesystem fs, path):
    """Find info about a file or directory"""
    cdef lfs_info * info = <lfs_info *>malloc(sizeof(lfs_info))
    try:
        _raise_on_error(lfs_stat(&fs._impl, path.encode(FILENAME_ENCODING), info))
        return LFSStat(info.type, info.size, info.name.decode(FILENAME_ENCODING))
    finally:
        free(info)


def getattr(LFSFilesystem fs, path, type, buffer, size):
    raise NotImplementedError


def setattr(LFSFilesystem fs, path, type, buffer, size):
    raise NotImplementedError


def removeattr(LFSFilesystem fs, path, type):
    raise NotImplementedError


def file_open(LFSFilesystem fs, path, flags):
    if flags == 'w':
        flags = LFS_O_WRONLY | LFS_O_CREAT
    elif flags == 'r':
        flags = LFS_O_RDONLY
    else:
        raise NotImplementedError
    fh = LFSFile()
    _raise_on_error(lfs_file_open(&fs._impl, &fh._impl, path.encode(FILENAME_ENCODING), flags))
    return fh


def file_open_cfg(self, path, flags, config):
    raise NotImplementedError


def file_close(LFSFilesystem fs, LFSFile fh):
    return _raise_on_error(lfs_file_close(&fs._impl, &fh._impl))


def file_sync(LFSFilesystem fs, LFSFile fh):
    _raise_on_error(lfs_file_sync(&fs._impl, &fh._impl))


def file_read(LFSFilesystem fs, LFSFile fh, size):
    assert size >= 0, 'Size must be >= 0'
    buffer = b'\0xff' * size
    rsize = _raise_on_error(lfs_file_read(&fs._impl, &fh._impl, <char *>buffer, size))
    return buffer[:rsize]


def file_write(LFSFilesystem fs, LFSFile fh, data):
    assert isinstance(data, (bytes, bytearray))
    pdata = <char *>data
    code =_raise_on_error(lfs_file_write(&fs._impl, &fh._impl, <char *>data, len(data)))
    if code != len(data):
        raise RuntimeError("Not all data written")
    return code


def file_seek(LFSFilesystem fs, LFSFile fh, off, whence):
    return _raise_on_error(lfs_file_seek(&fs._impl, &fh._impl, off, whence))


def file_truncate(LFSFilesystem fs, LFSFile fh, size):
    return _raise_on_error(lfs_file_truncate(&fs._impl, &fh._impl, size))


def file_tell(LFSFilesystem fs, LFSFile fh):
    return _raise_on_error(lfs_file_tell(&fs._impl, &fh._impl))


def file_rewind(LFSFilesystem fs, LFSFile fh):
    return _raise_on_error(lfs_file_rewind(&fs._impl, &fh._impl))


def file_size(LFSFilesystem fs, LFSFile fh):
    return _raise_on_error(lfs_file_size(&fs._impl, &fh._impl))

def mkdir(LFSFilesystem fs, path):
    return _raise_on_error(lfs_mkdir(&fs._impl, path.encode(FILENAME_ENCODING)))

def dir_open(LFSFilesystem fs, path):
    handle = LFSDirectory()
    _raise_on_error(lfs_dir_open(&fs._impl, &handle._impl, path.encode(FILENAME_ENCODING)))
    return handle

def dir_close(LFSFilesystem fs, LFSDirectory dh):
    return _raise_on_error(lfs_dir_close(&fs._impl, &dh._impl))

def dir_read(LFSFilesystem fs, LFSDirectory dh):
    cdef lfs_info * info = <lfs_info *>malloc(sizeof(lfs_info))
    try:
        retval = _raise_on_error(lfs_dir_read(&fs._impl, &dh._impl, info))
        if retval == 0:
            return None
        return LFSStat(info.type, info.size, info.name.decode(FILENAME_ENCODING))
    finally:
        free(info)

def dir_tell(LFSFilesystem fs, LFSDirectory dh):
    return _raise_on_error(lfs_dir_tell(&fs._impl, &dh._impl))

def dir_rewind(LFSFilesystem fs, LFSDirectory dh):
    return _raise_on_error(lfs_dir_rewind(&fs._impl, &dh._impl))

