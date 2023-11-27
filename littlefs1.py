import ctypes
import win32file
# from src.littlefs.win_disk_context import UserContextWinDisk
import ctypes
import win32file
import logging
import typing


from littlefs import LittleFS, UserContextWinDisk

disk_path = r"\\.\D:"
    

fs = LittleFS(block_size=512, block_count=256, mount=False, context=UserContextWinDisk(disk_path))
# with open('FlashMemory.bin', 'rb') as fh:
#     fs.context.buffer = bytearray(fh.read())

fs.mount()

print(fs.listdir('/'))
with fs.open('first-file.txt', 'r') as fh:
    print(fh.readlines())    
