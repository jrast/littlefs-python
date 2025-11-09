from __future__ import annotations

import cmd
import posixpath
import shlex
import sys
from pathlib import Path
from typing import BinaryIO

from littlefs import LittleFS, LFSStat


class LittleFSRepl(cmd.Cmd):
    """Interactive shell for inspecting a LittleFS volume via the provided filesystem object."""

    prompt = "littlefs> "

    def __init__(self, fs: LittleFS) -> None:
        """Initialize the shell with a LittleFS handle."""
        super().__init__()
        self._fs = fs
        self._mounted = False
        self._cwd = "/"

    def onecmd(self, line: str) -> bool:
        """Dispatch a command while converting unexpected errors to readable messages."""
        try:
            return super().onecmd(line)
        except Exception as exc:  # noqa: BLE001
            print(f"{exc.__class__.__name__}: {exc}")
            return False

    def _ensure_mounted(self) -> None:
        """Raise if the remote filesystem is not mounted yet."""
        if not self._mounted:
            raise RuntimeError("Filesystem is not mounted. Run 'mount' first.")

    def _resolve_path(self, raw_path: str | None) -> str:
        """Normalize local CLI paths into absolute LittleFS paths."""
        candidate = raw_path.strip() if raw_path and raw_path.strip() else self._cwd
        if not candidate.startswith("/"):
            candidate = posixpath.join(self._cwd, candidate)
        normalized = posixpath.normpath(candidate)
        return "/" if normalized in ("", ".") else normalized

    def _resolve_remote_destination(self, raw_path: str, basename: str) -> str:
        """Return the full remote destination path, adding basename when needed."""
        if not raw_path:
            # Put in root
            return self._resolve_path(basename)

        if raw_path.endswith("/"):
            # Remote ends with a slash, attach name
            return self._resolve_path(posixpath.join(raw_path, basename))

        # Full filepath provided
        return self._resolve_path(raw_path)

    @staticmethod
    def _copy_stream(src: BinaryIO, dst: BinaryIO) -> None:
        """Copy data from src to dst in small chunks."""
        while True:
            chunk = src.read(16 * 1024)
            if not chunk:
                break
            dst.write(chunk)

    def do_mount(self, _: str = "") -> None:
        """Attempt to mount the remote filesystem."""
        if self._mounted:
            raise RuntimeError("Filesystem already mounted.")
        self._fs.mount()
        self._mounted = True
        self._cwd = "/"
        print("Mounted remote littlefs.")

    def do_unmount(self, _: str = "") -> None:
        """Unmount the remote filesystem."""
        if not self._mounted:
            raise RuntimeError("Filesystem already unmounted.")
        self._fs.unmount()
        self._mounted = False
        self._cwd = "/"
        print("Unmounted remote littlefs.")

    def do_ls(self, line: str = "") -> None:
        """List directory contents for the provided path."""
        self._ensure_mounted()
        target = self._resolve_path(line)
        entries = self._fs.listdir(target)
        for fname in entries:
            print(fname)

    def do_dir(self, line: str = "") -> None:
        """Alias for ls (Windows muscle memory)."""
        self.do_ls(line)

    def do_cd(self, line: str = "") -> None:
        """Change the current working directory."""
        self._ensure_mounted()
        target = "/" if not line.strip() else self._resolve_path(line)
        stat = self._fs.stat(target)
        if stat.type != LFSStat.TYPE_DIR:
            raise NotADirectoryError(f"Not a directory: {target}")
        self._cwd = target
        print(self._cwd)

    def do_pwd(self, _: str = "") -> None:
        """Print the current working directory."""
        self._ensure_mounted()
        print(self._cwd)

    def do_tree(self, line: str = "") -> None:
        """Print the directory tree rooted at the provided path."""
        self._ensure_mounted()
        root = self._resolve_path(line)
        print(root)
        self._print_tree(root, "")

    def _print_tree(self, path: str, prefix: str) -> None:
        """Recursive helper for do_tree that renders a tree view."""
        entries = sorted(self._fs.listdir(path))
        for idx, name in enumerate(entries):
            child = posixpath.join(path, name)
            stat = self._fs.stat(child)

            is_dir = stat.type == LFSStat.TYPE_DIR
            connector = "`-- " if idx == len(entries) - 1 else "|-- "
            label = f"{name}/" if is_dir else name
            print(f"{prefix}{connector}{label}")
            if is_dir:
                extension = "    " if idx == len(entries) - 1 else "|   "
                self._print_tree(child, prefix + extension)

    def do_put(self, line: str) -> None:
        """Copy a local file to the LittleFS volume."""
        self._ensure_mounted()
        args = shlex.split(line)
        if not args:
            raise ValueError("Usage: put <local_path> [remote_path]")

        local_path = Path(args[0]).expanduser()
        if not local_path.is_file():
            raise FileNotFoundError(f"Local file not found: {local_path}")

        remote_arg = args[1] if len(args) > 1 else None
        remote_target = self._resolve_remote_destination(remote_arg or "", local_path.name)
        parent = posixpath.dirname(remote_target)

        if parent and parent != "/":
            self._fs.makedirs(parent, exist_ok=True)

        with open(local_path, "rb") as src, self._fs.open(remote_target, "wb") as dst:
            self._copy_stream(src, dst)

        print(f"Put {local_path} -> {remote_target}")

    def do_get(self, line: str) -> None:
        """Copy a remote file from the LittleFS volume to the host."""
        self._ensure_mounted()
        args = shlex.split(line)
        if not args:
            raise ValueError("Usage: get <remote_path> [local_path]")
        remote_path = self._resolve_path(args[0])
        local_arg = args[1] if len(args) > 1 else None
        remote_name = Path(remote_path).name or "download.bin"
        local_path = self._resolve_local_destination(local_arg, remote_name)
        if local_path.parent and not local_path.parent.exists():
            local_path.parent.mkdir(parents=True, exist_ok=True)
        with self._fs.open(remote_path, "rb") as src, open(local_path, "wb") as dst:
            self._copy_stream(src, dst)
        print(f"Got {remote_path} -> {local_path}")

    def do_cat(self, line: str = "") -> None:
        """Print the contents of a remote file to stdout."""
        self._ensure_mounted()
        args = shlex.split(line)
        if not args:
            raise ValueError("Usage: cat <remote_path>")
        remote_path = self._resolve_path(args[0])
        with self._fs.open(remote_path, "rb") as src:
            self._copy_stream(src, sys.stdout.buffer)
        sys.stdout.buffer.flush()

    def do_xxd(self, line: str = "") -> None:
        """Show a hexadecimal dump of a remote file."""
        self._ensure_mounted()
        args = shlex.split(line)
        if not args:
            raise ValueError("Usage: xxd <remote_path>")

        remote_path = self._resolve_path(args[0])
        offset = 0
        with self._fs.open(remote_path, "rb") as src:
            while True:
                chunk = src.read(16)
                if not chunk:
                    break
                hex_pairs = [f"{byte:02x}" for byte in chunk]
                first_half = " ".join(hex_pairs[:8])
                second_half = " ".join(hex_pairs[8:])
                hex_line = f"{first_half:<23} {second_half:<23}".rstrip()
                ascii_line = "".join(chr(b) if 32 <= b < 127 else "." for b in chunk)
                print(f"{offset:08x}: {hex_line:<48}  {ascii_line}")
                offset += len(chunk)

    def do_mkdir(self, line: str) -> None:
        """Create a directory (use -p to create parents)."""
        self._ensure_mounted()
        args = shlex.split(line)
        if not args:
            raise ValueError("Usage: mkdir [-p] <remote_path>")
        recursive = False
        target_arg = args[0]
        if args[0] == "-p":
            if len(args) < 2:
                raise ValueError("Usage: mkdir [-p] <remote_path>")
            recursive = True
            target_arg = args[1]
        target = self._resolve_path(target_arg)
        if recursive:
            self._fs.makedirs(target, exist_ok=True)
        else:
            self._fs.mkdir(target)
        print(f"Created directory {target}")

    def do_mv(self, line: str) -> None:
        """Rename or move a file or directory."""
        self._ensure_mounted()
        args = shlex.split(line)
        if len(args) != 2:
            raise ValueError("Usage: mv <source> <destination>")
        src = self._resolve_path(args[0])
        dst = self._resolve_path(args[1])
        self._fs.rename(src, dst)
        if self._cwd == src:
            self._cwd = dst
        elif self._cwd.startswith(f"{src}/"):
            suffix = self._cwd[len(src) :]
            self._cwd = posixpath.normpath(f"{dst}{suffix}")
        print(f"Moved {src} -> {dst}")

    def do_rm(self, line: str) -> None:
        """Remove a file or directory (use -r for recursive removal)."""
        self._ensure_mounted()
        args = shlex.split(line)
        if not args:
            raise ValueError("Usage: rm [-r] <path>")
        recursive = False
        target_arg = args[0]
        if args[0] == "-r":
            if len(args) < 2:
                raise ValueError("Usage: rm [-r] <path>")
            recursive = True
            target_arg = args[1]
        target = self._resolve_path(target_arg)
        self._fs.remove(target, recursive=recursive)
        print(f"Removed {target}")

    def _resolve_local_destination(self, raw_path: str | None, remote_name: str) -> Path:
        """Determine the local path where a remote file should be stored."""
        if not raw_path:
            # Filename only
            return Path(remote_name)

        expanded = Path(raw_path).expanduser()
        if raw_path.endswith(("/", "\\")) or expanded.is_dir():
            return expanded / remote_name

        return expanded

    def do_exit(self, _):
        """Exit the CLI session."""
        return True

    def default(self, line: str):
        """Handle EOF shortcuts or fall back to cmd.Cmd implementation."""
        if line == "EOF":
            print()
            return self.do_exit(line)
        return super().default(line)
