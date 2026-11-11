#!/usr/bin/env python3
"""Tests for find-polluter.sh (temp project dir, TEST_CMD=sh so no npm/node needed)."""

import os
import subprocess
from pathlib import Path

SCRIPT = Path(__file__).resolve().parent.parent / "find-polluter.sh"

CLEAN = "true\n"
POLLUTER = "mkdir -p .git\n"


def _project(tmp_path):
    src = tmp_path / "src"
    src.mkdir()
    (src / "a.test.sh").write_text(CLEAN)
    (src / "b.test.sh").write_text(POLLUTER)
    (src / "c.test.sh").write_text(CLEAN)
    return tmp_path


def _run(cwd, pattern):
    env = {**os.environ, "TEST_CMD": "sh"}
    return subprocess.run(
        ["bash", str(SCRIPT), ".git", pattern],
        capture_output=True, text=True, cwd=cwd, env=env,
    )


def test_find_polluter_pattern_without_dot_slash_finds_polluter(tmp_path):
    """Regression: 'src/*.test.sh' matched 0 files and reported all clean."""
    # Arrange
    cwd = _project(tmp_path)

    # Act
    result = _run(cwd, "src/*.test.sh")

    # Assert
    assert result.returncode == 1
    assert "FOUND POLLUTER" in result.stdout
    assert "./src/b.test.sh" in result.stdout


def test_find_polluter_pattern_with_dot_slash_finds_polluter(tmp_path):
    # Arrange
    cwd = _project(tmp_path)

    # Act
    result = _run(cwd, "./src/*.test.sh")

    # Assert
    assert result.returncode == 1
    assert "./src/b.test.sh" in result.stdout


def test_find_polluter_no_matching_files_exits_2_not_clean(tmp_path):
    """Regression: an empty match set printed 'No polluter found' and exited 0."""
    # Arrange
    cwd = _project(tmp_path)

    # Act
    result = _run(cwd, "lib/*.spec.ts")

    # Assert
    assert result.returncode == 2
    assert "No polluter found" not in result.stdout
    assert "No test files match" in result.stderr


def test_find_polluter_all_clean_exits_0(tmp_path):
    # Arrange
    cwd = _project(tmp_path)
    (cwd / "src" / "b.test.sh").write_text(CLEAN)

    # Act
    result = _run(cwd, "src/*.test.sh")

    # Assert
    assert result.returncode == 0
    assert "Found 3 test files" in result.stdout
    assert "No polluter found" in result.stdout
