"""
Declarations for littlefs

This file imports and defines all external types and functions
required by the wrapper. This includes some standard types and functions
from the standard c library as well as the complete interface to
the littlefs implementation
"""

from libc.stdint cimport uint8_t, int32_t, uint32_t
from libc.stdlib cimport malloc, free
from libc.string cimport memcpy


cdef extern from "lfs.h":

    # Import #defined version information
    cdef const int LFS_VERSION
    cdef const int LFS_VERSION_MAJOR
    cdef const int LFS_VERSION_MINOR

    cdef const int LFS_DISK_VERSION
    cdef const int LFS_DISK_VERSION_MAJOR
    cdef const int LFS_DISK_VERSION_MINOR

    cdef const int LFS_NAME_MAX

    cdef const int LFS_ATTR_MAX


    # Basic type definitions
    ctypedef uint32_t lfs_size_t
    ctypedef uint32_t lfs_off_t

    ctypedef int32_t  lfs_ssize_t
    ctypedef int32_t  lfs_soff_t

    ctypedef uint32_t lfs_block_t

    # Enumerations
    cdef enum lfs_open_flags:
        LFS_O_RDONLY = 1         # Open a file as read only
        LFS_O_WRONLY = 2         # Open a file as write only
        LFS_O_RDWR   = 3         # Open a file as read and write
        LFS_O_CREAT  = 0x0100    # Create a file if it does not exist
        LFS_O_EXCL   = 0x0200    # Fail if a file already exists
        LFS_O_TRUNC  = 0x0400    # Truncate the existing file to zero size
        LFS_O_APPEND = 0x0800    # Move to end of file on every write

        # internally used flags
        LFS_F_DIRTY   = 0x010000 # File does not match storage
        LFS_F_WRITING = 0x020000 # File has been written since last flush
        LFS_F_READING = 0x040000 # File has been read since last flush
        LFS_F_ERRED   = 0x080000 # An error occurred during write
        LFS_F_INLINE  = 0x100000 # Currently inlined in directory entry
        LFS_F_OPENED  = 0x200000 # File has been opened

    cdef enum lfs_type:
        # littlefs-python: Only exporting public values for now.
        LFS_TYPE_REG = 0x001
        LFS_TYPE_DIR = 0x002

    cdef struct lfs:
        lfs_size_t block_count

    ctypedef lfs lfs_t

    cdef struct lfs_info:
        uint8_t type
        lfs_size_t size
        char name[LFS_NAME_MAX+1]

    cdef struct lfs_fsinfo:
        uint32_t disk_version
        lfs_size_t name_max
        lfs_size_t file_max
        lfs_size_t attr_max
        lfs_size_t block_count
        lfs_size_t block_size

    cdef struct lfs_dir:
        pass

    ctypedef lfs_dir lfs_dir_t

    cdef struct lfs_file:
        uint32_t flags

    ctypedef lfs_file lfs_file_t

    cdef struct lfs_file_config:
        pass

    cdef struct lfs_config:
        void * context
        int (*read)(const lfs_config *c, lfs_block_t block,
                    lfs_off_t off, void *buffer, lfs_size_t size)

        int (*prog)(const lfs_config *c, lfs_block_t block,
                    lfs_off_t off, const void *buffer, lfs_size_t size)

        int (*erase)(const lfs_config *c, lfs_block_t block)

        int (*sync)(const lfs_config *c)

        lfs_size_t read_size
        lfs_size_t prog_size
        lfs_size_t block_size
        lfs_size_t block_count
        int32_t block_cycles
        lfs_size_t cache_size
        lfs_size_t lookahead_size
        void *read_buffer
        void *prog_buffer
        void *lookahead_buffer
        lfs_size_t name_max
        lfs_size_t file_max
        lfs_size_t attr_max
        lfs_size_t metadata_max
        uint32_t disk_version

    int lfs_mount(lfs_t *lfs, const lfs_config *config)
    int lfs_format(lfs_t *lfs, const lfs_config *config)
    int lfs_unmount(lfs_t *lfs)

    int lfs_remove(lfs_t *lfs, const char *path)
    int lfs_rename(lfs_t *lfs, const char *oldpath, const char *newpath)
    int lfs_stat(lfs_t *lfs, const char *path,  lfs_info *info)

    lfs_ssize_t lfs_getattr(lfs_t *lfs, const char *path,
                            uint8_t type, void *buffer, lfs_size_t size)

    int lfs_setattr(lfs_t *lfs, const char *path,
                    uint8_t type, const void *buffer, lfs_size_t size)

    int lfs_removeattr(lfs_t *lfs, const char *path, uint8_t type)

    int lfs_file_open(lfs_t *lfs, lfs_file_t *file,
                      const char *path, int flags)

    int lfs_file_opencfg(lfs_t *lfs, lfs_file_t *file,
                         const char *path, int flags,
                         const  lfs_file_config *config)

    int lfs_file_close(lfs_t *lfs, lfs_file_t *file)

    int lfs_file_sync(lfs_t *lfs, lfs_file_t *file)

    lfs_ssize_t lfs_file_read(lfs_t *lfs, lfs_file_t *file,
                              void *buffer, lfs_size_t size)
    lfs_ssize_t lfs_file_write(lfs_t *lfs, lfs_file_t *file,
                               const void *buffer, lfs_size_t size)
    lfs_soff_t lfs_file_seek(lfs_t *lfs, lfs_file_t *file,
                             lfs_soff_t off, int whence)
    int lfs_file_truncate(lfs_t *lfs, lfs_file_t *file, lfs_off_t size)
    lfs_soff_t lfs_file_tell(lfs_t *lfs, lfs_file_t *file)
    int lfs_file_rewind(lfs_t *lfs, lfs_file_t *file)
    lfs_soff_t lfs_file_size(lfs_t *lfs, lfs_file_t *file)
    int lfs_mkdir(lfs_t *lfs, const char *path)
    int lfs_dir_open(lfs_t *lfs, lfs_dir *dir, const char *path)
    int lfs_dir_close(lfs_t *lfs, lfs_dir *dir)
    int lfs_dir_read(lfs_t *lfs, lfs_dir *dir,  lfs_info *info)
    int lfs_dir_seek(lfs_t *lfs, lfs_dir *dir, lfs_off_t off)
    lfs_soff_t lfs_dir_tell(lfs_t *lfs, lfs_dir *dir)
    int lfs_dir_rewind(lfs_t *lfs, lfs_dir *dir)
    int lfs_fs_stat(lfs_t *lfs, lfs_fsinfo* info)
    lfs_ssize_t lfs_fs_size(lfs_t *lfs)
    int lfs_fs_traverse(lfs_t *lfs, int (*cb)(void*, lfs_block_t), void *data)
    int lfs_fs_mkconsistent(lfs_t *lfs)
    int lfs_fs_grow(lfs_t *lfs, lfs_size_t block_count);
    int lfs_fs_gc(lfs_t *lfs)
