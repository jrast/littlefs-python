from typing import TYPE_CHECKING, List, Tuple, Optional, Iterator

from pkg_resources import DistributionNotFound, get_distribution

from . import errors, lfs
from .lfs import __LFS_DISK_VERSION__, __LFS_VERSION__

try:
    __version__ = get_distribution('littlefs-python').version
except DistributionNotFound:
    # Package not installed
    pass

if TYPE_CHECKING:
    from .context import UserContext
    from .lfs import LFSStat

class LittleFS:
    """Littlefs file system"""

    def __init__(self, context:'UserContext'=None, **kwargs) -> None:

        self.cfg = lfs.LFSConfig(context=context, **kwargs)
        self.fs = lfs.LFSFilesystem()

        if kwargs.get('mount', True):
            try:
                self.mount()
            except errors.LittleFSError:
                self.format()
                self.mount()

    @property
    def context(self) -> 'UserContext':
        """User context of the file system"""
        return self.cfg.user_context

    def format(self) -> int:
        """Format the underlying buffer"""
        return lfs.format(self.fs, self.cfg)

    def mount(self) -> int:
        """Mount the underlying buffer"""
        return lfs.mount(self.fs, self.cfg)

    def open(self, fname: str, mode='r') -> 'FileHandle':
        """Open a file"""
        fh = lfs.file_open(self.fs, fname, mode)
        return FileHandle(self.fs, fh)

    def listdir(self, path='.') -> List[str]:
        """List directory content
        
        List the content of a directory. This function uses :meth:`scandir`
        internally. Using :meth:`scandir` might be better if you are
        searching for a specific file or need access to the :class:`littlefs.lfs.LFSStat`
        of the files.
        """
        return [st.name for st in self.scandir(path)]

    def mkdir(self, path: str) -> int:
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

    def makedirs(self, name: str, exist_ok=False):
        """Recursive directory creation function."""
        parts = [p for p in name.split('/') if p]
        current_name = ''
        for nr, part in enumerate(parts):
            current_name += '/%s' % part
            try:
                self.mkdir(current_name)
            except FileExistsError as e:
                is_last = nr == len(parts) - 1
                if (not is_last) or (is_last and exist_ok):
                    continue
                raise e

    def remove(self, path: str) -> int:
        """Remove a file or directory

        If the path to remove is a directory, the directory must be empty.

        Parameters
        ----------
        path : str
            The path to the file or directory to remove.
        """
        try:
            return lfs.remove(self.fs, path)
        except errors.LittleFSError as e:
            if e.code == -2:
                msg = "[LittleFSError {:d}] No such file or directory: '{:s}'.".format(
                    e.code, path
                )
                raise FileNotFoundError(msg) from e
            raise e

    def removedirs(self, name):
        """Remove directories recursively

        This works like :func:`remove` but if the leaf directory
        is empty after the successfull removal of :attr:`name`, the
        function tries to recursively remove all parent directories
        which are also empty.
        """
        parts = name.split('/')
        while parts:
            try:
                name = '/'.join(parts)
                if not name:
                    break
                self.remove('/'.join(parts))
            except errors.LittleFSError as e:
                if e.code == -39:
                    break
                raise e
            parts.pop()

    def rename(self, src: str, dst: str) -> int:
        """Rename a file or directory"""
        return lfs.rename(self.fs, src, dst)

    def rmdir(self, path: str) -> int:
        """Remove a directory

        This function is an alias for :func:`remove`
        """
        return self.remove(path)

    def scandir(self, path='.') -> Iterator['LFSStat']:
        """List directory content"""
        dh = lfs.dir_open(self.fs, path)
        info = lfs.dir_read(self.fs, dh)
        while info:
            if info.name not in ['.', '..']:
                yield info
            info = lfs.dir_read(self.fs, dh)
        lfs.dir_close(self.fs, dh)

    def stat(self, path: str) -> 'LFSStat':
        """Get the status of a file or directory"""
        return lfs.stat(self.fs, path)

    def unlink(self, path: str) -> int:
        """Remove a file or directory

        This function is an alias for :func:`remove`.
        """
        return self.remove(path)

    def walk(self, top: str) -> Iterator[Tuple[str, List[str], List[str]]]:
        """Generate the file names in a directory tree

        Generate the file and directory names in a directory tree by
        walking the tree top-down. This functions closely resembels the 
        behaviour of :func:`os.stat`.

        Each iteration yields a tuple containing three elements:

        - The root of the currently processed element
        - A list of filenames located in the root
        - A list of directorys located in the root

        """
        files = []
        dirs = []
        from os import walk
        for elem in self.scandir(top):
            if elem.type == 1:
                files.append(elem.name)
            elif elem.type == 2:
                dirs.append(elem.name)
        
        yield top, dirs, files
        for dirname in dirs:
            newtop = '/'.join((top, dirname)).replace('//', '/')
            yield from self.walk(newtop)



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
