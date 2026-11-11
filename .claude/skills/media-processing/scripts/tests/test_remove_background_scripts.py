#!/usr/bin/env python3
"""Tests for remove-background.sh / batch-remove-background.sh dependency gate."""

import os
import subprocess
from pathlib import Path

import pytest

SCRIPTS_DIR = Path(__file__).parent.parent


@pytest.mark.parametrize(
    "script,make_arg",
    [
        ("remove-background.sh", lambda d: d / "photo.jpg"),
        ("batch-remove-background.sh", lambda d: d),
    ],
)
def test_remove_background_rmbg_missing_exits_2_without_npm_install(
    tmp_path, script, make_arg
):
    """Regression: a missing rmbg-cli triggered a silent `npm install -g`."""
    # Arrange: PATH without rmbg; a fake npm records any call.
    bin_dir = tmp_path / "bin"
    bin_dir.mkdir()
    npm_log = tmp_path / "npm-called"
    fake_npm = bin_dir / "npm"
    fake_npm.write_text(f'#!/bin/sh\necho "$@" > "{npm_log}"\n')
    fake_npm.chmod(0o755)
    (tmp_path / "photo.jpg").write_bytes(b"x")
    env = {**os.environ, "PATH": f"{bin_dir}:/usr/bin:/bin"}

    # Act
    result = subprocess.run(
        ["bash", str(SCRIPTS_DIR / script), str(make_arg(tmp_path))],
        capture_output=True, text=True, env=env, cwd=tmp_path,
    )

    # Assert
    assert result.returncode == 2
    assert "npm install -g rmbg-cli" in result.stderr
    assert not npm_log.exists()
    assert not (tmp_path / "no-bg").exists()
