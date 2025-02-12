import argparse
from contextlib import suppress
from pathlib import Path
import sys
import textwrap

from littlefs import LittleFS, __version__
from littlefs.errors import LittleFSError

# Dictionary mapping suffixes to their size in bytes
_suffix_map = {
    "kb": 1024,
    "mb": 1024**2,
    "gb": 1024**3,
}


def _fs_from_args(args: argparse.Namespace, mount=True) -> LittleFS:
    return LittleFS(
        block_size=args.block_size,
        block_count=getattr(args, "block_count", 0),
        name_max=args.name_max,
        mount=mount,
    )


def size_parser(size_str):
    """Parse filesystem / block size in different formats"""
    size_str = str(size_str).lower()

    # Check if the string starts with '0x', which indicates a hexadecimal number
    if size_str.startswith("0x"):
        base = 16
        size_str = size_str[2:]
    else:
        base = 10

    # Separate the size number and suffix
    for suffix, multiplier in _suffix_map.items():
        if size_str.endswith(suffix):
            num_part = size_str[: -len(suffix)]
            return int(num_part, base) * multiplier

    # Handle base units; remove base suffix
    if size_str.endswith("b"):
        size_str = size_str[:-1]

    # If no suffix, assume it's in bytes
    return int(size_str, base)


def create(parser: argparse.ArgumentParser, args: argparse.Namespace) -> int:
    """Create LittleFS image from file/directory contents."""
    # fs_size OR block_count may be populated; make them consistent.
    if args.block_count is None:
        block_count = args.fs_size // args.block_size
        if block_count * args.block_size != args.fs_size:
            parser.error("fs-size must be a multiple of block-size.")
        args.block_count = block_count
    else:
        args.fs_size = args.block_size * args.block_count

    if args.verbose:
        print("LittleFS Configuration:")
        print(f"  Block Size:  {args.block_size:9d}  /  0x{args.block_size:X}")
        print(f"  Image Size:  {args.fs_size:9d}  /  0x{args.fs_size:X}")
        print(f"  Block Count: {args.block_count:9d}")
        print(f"  Name Max:    {args.name_max:9d}")
        print(f"  Image:       {args.destination}")

    source = Path(args.source).absolute()
    if source.is_dir():
        sources = source.rglob("*")
        root = source
    else:
        sources = [source]
        root = source.parent

    fs = _fs_from_args(args)
    for path in sources:
        rel_path = path.relative_to(root)
        if path.is_dir():
            if args.verbose:
                print("Adding Directory:", rel_path)
            fs.mkdir(rel_path.as_posix())
        else:
            if args.verbose:
                print("Adding File:     ", rel_path)
            with fs.open(rel_path.as_posix(), "wb") as dest:
                dest.write(path.read_bytes())

    if args.compact:
        if args.verbose:
            print(f"Compacting... {fs.used_block_count} / {args.block_count}")
        compact_fs = LittleFS(
            block_size=args.block_size,
            block_count=fs.used_block_count,
            name_max=args.name_max,
        )
        for root, dirs, files in fs.walk("/"):
            if not root.endswith("/"):
                root += "/"
            for _dir in dirs:
                compact_fs.makedirs(root + _dir, exist_ok=True)
            for file in files:
                path = root + file
                print(path)
                with fs.open(path, "rb") as src, compact_fs.open(path, "wb") as dest:
                    dest.write(src.read())
        compact_fs.fs_grow(args.block_count)
        data = compact_fs.context.buffer
        if not args.no_pad:
            data = data.ljust(args.fs_size, b"\xFF")
    else:
        data = fs.context.buffer

    args.destination.parent.mkdir(exist_ok=True, parents=True)
    args.destination.write_bytes(data)
    return 0


def _list(parser: argparse.ArgumentParser, args: argparse.Namespace) -> int:
    """List LittleFS image contents."""
    fs = _fs_from_args(args, mount=False)
    fs.context.buffer = bytearray(args.source.read_bytes())
    fs.mount()

    if args.verbose:
        fs_size = len(fs.context.buffer)
        print("LittleFS Configuration:")
        print(f"  Block Size:  {args.block_size:9d}  /  0x{args.block_size:X}")
        print(f"  Image Size:  {fs_size:9d}  /  0x{fs_size:X}")
        print(f"  Block Count: {fs.block_count:9d}")
        print(f"  Name Max:    {args.name_max:9d}")
        print(f"  Image:       {args.source}")

    for root, dirs, files in fs.walk("/"):
        if not root.endswith("/"):
            root += "/"
        for dir in dirs:
            print(f"{root}{dir}")
        for file in files:
            print(f"{root}{file}")
    return 0


def extract(parser: argparse.ArgumentParser, args: argparse.Namespace) -> int:
    """Extract LittleFS image contents to a directory."""
    fs = _fs_from_args(args, mount=False)
    fs.context.buffer = bytearray(args.source.read_bytes())
    fs.mount()

    if args.verbose:
        fs_size = len(fs.context.buffer)
        print("LittleFS Configuration:")
        print(f"  Block Size:  {args.block_size:9d}  /  0x{args.block_size:X}")
        print(f"  Image Size:  {fs_size:9d}  /  0x{fs_size:X}")
        print(f"  Block Count: {fs.block_count:9d}")
        print(f"  Name Max:    {args.name_max:9d}")
        print(f"  Image:       {args.source}")

    root_dest = args.destination.absolute()
    if not root_dest.exists():
        root_dest.mkdir(parents=True)
    if not root_dest.is_dir():
        print("Destination must be a directory.")
        return 1

    for root, dirs, files in fs.walk("/"):
        if not root.endswith("/"):
            root += "/"
        for dir in dirs:
            src_path = root + dir
            dst_path = root_dest / src_path[1:]
            if args.verbose:
                print(src_path, dst_path)
            assert root_dest in dst_path.parents
            dst_path.mkdir(exist_ok=True)
        for file in files:
            src_path = root + file
            dst_path = root_dest / src_path[1:]
            if args.verbose:
                print(src_path, dst_path)
            assert root_dest in dst_path.parents
            with fs.open(src_path, "rb") as src:
                dst_path.write_bytes(src.read())

    return 0


def get_parser():
    if sys.argv[0].endswith("__main__.py"):
        prog = f"python -m littlefs"
    else:
        prog = f"littlefs-python"

    parser = argparse.ArgumentParser(
        prog=prog,
        description=textwrap.dedent(
            """\
            Create, extract and inspect LittleFS filesystem images. Use one of the
            commands listed below, the '-h' / '--help' option can be used on each
            command to learn more about the usage.
            """
        ),
        # formatter_class=argparse.RawTextHelpFormatter,
    )
    parser.add_argument("--version", action="version", version=__version__)

    common_parser = argparse.ArgumentParser(add_help=False)
    common_parser.add_argument("-v", "--verbose", action="count", default=0)
    common_parser.add_argument(
        "--name-max",
        type=size_parser,
        default=255,
        help="LittleFS max file path length. Defaults to LittleFS's default (255).",
    )

    subparsers = parser.add_subparsers(required=True, title="Available Commands", dest="command")

    def add_command(handler, name="", help=""):
        subparser = subparsers.add_parser(
            name or handler.__name__, parents=[common_parser], help=help or handler.__doc__
        )
        subparser.set_defaults(func=handler)
        return subparser

    parser_create = add_command(create)
    parser_create.add_argument(
        "source",
        type=Path,
        help="Source file/directory-of-files to encode into a littlefs filesystem.",
    )
    parser_create.add_argument(
        "destination",
        type=Path,
        nargs="?",
        default=Path("lfs.bin"),
        help="Output LittleFS filesystem binary image.",
    )
    parser_create.add_argument(
        "--block-size",
        type=size_parser,
        required=True,
        help="LittleFS block size.",
    )
    parser_create.add_argument(
        "--compact",
        action="store_true",
        help="Store all data in the beginning blocks.",
    )
    parser_create.add_argument(
        "--no-pad",
        action="store_true",
        help="Do not pad the binary to-size with 0xFF. Only valid with --compact.",
    )
    block_count_group = parser_create.add_mutually_exclusive_group(required=True)
    block_count_group.add_argument(
        "--block-count",
        type=int,
        help="LittleFS block count",
    )
    block_count_group.add_argument(
        "--fs-size",
        type=size_parser,
        help="LittleFS filesystem size. Accepts byte units; e.g. 1MB and 1048576 are equivalent.",
    )

    parser_extract = add_command(extract)
    parser_extract.add_argument(
        "source",
        type=Path,
        help="Source LittleFS filesystem binary.",
    )
    parser_extract.add_argument(
        "destination",
        default=Path("."),
        nargs="?",
        type=Path,
        help="Destination directory. Defaults to current directory.",
    )
    parser_extract.add_argument(
        "--block-size",
        type=size_parser,
        required=True,
        help="LittleFS block size.",
    )

    parser_list = add_command(_list, "list")
    parser_list.add_argument(
        "source",
        type=Path,
        help="Source LittleFS filesystem binary.",
    )
    parser_list.add_argument(
        "--block-size",
        type=size_parser,
        required=True,
        help="LittleFS block size.",
    )

    return parser


def main():
    parser = get_parser()
    parser.parse_known_args(sys.argv[1:])  # Allows for ``littlefs-python --version``
    args = parser.parse_args(sys.argv[1:])
    return args.func(parser, args)


if __name__ == "__main__":
    sys.exit(main())
