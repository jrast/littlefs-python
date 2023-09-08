import argparse
import sys
import textwrap
import pathlib
from littlefs import LittleFS


def create(args: argparse.Namespace):
    """Create LittleFS image from directory content"""
    if args.block_size is None or args.block_count is None:
        print("Block size and block count is required to create an image.")
        return -1

    source = pathlib.Path(args.source).absolute()
    fs = LittleFS(block_size=args.block_size, block_count=args.block_count)
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


def _list(args: argparse.Namespace):
    """List LittleFS image content"""
    if args.block_size is None or args.block_count is None:
        print("Block size and block count is required to create an image.")
        return -1

    fs = LittleFS(block_size=args.block_size, block_count=args.block_count)
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


def unpack(args: argparse.Namespace):
    """Unpack LittleFS image to directory"""
    if args.block_size is None or args.block_count is None:
        print("Block size and block count is required to create an image.")
        return -1

    fs = LittleFS(block_size=args.block_size, block_count=args.block_count)
    with open(args.image, "rb") as fp:
        fs.context.buffer = bytearray(fp.read())

    root_dest: pathlib.Path = args.destination
    root_dest = root_dest.absolute()
    if not root_dest.exists() or not root_dest.is_dir():
        print("Destination directory does not exist")
        return -1

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


def main():
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

    common_parser = argparse.ArgumentParser(add_help=False)
    common_parser.add_argument("-v", "--verbose", action="count", default=0)
    common_parser.add_argument("-s", "--block-size", type=int, help="LittleFS block size")
    common_parser.add_argument("-c", "--block-count", type=int, help="LittleFS block count")
    common_parser.add_argument("-i", "--image", help="LittleFS filesystem image", type=pathlib.Path)

    subparsers = parser.add_subparsers(required=True, title="available commands", dest="command")

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

    args = parser.parse_args(sys.argv[1:])
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
