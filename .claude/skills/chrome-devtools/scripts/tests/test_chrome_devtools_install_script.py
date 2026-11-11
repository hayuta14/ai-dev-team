#!/usr/bin/env python3
"""Tests for chrome-devtools install.sh (fake node/npm on PATH, nothing installed)."""

import os
import shutil
import subprocess
from pathlib import Path

INSTALL_SH = Path(__file__).resolve().parent.parent / "install.sh"


def _setup(tmp_path):
    """Copy install.sh into a fake skill dir; fake npm logs its cwd and env."""
    skill = tmp_path / "skill"
    skill.mkdir()
    shutil.copy(INSTALL_SH, skill / "install.sh")
    bin_dir = tmp_path / "bin"
    bin_dir.mkdir()
    log = tmp_path / "npm.log"
    (bin_dir / "node").write_text("#!/bin/sh\necho v22.0.0\n")
    (bin_dir / "npm").write_text(
        f'#!/bin/sh\necho "$(pwd) skip=$PUPPETEER_SKIP_DOWNLOAD" > "{log}"\n'
    )
    for f in bin_dir.iterdir():
        f.chmod(0o755)
    other = tmp_path / "workspace-root"
    other.mkdir()
    return skill, bin_dir, log, other


def _run(skill, bin_dir, cwd, **extra_env):
    env = {k: v for k, v in os.environ.items() if k not in ("CHROME_PATH", "PUPPETEER_SKIP_DOWNLOAD")}
    env.update(PATH=f"{bin_dir}:/usr/bin:/bin", **extra_env)
    return subprocess.run(
        ["bash", str(skill / "install.sh")], cwd=cwd, env=env,
        stdin=subprocess.DEVNULL, capture_output=True, text=True,
    )


def test_chrome_devtools_install_from_other_cwd_installs_in_script_dir(tmp_path):
    """Regression: npm install ran in the caller's cwd (e.g. workspace root)."""
    # Arrange
    skill, bin_dir, log, other = _setup(tmp_path)

    # Act
    result = _run(skill, bin_dir, other)

    # Assert
    assert result.returncode == 0, result.stdout + result.stderr
    assert log.read_text().split()[0] == str(skill.resolve())


def test_chrome_devtools_install_puppeteer_present_skips_npm(tmp_path):
    # Arrange
    skill, bin_dir, log, other = _setup(tmp_path)
    (skill / "node_modules" / "puppeteer").mkdir(parents=True)

    # Act
    result = _run(skill, bin_dir, other)

    # Assert
    assert result.returncode == 0
    assert not log.exists()


def test_chrome_devtools_install_chrome_path_skips_chrome_download(tmp_path):
    # Arrange
    skill, bin_dir, log, other = _setup(tmp_path)

    # Act
    result = _run(skill, bin_dir, other, CHROME_PATH="/opt/chrome/chrome")

    # Assert
    assert result.returncode == 0
    assert "skip=1" in log.read_text()
