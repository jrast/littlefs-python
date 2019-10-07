from pkg_resources import get_distribution, DistributionNotFound
try:
    __version__ = get_distribution('littlefs-python').version
except DistributionNotFound:
    # Package not installed
    pass


from .lfs import __LFS_DISK_VERSION__, __LFS_VERSION__
from . import lfs
from . import errors


class LittleFS:
    """Littlefs file system"""

    def __init__(self, context=None, **kwargs):

        self.cfg = lfs.LFSConfig(**kwargs)
        self.fs = lfs.LFSFilesystem()

        if kwargs.get('mount', True):
            try:
                self.mount()
            except errors.LittleFSError:
                self.format()
                self.mount()

    @property
    def context(self):
        return self.cfg.user_context

    def format(self):
        """Format the underlying buffer"""
        return lfs.format(self.fs, self.cfg)

    def mount(self):
        """Mount the underlying buffer"""
        return lfs.mount(self.fs, self.cfg)

    def open(self, fname, mode='r'):
        """Open a file"""
        fh = lfs.file_open(self.fs, fname, mode)
        return FileHandle(self.fs, fh)

    def listdir(self, path='.'):
        """List directory content"""
        dh = lfs.dir_open(self.fs, path)
        info = lfs.dir_read(self.fs, dh)
        lst = []
        while info:
            if info.name not in ['.', '..']:
                lst.append(info.name)
            info = lfs.dir_read(self.fs, dh)
        lfs.dir_close(self.fs, dh)
        return lst

    def mkdir(self, path):
        """Create a new directory"""
        try:
            return lfs.mkdir(self.fs, path)
        except errors.LittleFSError as e:
            if e.code == -17:
                msg = "[LittleFSError {:d}] Cannot create a file when that file already exists: '{:s}'.".format(
                    e.code, path
                )
                raise FileExistsError(msg) from e
            raise

    def makedirs(self, name, exist_ok=False):
        raise NotImplementedError

    def remove(self, path):
        """Remove a file or directory

        If the path to remove is a directory, the directory must be empty.

        Parameters
        ----------
        path : str
            The path to the file or directory to remove.
        """
        return lfs.remove(self.fs, path)

    def removedirs(self, name):
        """Remove directories recursively

        This works like :func:`remove` but if the leaf directory
        is empty after the successfull removal of :attr:`name`, the
        function tries to recursively remove all parent directories
        which are also empty.
        """
        raise NotImplementedError

    def rename(self, src, dst):
        return lfs.rename(self.fs, src, dst)

    def replace(self, src, dst):
        raise NotImplementedError

    def rmdir(self, path):
        raise NotImplementedError

    def scandir(self, path):
        raise NotImplementedError

    def stat(self, path):
        return lfs.stat(self.fs, path)

    def sync(self):
        return lfs.sync(self.fs)

    def truncate(self, path, length):
        raise NotImplementedError

    def unlink(self, path):
        """Remove a file or directory

        This function is an alias for :func:`remove`.
        """
        return self.remove(path)

    def walk(self, top):
        raise NotImplementedError




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



