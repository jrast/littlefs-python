from pkg_resources import get_distribution, DistributionNotFound
try:
    __version__ = get_distribution(__name__).version
except DistributionNotFound:
    # Package not installed
    pass

from _littlefs import (__LFS_DISK_VERSION__, __LFS_VERSION__, LFSFileHandle,
                       LittleFS)


