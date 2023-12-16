import argparse
import sys
import textwrap
import pathlib
from littlefs import LittleFS, __version__

# Dictionary mapping suffixes to their size in bytes
_suffix_map = {
    "kb": 1024,
    "mb": 1024**2,
    "gb": 1024**3,
}


def _fs_from_args(args: argparse.Namespace) -> LittleFS:
    return LittleFS(
        block_size=args.block_size,
        block_count=args.block_count,
        name_max=args.name_max,
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


def validate_args(parser: argparse.ArgumentParser, args: argparse.Namespace):
    if args.block_count is None:
        block_count = args.fs_size // args.block_size
        if block_count * args.block_size != args.fs_size:
            parser.error("fs-size must be a multiple of block-size.")
        args.block_count = block_count
    else:
        args.fs_size = args.block_size * args.block_count

    args.image = args.image.absolute()

    if args.verbose:
        print("LittleFS Configuration:")
        print(f"  Block Size:  {args.block_size:9d}  /  0x{args.block_size:X}")
        print(f"  Image Size:  {args.fs_size:9d}  /  0x{args.fs_size:X}")
        print(f"  Block Count: {args.block_count:9d}")
        print(f"  Name Max:    {args.name_max:9d}")
        print(f"  Image:       {args.image}")


def create(parser: argparse.ArgumentParser, args: argparse.Namespace) -> int:
    """Create LittleFS image from directory content"""
    validate_args(parser, args)

    source = pathlib.Path(args.source).absolute()
    fs = _fs_from_args(args)
    for path in source.rglob("*"):
        rel_path = path.relative_to(source)
        if path.is_dir():
            print("Adding Directory:", rel_path)
            fs.mkdir(rel_path.as_posix())
        else:
            print("Adding File:     ", rel_path)
            with fs.open(rel_path.as_posix(), "wb") as dest:
                dest.write(path.read_bytes())

    args.image.write_bytes(fs.context.buffer)
    return 0


def _list(parser: argparse.ArgumentParser, args: argparse.Namespace) -> int:
    """List LittleFS image content"""
    validate_args(parser, args)

    fs = _fs_from_args(args)
    fs.context.buffer = bytearray(args.image.read_bytes())

    fs.mount()
    for root, dirs, files in fs.walk("/"):
        if not root.endswith("/"):
            root += "/"
        for dir in dirs:
            print(f"{root}{dir}")
        for file in files:
            print(f"{root}{file}")
    return 0


def unpack(parser: argparse.ArgumentParser, args: argparse.Namespace) -> int:
    """Unpack LittleFS image to directory"""
    validate_args(parser, args)

    fs = _fs_from_args(args)
    with open(args.image, "rb") as fp:
        fs.context.buffer = bytearray(fp.read())

    root_dest: pathlib.Path = args.destination
    root_dest = root_dest.absolute()
    if not root_dest.exists() or not root_dest.is_dir():
        print("Destination directory does not exist")
        return 1

    fs.mount()
    for root, dirs, files in fs.walk("/"):
        if not root.endswith("/"):
            root += "/"
        for dir in dirs:
            src_path = root + dir
            dst_path = root_dest / src_path[1:]
            print(src_path, dst_path)
            assert root_dest in dst_path.parents
            dst_path.mkdir(exist_ok=True)
        for file in files:
            src_path = root + file
            dst_path = root_dest / src_path[1:]
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
    common_parser.add_argument("--block-size", type=size_parser, required=True, help="LittleFS block size")
    common_parser.add_argument("--name-max", type=size_parser, default=255, help="LittleFS max file path length.")
    group = common_parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--block-count", type=int, help="LittleFS block count")
    group.add_argument("--fs-size", type=size_parser, help="LittleFS filesystem size")
    common_parser.add_argument("--image", type=pathlib.Path, required=True, help="LittleFS filesystem image")

    subparsers = parser.add_subparsers(required=True, title="Available Commands", dest="command")

    def add_command(handler, name="", help=""):
        subparser = subparsers.add_parser(
            name or handler.__name__, parents=[common_parser], help=help or handler.__doc__
        )
        subparser.set_defaults(func=handler)
        return subparser

    parser_create = add_command(create)
    parser_create.add_argument("source", help="Source Directory", type=pathlib.Path)

    parser_unpack = add_command(unpack)
    parser_unpack.add_argument("destination", help="Destination Directory", type=pathlib.Path)

    parser_list = add_command(_list, "list")

    return parser


def main():
    parser = get_parser()
    parser.parse_known_args(sys.argv[1:])  # Allows for ``littlefs-python --version``
    args = parser.parse_args(sys.argv[1:])
    return args.func(parser, args)


if __name__ == "__main__":
    sys.exit(main())
