from pkg_resources import get_distribution, DistributionNotFound
try:
    __version__ = get_distribution('littlefs-python').version
except DistributionNotFound:
    # Package not installed
    pass


from .lfs import __LFS_DISK_VERSION__, __LFS_VERSION__
from . import lfs


class LittleFS:
    """Littlefs file system"""
    
    FILENAME_ENCODING = 'ascii'
    """Encoding used for file and directory names"""

    def __init__(self, context=None, **kwargs):

        self.cfg = lfs.LFSConfig(**kwargs)
        self.fs = lfs.LFSFilesystem()

        if kwargs.get('mount', True):
            try:
                self.mount()
            except errors.LittleFSException:
                self.format()
                self.mount()

    @property
    def context(self):
        return self.cfg.user_context

    def format(self):
        return lfs.format(self.fs, self.cfg)

    def mount(self):
        return lfs.mount(self.fs, self.cfg)

    def open(self, fname, mode='r'):
        fh = lfs.file_open(self.fs, fname, mode)
        return FileHandle(self.fs, fh)


class FileHandle:

    def __init__(self, fs, fh):
        self.fs = fs
        self.fh = fh

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()

    def write(self, data):
        return lfs.file_write(self.fs, self.fh, data)

    def read(self, size):
        return lfs.file_read(self.fs, self.fh, size)

    def close(self):
        lfs.file_close(self.fs, self.fh)



