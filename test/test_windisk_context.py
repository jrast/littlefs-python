"""Tests for UserContextWinDisk on Windows platforms.

These tests are only run on Windows systems where win32file is available.
They test the Windows disk/file context for basic LittleFS operations.
"""

import pytest
import sys

# Only run these tests on Windows with win32file available
try:
    import win32file
    HAS_WIN32FILE = True
except ImportError:
    HAS_WIN32FILE = False

# Import after checking for win32file
from littlefs import LittleFS
from littlefs.context import UserContextWinDisk


@pytest.mark.skipif(
    not HAS_WIN32FILE or sys.platform != "win32",
    reason="win32file is required and test must run on Windows"
)
class TestUserContextWinDisk:
    """Test suite for UserContextWinDisk"""

    @pytest.fixture
    def disk_image_path(self, tmp_path):
        """Create a temporary disk image file path"""
        # Create a pre-allocated disk image file (2MB with 0xFF fill)
        image_path = tmp_path / "disk_image.bin"
        with open(image_path, "wb") as f:
            # Create a 2MB disk image (0xFF filled)
            f.write(b"\xff" * (2 * 1024 * 1024))
        return str(image_path)

    def test_windisk_read_after_remount(self, disk_image_path):
        """Test reading file content after remounting"""
        block_size = 512
        block_count = 256
        test_content = "Hello, this is persistent data!"

        ctx = UserContextWinDisk(disk_image_path)
        try:
            fs = LittleFS(context=ctx, block_size=block_size, block_count=block_count)

            # Write file
            with fs.open("persistent.txt", "w") as fh:
                fh.write(test_content)

            fs.unmount()

            # Remount and read
            fs.mount()
            with fs.open("persistent.txt", "r") as fh:
                content = fh.read()
                assert content == test_content

            fs.unmount()
        finally:
            ctx.__del__()
