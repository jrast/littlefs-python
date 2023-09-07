import argparse
import sys
import textwrap
import pathlib
from littlefs import LittleFS


def _add_default_args(parser: argparse.ArgumentParser):
    parser.add_argument("-v", "--verbose", action="count", default=0)


def _add_littlefs_args(parser: argparse.ArgumentParser):
    parser.add_argument("-s", "--block-size", type=int, help="LittleFS block size")
    parser.add_argument("-c", "--block-count", type=int, help="LittleFS block count")
    parser.add_argument("-i", "--image", help="LittleFS filesystem image", type=pathlib.Path)


def _create(args: argparse.Namespace):
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
                with open(path, "rb") as src:
                    dest.write(src.read())
    with open(args.image, "wb") as fp:
        fp.write(fs.context.buffer)


def _list(args: argparse.Namespace):
    if args.block_size is None or args.block_count is None:
        print("Block size and block count is required to create an image.")
        return -1

    fs = LittleFS(block_size=args.block_size, block_count=args.block_count)
    with open(args.image, "rb") as fp:
        fs.context.buffer = bytearray(fp.read())

    fs.mount()
    for root, dirs, files in fs.walk("/"):
        if not root.endswith("/"):
            root += "/"
        for dir in dirs:
            print(f"{root}{dir}")
        for file in files:
            print(f"{root}{file}")


def _unpack(args: argparse.Namespace):
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
        prog = f"python-littlefs"

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

    subparsers = parser.add_subparsers(required=True, title="available commands", dest="command")

    parser_create = subparsers.add_parser(
        "create", help="Create LittleFS image from directory content"
    )
    parser_create.add_argument("source", help="Source Directory", type=pathlib.Path)

    parser_unpack = subparsers.add_parser("unpack", help="Unpack LittleFS image to directory")
    parser_unpack.add_argument("destination", help="Destination Directory", type=pathlib.Path)

    parser_list = subparsers.add_parser("list", help="List LittleFS image content")

    for subparser in subparsers.choices.values():
        _add_default_args(subparser)
        _add_littlefs_args(subparser)

    args = parser.parse_args(sys.argv[1:])

    print("Verbosity:", args.verbose)

    meth = {"create": _create, "unpack": _unpack, "list": _list}[args.command]
    return meth(args)


if __name__ == "__main__":
    sys.exit(main())
