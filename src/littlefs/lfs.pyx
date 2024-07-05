import logging
import enum
from typing import NamedTuple
# Import all definitions
# from littlefs._lfs cimport *

from littlefs.context import UserContext
from littlefs import errors


FILENAME_ENCODING = 'ascii'
"""Default filename encoding"""

class LFSStat(NamedTuple):
    """Littlefs File / Directory status."""
    type: int
    size: int
    name: str

    # Constants
    TYPE_REG = LFS_TYPE_REG
    TYPE_DIR = LFS_TYPE_DIR


class LFSFSStat(NamedTuple):
    """Littlefs filesystem status."""
    disk_version: int
    name_max: int
    file_max: int
    attr_max: int
    block_count: int
    block_size: int


class LFSFileFlag(enum.IntFlag):
    """Littlefs file mode flags"""
    rdonly = LFS_O_RDONLY
    wronly = LFS_O_WRONLY
    rdwr = LFS_O_RDWR
    creat = LFS_O_CREAT
    excl = LFS_O_EXCL
    trunc = LFS_O_TRUNC
    append = LFS_O_APPEND


# Export LFS version and disk version to python
__LFS_VERSION__ = (LFS_VERSION_MAJOR, LFS_VERSION_MINOR)
__LFS_DISK_VERSION__ = (LFS_DISK_VERSION_MAJOR, LFS_DISK_VERSION_MINOR)


cdef int _lfs_read(const lfs_config *c, lfs_block_t block, lfs_off_t off, void * buffer, lfs_size_t size) noexcept:
    ctx = <object>c.context
    data = ctx.user_context.read(ctx, block, off, size)
    memcpy(buffer, <char *>data, size)
    return 0


cdef int _lfs_prog(const lfs_config *c, lfs_block_t block, lfs_off_t off, const void * buffer, lfs_size_t size) noexcept:
    ctx = <object>c.context
    data = (<char*>buffer)[:size]
    return ctx.user_context.prog(ctx, block, off, data)


cdef int _lfs_erase(const lfs_config *c, lfs_block_t block) noexcept:
    ctx = <object>c.context
    return ctx.user_context.erase(ctx, block)


cdef int _lfs_sync(const lfs_config *c) noexcept:
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


    def __init__(self,
                 context=None,
                 *,
                 block_size: int = 128,
                 block_count: int = 64,
                 read_size: int = 0,
                 prog_size: int = 0,
                 block_cycles: int = -1,
                 cache_size: int = 0,
                 lookahead_size: int = 8,
                 name_max: int = 255,
                 file_max: int = 0,
                 attr_max: int = 0,
                 metadata_max: int = 0,
                 disk_version: int = 0,
                ):
        """LittleFS Configuration.

        If the block size and count is not given, create a
        small memory with minimal block size and 8KB size.

        Parameters
        ----------
        block_size : int
            Defaults to 128.
        block_count : int
            Number of blocks in the filesystem.
            If set to 0, attempt to autodetect ``block_count`` from filesystem.
            Defaults to 64.
        read_size: int
            Minimum size of a block read in bytes. All read operations will be a
            multiple of this value.
            Defaults to ``block_size``.
        prog_size: int
            Minimum size of a block program in bytes. All program operations will be
            a multiple of this value.
            Defaults to ``block_size``.
        block_cycles: int
            Number of erase cycles before littlefs evicts metadata logs and moves
            the metadata to another block. Suggested values are in the
            range 100-1000, with large values having better performance at the cost
            of less consistent wear distribution.
            Set to -1 to disable block-level wear-leveling.
            Defaults to -1 (disable block-level wear-leveling).
        cache_size:
            Size of block caches in bytes. Each cache buffers a portion of a block in
            RAM. The littlefs needs a read cache, a program cache, and one additional
            Defaults to ``read_size`` or ``prog_size``, whichever is larger.
        lookahead_size: int
            Size of the lookahead buffer in bytes. A larger lookahead buffer
            increases the number of blocks found during an allocation pass. The
            lookahead buffer is stored as a compact bitmap, so each byte of RAM
            can track 8 blocks. Must be a multiple of 8.
            Defaults to 8.
        name_max: int
            Defaults to 255 (LittleFS default).
        file_max: int
        attr_max: int
        metadata_max: int
        disk_version: int
        """

        if block_size < 128:
            raise ValueError('Minimal block size is 128')

        if name_max > 1022:  # LittleFS maximum name length limitation
            raise ValueError(f"name_max must be <=1022.")

        self._impl.read_size = read_size if read_size else block_size
        self._impl.prog_size = prog_size if prog_size else block_size
        self._impl.block_size = block_size
        self._impl.block_count = block_count
        self._impl.block_cycles = block_cycles
        # Cache size, at least as big as read / prog size
        self._impl.cache_size = cache_size if cache_size else max(self._impl.read_size, self._impl.prog_size)
        # Lookahead buffer size in bytes
        self._impl.lookahead_size = lookahead_size
        self._impl.name_max = name_max
        self._impl.file_max = file_max
        self._impl.attr_max = attr_max
        self._impl.metadata_max = metadata_max
        self._impl.disk_version = disk_version

        if context is None:
            context = UserContext(self._impl.block_size * self._impl.block_count)

        self.user_context = context
        self._impl.context = <void *>self

    def __repr__(self):
        args = (
            f"context={self.user_context!r}",
            f"block_size={self._impl.block_size}",
            f"block_count={self._impl.block_count}",
            f"read_size={self._impl.read_size}",
            f"prog_size={self._impl.prog_size}",
            f"block_cycles={self._impl.block_cycles}",
            f"cache_size={self._impl.cache_size}",
            f"lookahead_size={self._impl.lookahead_size}",
            f"name_max={self._impl.name_max}",
            f"file_max={self._impl.file_max}",
            f"attr_max={self._impl.attr_max}",
            f"metadata_max={self._impl.metadata_max}",
            f"disk_version={self._impl.disk_version}"
        )
        return f"{self.__class__.__name__}({', '.join(args)})"

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

    @property
    def name_max(self):
        return self._impl.name_max

    @property
    def file_max(self):
        return self._impl.file_max

    @property
    def attr_max(self):
        return self._impl.attr_max

    @property
    def metadata_max(self):
        return self._impl.metadata_max

    @property
    def disk_version(self):
        return self._impl.disk_version


cdef class LFSFilesystem:
    cdef lfs_t _impl

    @property
    def block_count(self) -> lfs_size_t:
        return self._impl.block_count


cdef class LFSFile:
    cdef lfs_file_t _impl

    @property
    def flags(self) -> LFSFileFlag:
        """Mode flags of an open file"""
        return LFSFileFlag(self._impl.flags)


cdef class LFSDirectory:
    cdef lfs_dir_t _impl


def fs_stat(LFSFilesystem fs):
    """Get filesystem status"""
    cdef lfs_fsinfo * info = <lfs_fsinfo *>malloc(sizeof(lfs_fsinfo))
    try:
        _raise_on_error(lfs_fs_stat(&fs._impl, info))
        return LFSFSStat(
            info.disk_version,
            info.name_max,
            info.file_max,
            info.attr_max,
            info.block_count,
            info.block_size,
        )
    finally:
        free(info)


def fs_size(LFSFilesystem fs):
    return _raise_on_error(lfs_fs_size(&fs._impl))

def fs_gc(LFSFilesystem fs):
    return _raise_on_error(lfs_fs_gc(&fs._impl))

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


def fs_mkconsistent(LFSFilesystem fs):
    """Attempt to make the filesystem consistent and ready for writing"""
    return _raise_on_error(lfs_fs_mkconsistent(&fs._impl))


def fs_grow(LFSFilesystem fs, block_count) -> int:
    """Irreversibly grows the filesystem to a new size.

    Parameters
    ----------
    fs: LFSFilesystem
    block_count: int
        Number of blocks in the new filesystem.
    """
    return _raise_on_error(lfs_fs_grow(&fs._impl, block_count))


def remove(LFSFilesystem fs, path):
    """Remove a file or directory

    If removing a directory, the directory must be empty.
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


def getattr(LFSFilesystem fs, path, typ):
    buf = bytearray(LFS_ATTR_MAX)
    cdef unsigned char[::1] buf_view = buf
    attr_size = _raise_on_error(lfs_getattr(&fs._impl, path.encode(FILENAME_ENCODING), typ, &buf_view[0], LFS_ATTR_MAX))
    return bytes(buf[:attr_size])


def setattr(LFSFilesystem fs, path, typ, data):
    cdef const unsigned char[::1] buf_view = data
    _raise_on_error(lfs_setattr(&fs._impl, path.encode(FILENAME_ENCODING), typ, &buf_view[0], len(data)))


def removeattr(LFSFilesystem fs, path, typ):
    _raise_on_error(lfs_removeattr(&fs._impl, path.encode(FILENAME_ENCODING), typ))


def file_open(LFSFilesystem fs, path, flags):
    if isinstance(flags, str):
        creating = False
        reading = False
        writing = False
        appending = False
        updating = False

        for ch in flags:
            if ch == "x":
                creating = True
            elif ch == "r":
                reading = True
            elif ch == "w":
                writing = True
            elif ch == "a":
                appending = True
            elif ch == "+":
                updating = True
            elif ch in ("t", "b"):
                # lfs_file_open() always opens files in binary mode.
                # Text decoding is done at a higher level.
                pass
            else:
                raise ValueError(f"invalid mode: '{flags}'")

        exclusive_modes = (creating, reading, writing, appending)

        if sum(int(m) for m in exclusive_modes) > 1:
            raise ValueError(
                "must have exactly one of create/read/write/append mode"
            )

        if creating:
            flags = LFSFileFlag.creat | LFSFileFlag.excl | LFSFileFlag.wronly
        elif reading:
            flags = LFSFileFlag.rdonly
        elif writing:
            flags = LFSFileFlag.creat | LFSFileFlag.wronly | LFSFileFlag.trunc
        elif appending:
            flags = LFSFileFlag.wronly | LFSFileFlag.append

        if updating:
            flags |= LFSFileFlag.rdwr

    flags = int(flags)
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
