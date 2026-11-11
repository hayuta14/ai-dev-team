#!/usr/bin/env python3
"""Tests for search.py entry point."""

import subprocess
import sys
from pathlib import Path

SEARCH = Path(__file__).resolve().parent.parent / "search.py"


def test_ui_ux_search_isolated_mode_from_other_cwd_finds_core(tmp_path):
    """Regression: `python3 -I search.py` crashed with ModuleNotFoundError: core."""
    # Arrange: -I drops the script dir from sys.path; -B keeps the tree clean.
    cmd = [sys.executable, "-I", "-B", str(SEARCH), "dashboard", "--max-results", "1"]

    # Act
    result = subprocess.run(cmd, capture_output=True, text=True, cwd=tmp_path)

    # Assert
    assert result.returncode == 0, result.stderr
    assert "ModuleNotFoundError" not in result.stderr
    assert "UI Pro Max Search Results" in result.stdout
