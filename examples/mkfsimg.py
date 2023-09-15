# This script creates a littlefs filesystem image from a directory.
#
# E.g.
# % python3 examples/mkfsimg.py --img-filename=test.img test
# root test dirs ['lfs'] files ['test_directories.py', 'test_version.py', 'test_files.py', 'test_walk.py', 'test_remove_rename.py']
# Mkdir lfs
# Copying test/test_directories.py to test_directories.py
# Copying test/test_version.py to test_version.py
# Copying test/test_files.py to test_files.py
# Copying test/test_walk.py to test_walk.py
# Copying test/test_remove_rename.py to test_remove_rename.py
# root test/lfs dirs [] files ['conftest.py', 'test_dir_functions.py', 'test_fs_functions.py', 'test_file_functions.py']
# Copying test/lfs/conftest.py to lfs/conftest.py
# Copying test/lfs/test_dir_functions.py to lfs/test_dir_functions.py
# Copying test/lfs/test_fs_functions.py to lfs/test_fs_functions.py
# Copying test/lfs/test_file_functions.py to lfs/test_file_functions.py
# %

import argparse
import os
import sys

from littlefs import LittleFS

parser = argparse.ArgumentParser()
parser.add_argument("--img-filename", default="littlefs.img")
parser.add_argument("--img-size", type=int, default=1 * 1024 * 1024)
parser.add_argument("--block-size", type=int, default=4096)
parser.add_argument("--read-size", type=int, default=256)
parser.add_argument("--prog-size", type=int, default=256)
# Note: 0 means to use the build-time default.
parser.add_argument("--name-max", type=int, default=0)
parser.add_argument("--file-max", type=int, default=0)
parser.add_argument("--attr-max", type=int, default=0)
parser.add_argument("--disk-version", default=None)
parser.add_argument("source")
args = parser.parse_args()

img_filename = args.img_filename
img_size = args.img_size
block_size = args.block_size
read_size = args.read_size
prog_size = args.prog_size
name_max = args.name_max
file_max = args.file_max
attr_max = args.attr_max
source_dir = args.source

block_count = img_size // block_size
if block_count * block_size != img_size:
    print("image size should be a multiple of block size")
    exit(1)

if args.disk_version is None:
    disk_version = 0  # 0 means the latest
else:
    # "2.1" -> 0x00020001
    try:
        major, minor = args.disk_version.split(".")
        disk_version = int(major) * 0x10000 + int(minor)
    except:
        print(f"failed to parse disk version: {args.disk_version}")
        exit(1)

fs = LittleFS(
    block_size=block_size,
    block_count=block_count,
    read_size=read_size,
    prog_size=prog_size,
    name_max=name_max,
    file_max=file_max,
    attr_max=attr_max,
    disk_version=disk_version,
)

# Note: path component separator etc are assumed to be compatible
# between littlefs and host.
for root, dirs, files in os.walk(source_dir):
    print(f"root {root} dirs {dirs} files {files}")
    for dir in dirs:
        path = os.path.join(root, dir)
        relpath = os.path.relpath(path, start=source_dir)
        print(f"Mkdir {relpath}")
        fs.mkdir(relpath)
    for f in files:
        path = os.path.join(root, f)
        relpath = os.path.relpath(path, start=source_dir)
        print(f"Copying {path} to {relpath}")
        with open(path, "rb") as infile:
            with fs.open(relpath, "wb") as outfile:
                outfile.write(infile.read())

with open(img_filename, "wb") as f:
    f.write(fs.context.buffer)
