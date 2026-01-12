from pathlib import Path
import filecmp

from littlefs.__main__ import main


def test_create_and_extract(tmp_path):
    """Test creating a filesystem image and extracting it."""
    # Create test directory with files
    source_dir = tmp_path / "source"
    source_dir.mkdir()
    (source_dir / "file1.txt").write_text("hello world")
    (source_dir / "subdir").mkdir()
    (source_dir / "subdir" / "file2.txt").write_text("test content")
    
    # Create filesystem image
    image_file = tmp_path / "test_image.bin"
    create_argv = [
        "littlefs",
        "create",
        str(source_dir),
        str(image_file),
        "--block-size", "512",
        "--fs-size", "64KB",
    ]
    assert main(create_argv) == 0
    assert image_file.exists()
    
    # Extract filesystem image
    extract_dir = tmp_path / "extracted"
    extract_argv = [
        "littlefs",
        "extract",
        str(image_file),
        str(extract_dir),
        "--block-size", "512",
    ]
    assert main(extract_argv) == 0
    assert extract_dir.exists()
    
    # Compare directories
    comparison = filecmp.dircmp(source_dir, extract_dir)
    assert not comparison.diff_files
    assert not comparison.left_only
    assert not comparison.right_only
    
    # Verify file contents
    assert (extract_dir / "file1.txt").read_text() == "hello world"
    assert (extract_dir / "subdir" / "file2.txt").read_text() == "test content"
