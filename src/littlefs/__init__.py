import io
import warnings
from typing import TYPE_CHECKING, List, Tuple, Iterator, IO

from pkg_resources import DistributionNotFound, get_distribution

from . import errors, lfs
from .lfs import __LFS_DISK_VERSION__, __LFS_VERSION__
from .errors import LittleFSError


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

    def open(
        self,
        fname: str,
        mode='r',
        buffering: int = -1,
        encoding: str = None,
        errors: str = None,
        newline: str = None
    ) -> IO:
        """Open a file.

        :attr:`mode` is an optional string that specifies the mode in which
        the file is opened and is analogous to the built-in :func:`io.open`
        function. Files opened in text mode (default) will take and return
        `str` objects. Files opened in binary mode will take and return
        byte-like objects.

        Parameters
        ----------
        fname : str
            The path to the file to open.
        mode : str
            Specifies the mode in which the file is opened.
        buffering : int
            Specifies the buffering policy. Pass `0` to disable buffering in
            binary mode.
        encoding : str
            Text encoding to use. (text mode only)
        errors : str
            Specifies how encoding and decoding errors are to be handled. (text mode only)
        newline : str
            Controls how universal newlines mode works. (text mode only)
        """

        # Parse mode
        creating = False
        reading = False
        writing = False
        appending = False
        updating = False

        binary = False
        text = False

        for ch in mode:
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
            elif ch == "b":
                binary = True
            elif ch == "t":
                text = True
            else:
                raise ValueError(f"invalid mode: '{mode}'")

        if text and binary:
            raise ValueError("can't have text and binary mode at once")

        exclusive_modes = (creating, reading, writing, appending)

        if sum(int(m) for m in exclusive_modes) > 1:
            raise ValueError(
                "must have exactly one of create/read/write/append mode"
            )

        if binary:
            if encoding is not None:
                raise ValueError(
                    "binary mode doesn't take an encoding argument"
                )

            if errors is not None:
                raise ValueError(
                    "binary mode doesn't take an errors argument"
                )

            if newline is not None:
                raise ValueError(
                    "binary mode doesn't take a newline argument"
                )

            if buffering == 1:
                msg = (
                    "line buffering (buffering=1) isn't supported in "
                    "binary mode, the default buffer size will be used"
                )
                warnings.warn(msg, RuntimeWarning)
                buffering = -1

        try:
            fh = lfs.file_open(self.fs, fname, mode)
        except LittleFSError as e:
            # Try to map to standard Python exceptions
            if e.code == LittleFSError.Error.LFS_ERR_NOENT:
                raise FileNotFoundError from e
            elif e.code == LittleFSError.Error.LFS_ERR_ISDIR:
                raise IsADirectoryError from e
            elif e.code == LittleFSError.Error.LFS_ERR_EXIST:
                raise FileExistsError from e
            else:
                raise e

        raw = FileHandle(self.fs, fh)

        line_buffering = False

        if buffering == 1:
            buffering = -1
            line_buffering = True

        if buffering < 0:
            buffering = self.cfg.cache_size

        if buffering == 0:
            if not binary:
                raise ValueError("can't have unbuffered text I/O")

            return raw

        if updating:
            buffered = io.BufferedRandom(raw, buffering)
        elif creating or writing or appending:
            buffered = io.BufferedWriter(raw, buffering)
        elif reading:
            buffered = io.BufferedReader(raw, buffering)
        else:
            raise ValueError(f"Unknown mode: '{mode}'")

        if binary:
            return buffered

        wrapped = io.TextIOWrapper(
            buffered,
            encoding,
            errors,
            newline,
            line_buffering
        )

        return wrapped

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
        - A list of directorys located in the root
        - A list of filenames located in the root

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


class FileHandle(io.RawIOBase):
    def __init__(self, fs, fh):
        super().__init__()

        self.fs = fs
        self.fh = fh

    def close(self):
        # Base implementation is not used to avoid extra call to flush().
        # LittleFS already flushes the file on close.

        if not self.closed:
            lfs.file_close(self.fs, self.fh)
            setattr(self, "__IOBase_closed", True)

    def readable(self):
        return lfs.LFSFileFlag.rdonly in self.fh.flags and not self.closed

    def writable(self):
        return lfs.LFSFileFlag.wronly in self.fh.flags and not self.closed

    def seekable(self):
        self._checkClosed()
        return True

    def seek(self, offset, whence=io.SEEK_SET):
        # Whence constants are reused from the io module. The constants have
        # the same as LFS_SEEK_SET / LFS_SEEK_CUR / LFS_SEEK_END.
        self._checkClosed()
        return lfs.file_seek(self.fs, self.fh, offset, whence)

    def tell(self):
        self._checkClosed()
        return lfs.file_tell(self.fs, self.fh)

    def truncate(self, size=None) -> int:
        self._checkClosed()

        pos = self.tell()
        ret = lfs.file_truncate(self.fs, pos)

        return ret

    def write(self, data):
        self._checkClosed()
        self._checkWritable()

        return lfs.file_write(self.fs, self.fh, bytes(data))

    def readinto(self, b):
        self._checkClosed()
        self._checkReadable()

        req_len = len(b)
        result = lfs.file_read(self.fs, self.fh, req_len)
        res_len = len(result)

        b[0:res_len] = result

        return res_len

    def readall(self):
        self._checkClosed()
        self._checkReadable()

        file_size = lfs.file_size(self.fs, self.fh)
        file_pos = self.tell()
        size = file_size - file_pos

        return lfs.file_read(self.fs, self.fh, size)

    def flush(self):
        super().flush()
        lfs.file_sync(self.fs, self.fh)
