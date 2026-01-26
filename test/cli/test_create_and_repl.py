from pathlib import Path
from unittest.mock import patch
from io import StringIO

from littlefs.__main__ import main


def test_create_compact_no_pad_and_repl(tmp_path):
    """Test creating a filesystem image with --compact --no-pad and opening it in REPL."""
    # Create test directory with files
    source_dir = tmp_path / "source"
    source_dir.mkdir()
    (source_dir / "file1.txt").write_text("hello world")
    (source_dir / "subdir").mkdir()
    (source_dir / "subdir" / "file2.txt").write_text("test content")
    
    # Create filesystem image with --compact and --no-pad flags
    image_file = tmp_path / "test_compact.bin"
    create_argv = [
        "littlefs",
        "create",
        str(source_dir),
        str(image_file),
        "--block-size", "512",
        "--fs-size", "64KB",
        "--compact",
        "--no-pad",
    ]
    assert main(create_argv) == 0
    assert image_file.exists()
    
    # Verify the image is compacted (size should be less than 64KB)
    image_size = image_file.stat().st_size
    assert image_size < 64 * 1024, f"Expected compacted size < 64KB, got {image_size}"
    
    # Mock stdin to exit immediately from REPL
    # The REPL will run cmdloop() which reads from stdin
    # We send "exit" command to quit the REPL
    mock_stdin = StringIO("exit\n")
    
    with patch('sys.stdin', mock_stdin):
        # Test that REPL can open and mount the compacted image
        repl_argv = [
            "littlefs",
            "repl",
            str(image_file),
            "--block-size", "512",
        ]
        # The REPL should successfully mount and then exit
        result = main(repl_argv)
        assert result == 0 or result is None  # REPL returns 0 or None on success


def test_create_verbose_and_repl_verbose(tmp_path):
    """Test creating a filesystem image with --verbose and opening it in REPL with --verbose."""
    # Create test directory with files
    source_dir = tmp_path / "source"
    source_dir.mkdir()
    (source_dir / "file1.txt").write_text("hello world")
    (source_dir / "subdir").mkdir()
    (source_dir / "subdir" / "file2.txt").write_text("test content")
    
    # Create filesystem image with --verbose flag
    image_file = tmp_path / "test_verbose.bin"
    
    create_argv = [
        "littlefs",
        "create",
        str(source_dir),
        str(image_file),
        "--block-size", "512",
        "--fs-size", "64KB",
        "--verbose",
    ]
    assert main(create_argv) == 0
    
    assert image_file.exists()
    
    # Mock stdin to exit immediately from REPL
    mock_stdin = StringIO("exit\n")
    
    with patch('sys.stdin', mock_stdin):
        # Test that REPL can open and mount the image with --verbose
        repl_argv = [
            "littlefs",
            "repl",
            str(image_file),
            "--block-size", "512",
            "--verbose",
        ]
        # The REPL should successfully mount and then exit
        result = main(repl_argv)
        assert result == 0 or result is None  # REPL returns 0 or None on success

