"""
Env policy tests for repomix_batch.py: secrets come from os.environ ONLY.

The script is copied into a throwaway skill tree so planted .env files sit
exactly where the old EnvLoader looked (skill/.env, skills/.env, .claude/.env)
without touching the repo. subprocess.run is mocked; no real repomix needed.
"""

import importlib.util
import os
import shutil
from pathlib import Path
from unittest.mock import Mock, patch

SCRIPT = Path(__file__).resolve().parent.parent / "repomix_batch.py"
FILE_ONLY = "REPOMIX_TEST_FILE_ONLY_SECRET"
BOTH = "REPOMIX_TEST_BOTH"


def _load_copy_with_planted_dotenv(tmp_path):
    """Copy the script to <tmp>/.claude/skills/repomix/scripts/ and plant .env files."""
    claude_dir = tmp_path / ".claude"
    skills_dir = claude_dir / "skills"
    skill_dir = skills_dir / "repomix"
    scripts_dir = skill_dir / "scripts"
    scripts_dir.mkdir(parents=True)
    copied = scripts_dir / "repomix_batch.py"
    shutil.copy(SCRIPT, copied)
    for directory in (skill_dir, skills_dir, claude_dir):
        (directory / ".env").write_text(f"{FILE_ONLY}=from-dotenv\n{BOTH}=from-dotenv\n")
    spec = importlib.util.spec_from_file_location("repomix_batch_copy", copied)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_repomix_batch_dotenv_next_to_script_is_not_loaded(tmp_path):
    # Arrange
    module = _load_copy_with_planted_dotenv(tmp_path)
    clean_env = {k: v for k, v in os.environ.items() if k not in (FILE_ONLY, BOTH)}
    clean_env[BOTH] = "from-process"

    # Act
    with patch.dict(os.environ, clean_env, clear=True):
        processor = module.RepomixBatchProcessor(module.RepomixConfig())

    # Assert
    assert FILE_ONLY not in processor.env_vars
    assert processor.env_vars[BOTH] == "from-process"


def test_repomix_batch_dotenv_secret_is_not_forwarded_to_child_process(tmp_path):
    # Arrange
    module = _load_copy_with_planted_dotenv(tmp_path)
    clean_env = {k: v for k, v in os.environ.items() if k != FILE_ONLY}
    clean_env["REPOMIX_TEST_FROM_PROCESS"] = "yes"

    # Act
    with patch.dict(os.environ, clean_env, clear=True), \
            patch("subprocess.run", return_value=Mock(returncode=0)) as mock_run:
        processor = module.RepomixBatchProcessor(module.RepomixConfig(output_dir=str(tmp_path / "out")))
        processor.check_repomix_installed()
        processor.process_repository(str(tmp_path), "out.xml")

    # Assert
    assert mock_run.call_count >= 2
    for call in mock_run.call_args_list:
        child_env = call.kwargs["env"]
        assert FILE_ONLY not in child_env
        assert child_env["REPOMIX_TEST_FROM_PROCESS"] == "yes"


def test_repomix_batch_module_has_no_dotenv_walker():
    # Arrange / Act
    source = SCRIPT.read_text(encoding="utf-8")

    # Assert
    assert "EnvLoader" not in source
    assert "_parse_env_file" not in source
