from pathlib import Path

from littlefs.__main__ import _walk_all


def test_walk_all_basic(tmp_path):
    """Test basic directory traversal."""
    (tmp_path / "file1.txt").write_text("hello")
    (tmp_path / "subdir").mkdir()
    (tmp_path / "subdir" / "file2.txt").write_text("world")

    paths = list(_walk_all(tmp_path))
    rel_paths = {p.relative_to(tmp_path).as_posix() for p in paths}

    assert rel_paths == {"file1.txt", "subdir", "subdir/file2.txt"}


def test_walk_all_follows_symlinks(tmp_path):
    """Test that symlinks to directories are followed."""
    # Create a real directory with files
    real_dir = tmp_path / "real_dir"
    real_dir.mkdir()
    (real_dir / "file1.txt").write_text("hello")
    (real_dir / "nested").mkdir()
    (real_dir / "nested" / "file2.txt").write_text("world")

    # Create a symlink to the real directory
    symlink_dir = tmp_path / "symlink_dir"
    symlink_dir.symlink_to(real_dir)

    paths = list(_walk_all(tmp_path))
    rel_paths = {p.relative_to(tmp_path).as_posix() for p in paths}

    # Should include both the real directory contents and symlink contents
    assert "real_dir" in rel_paths
    assert "real_dir/file1.txt" in rel_paths
    assert "real_dir/nested" in rel_paths
    assert "real_dir/nested/file2.txt" in rel_paths
    assert "symlink_dir" in rel_paths
    assert "symlink_dir/file1.txt" in rel_paths
    assert "symlink_dir/nested" in rel_paths
    assert "symlink_dir/nested/file2.txt" in rel_paths


def test_walk_all_empty_directory(tmp_path):
    """Test traversal of empty directory."""
    paths = list(_walk_all(tmp_path))
    assert paths == []


def test_walk_all_nested_directories(tmp_path):
    """Test deeply nested directory traversal."""
    nested = tmp_path / "a" / "b" / "c"
    nested.mkdir(parents=True)
    (nested / "deep.txt").write_text("deep")

    paths = list(_walk_all(tmp_path))
    rel_paths = {p.relative_to(tmp_path).as_posix() for p in paths}

    assert rel_paths == {"a", "a/b", "a/b/c", "a/b/c/deep.txt"}
