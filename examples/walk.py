# This script walks in a littlefs image and print contents.
#
# E.g.
# % python3 examples/walk.py --img-filename=test.img
# root . dirs ['lfs'] files ['test_directories.py', 'test_files.py', 'test_remove_rename.py', 'test_version.py', 'test_walk.py']
# root ./lfs dirs [] files ['conftest.py', 'test_dir_functions.py', 'test_file_functions.py', 'test_fs_functions.py']
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
args = parser.parse_args()

img_filename = args.img_filename
img_size = args.img_size
block_size = args.block_size
read_size = args.read_size
prog_size = args.prog_size
name_max = args.name_max
file_max = args.file_max
attr_max = args.attr_max

block_count = img_size // block_size
if block_count * block_size != img_size:
    print("image size should be a multiple of block size")
    exit(1)

fs = LittleFS(
    block_size=block_size,
    block_count=block_count,
    read_size=read_size,
    prog_size=prog_size,
    name_max=name_max,
    file_max=file_max,
    attr_max=attr_max,
)

with open(img_filename, "rb") as f:
    data = f.read()
fs.context.buffer = bytearray(data)
fs.mount()

for root, dirs, files in fs.walk("."):
    print(f"root {root} dirs {dirs} files {files}")
