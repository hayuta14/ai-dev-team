"""Danh tính phụ (PAT cá nhân): mặc định đăng bằng bot, `--as-me` đăng dưới tên dev.

Phủ: load_credentials(as_me=...) + entry mattermost-post-comment-thread-and-direct-message.py.
FAKE token — không token thật. Không network (patch MattermostClient.post_json).
"""
import importlib.util
import json
import sys
from pathlib import Path

import pytest

SCRIPTS_DIR = Path(__file__).parent.parent.absolute()
if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))

import mattermost_credentials_reader_and_token_masker as creds_module  # noqa: E402

URL = "https://mm.nal.vn"
BOT = {
    "mattermostUrl": URL, "botName": "avatar", "botToken": "fake-bot-token",
    "teamId": "t1", "defaultChannelId": "c1", "defaultChannelName": "backlog",
}
PAT = {"mattermostUrl": URL, "username": "nam", "patToken": "fake-pat-token"}


def _workspace(tmp_path, pat=PAT, raw_pat=None):
    mm = tmp_path / ".mattermost"
    mm.mkdir()
    (mm / "credentials.json").write_text(json.dumps(BOT))
    if raw_pat is not None:
        (mm / "personal-token.json").write_text(raw_pat)
    elif pat is not None:
        (mm / "personal-token.json").write_text(json.dumps(pat))
    return str(tmp_path)


class TestLoadCredentialsAsMe:
    def test_load_credentials_default_returns_bot_token(self, tmp_path):
        ws = _workspace(tmp_path)
        c = creds_module.load_credentials(workspace_root=ws)
        assert c["botToken"] == "fake-bot-token" and c["botName"] == "avatar"

    def test_load_credentials_as_me_swaps_token_and_name_keeps_rest(self, tmp_path):
        ws = _workspace(tmp_path)
        c = creds_module.load_credentials(workspace_root=ws, as_me=True)
        assert c["botToken"] == "fake-pat-token" and c["botName"] == "nam"
        assert c["defaultChannelId"] == "c1" and c["teamId"] == "t1"

    def test_load_credentials_as_me_missing_pat_file_raises_not_fallback_to_bot(self, tmp_path):
        ws = _workspace(tmp_path, pat=None)
        with pytest.raises(creds_module.CredentialsError) as exc:
            creds_module.load_credentials(workspace_root=ws, as_me=True)
        assert "comm-connect --personal" in str(exc.value)
        assert "fake-bot-token" not in str(exc.value)

    def test_load_credentials_as_me_missing_field_raises(self, tmp_path):
        ws = _workspace(tmp_path, pat={"mattermostUrl": URL, "username": "nam"})
        with pytest.raises(creds_module.CredentialsError) as exc:
            creds_module.load_credentials(workspace_root=ws, as_me=True)
        assert "patToken" in str(exc.value)

    def test_load_credentials_as_me_invalid_json_raises(self, tmp_path):
        ws = _workspace(tmp_path, raw_pat="{not json")
        with pytest.raises(creds_module.CredentialsError):
            creds_module.load_credentials(workspace_root=ws, as_me=True)

    def test_load_credentials_as_me_other_server_raises_without_leaking_token(self, tmp_path):
        ws = _workspace(tmp_path, pat={**PAT, "mattermostUrl": "https://other.example"})
        with pytest.raises(creds_module.CredentialsError) as exc:
            creds_module.load_credentials(workspace_root=ws, as_me=True)
        assert "khác" in str(exc.value) and "fake-pat-token" not in str(exc.value)


def _load_post_script():
    spec = importlib.util.spec_from_file_location(
        "post_entry", SCRIPTS_DIR / "mattermost-post-comment-thread-and-direct-message.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


class TestPostScriptIdentity:
    def _run(self, monkeypatch, capsys, tmp_path, argv):
        ws = _workspace(tmp_path)
        seen = {}

        def fake_post_json(self, path, body):
            seen["token"] = self._token
            return {"id": "post-1"}

        monkeypatch.setattr(creds_module, "_find_workspace_root", lambda _s: Path(ws))
        monkeypatch.setattr(
            "mattermost_api_http_client_with_bearer_auth.MattermostClient.post_json", fake_post_json)
        monkeypatch.setattr(sys, "argv", ["post", *argv])
        monkeypatch.setattr(sys, "stdin", __import__("io").StringIO("xin chào"))
        code = _load_post_script().main()
        return code, seen, capsys.readouterr()

    def test_post_comment_without_flag_uses_bot_token(self, monkeypatch, capsys, tmp_path):
        code, seen, _ = self._run(monkeypatch, capsys, tmp_path, ["comment", "thread-1"])
        assert code == 0 and seen["token"] == "fake-bot-token"

    def test_post_comment_with_as_me_uses_pat_token(self, monkeypatch, capsys, tmp_path):
        code, seen, out = self._run(monkeypatch, capsys, tmp_path, ["comment", "thread-1", "--as-me"])
        assert code == 0 and seen["token"] == "fake-pat-token"
        assert "fake-pat-token" not in out.out + out.err

    def test_post_comment_as_me_without_pat_exits_2_and_posts_nothing(self, monkeypatch, capsys, tmp_path):
        ws = _workspace(tmp_path, pat=None)
        called = []
        monkeypatch.setattr(creds_module, "_find_workspace_root", lambda _s: Path(ws))
        monkeypatch.setattr(
            "mattermost_api_http_client_with_bearer_auth.MattermostClient.post_json",
            lambda self, p, b: called.append(1) or {"id": "x"})
        monkeypatch.setattr(sys, "argv", ["post", "comment", "t1", "--as-me"])
        monkeypatch.setattr(sys, "stdin", __import__("io").StringIO("hi"))
        assert _load_post_script().main() == 2
        assert called == []
