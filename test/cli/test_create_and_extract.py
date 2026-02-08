from pathlib import Path
import filecmp

import pytest

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
        "--block-size",
        "512",
        "--fs-size",
        "64KB",
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
        "--block-size",
        "512",
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


@pytest.mark.parametrize(
    "num_files, file_size",
    [
        (1, 10),
        (5, 100),
        (10, 200),
        (15, 300),
        (20, 400),
        (30, 500),
        (1, 10000),
        (5, 5000),
    ],
)
def test_create_compact_roundtrip(tmp_path, num_files, file_size):
    """Test that --compact creates a valid image with all files preserved."""
    source_dir = tmp_path / "source"
    source_dir.mkdir()

    # Create source files with deterministic content
    for i in range(num_files):
        (source_dir / f"file_{i}.txt").write_text(f"content_{i}_" + "x" * file_size)

    image_file = tmp_path / "test_compact.bin"
    create_argv = [
        "littlefs", "create", str(source_dir), str(image_file),
        "--block-size", "512", "--fs-size", "64KB",
        "--compact", "--no-pad",
    ]

    assert main(create_argv) == 0
    assert image_file.exists()
    assert image_file.stat().st_size < 64 * 1024

    # Extract and verify all files survived compaction
    extract_dir = tmp_path / "extracted"
    extract_argv = [
        "littlefs", "extract", str(image_file), str(extract_dir),
        "--block-size", "512",
    ]
    assert main(extract_argv) == 0

    for i in range(num_files):
        extracted_file = extract_dir / f"file_{i}.txt"
        assert extracted_file.exists(), f"file_{i}.txt missing from compact image"
        assert extracted_file.read_text() == f"content_{i}_" + "x" * file_size
