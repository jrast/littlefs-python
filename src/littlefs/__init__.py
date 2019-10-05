from pkg_resources import get_distribution, DistributionNotFound
try:
    __version__ = get_distribution('littlefs-python').version
except DistributionNotFound:
    # Package not installed
    pass

from .lfs import __LFS_DISK_VERSION__, __LFS_VERSION__




