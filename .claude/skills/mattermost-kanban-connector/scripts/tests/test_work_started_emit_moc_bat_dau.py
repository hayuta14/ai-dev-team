#!/usr/bin/env python3
"""Unit tests cho work-started-emit-moc-bat-dau.py.

Theo test-standards.md: tên test_[hệ thống]_[tình huống]_[kết quả mong đợi],
Arrange/Act/Assert, mock external deps (subprocess avatar CLI + urllib HTTP),
không phụ thuộc external state.

Script entry mang tên kebab-case nên KHÔNG import được bằng tên — load qua
importlib.util.spec_from_file_location (cùng lý do quy ước đặt tên trong SKILL.md).
"""
import importlib.util
import io
import json
import sys
from pathlib import Path
from unittest.mock import patch

import pytest

SCRIPT_PATH = Path(__file__).parent.parent / "work-started-emit-moc-bat-dau.py"


def _load_module():
    spec = importlib.util.spec_from_file_location("work_started_emit", SCRIPT_PATH)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


@pytest.fixture()
def mod():
    return _load_module()


def _run_main(mod, stdin_text, capsys):
    """Chạy main() với stdin giả, trả (exit_code, stdout, stderr)."""
    sys.stdin = io.StringIO(stdin_text)
    try:
        code = mod.main()
    finally:
        sys.stdin = sys.__stdin__
    captured = capsys.readouterr()
    return code, captured.out, captured.err


TOKEN_GIA = "SECRET-ID-TOKEN-KHONG-DUOC-LO"


class _FakeResp:
    """Response giả cho urlopen — context manager như bản thật."""

    def __init__(self, status=200, body=b'{"ok":true}'):
        self.status = status
        self._body = body

    def read(self):
        return self._body

    def __enter__(self):
        return self

    def __exit__(self, *a):
        return False


def test_work_started_emit_thanh_cong_tra_json_ok_exit_0(mod, capsys):
    # Arrange: token lấy được, server 200.
    with patch.object(mod, "_lay_id_token", return_value=TOKEN_GIA), \
         patch("urllib.request.urlopen", return_value=_FakeResp(200)) as mock_open:
        # Act
        code, out, err = _run_main(mod, '{"ticket_id": 298}', capsys)

    # Assert: exit 0, stdout JSON có ok/ticket_id, request mang Bearer token.
    assert code == 0
    body = json.loads(out)
    assert body["ok"] is True and body["ticket_id"] == 298
    req = mock_open.call_args[0][0]
    assert req.get_header("Authorization") == f"Bearer {TOKEN_GIA}"
    payload = json.loads(req.data.decode())
    assert payload["ticket_id"] == 298 and "moc_bat_dau" in payload


def test_work_started_emit_khong_in_token_ra_stdout_stderr(mod, capsys):
    # Arrange: cả ca thành công lẫn ca server lỗi — token không được xuất hiện đâu cả.
    for resp in (_FakeResp(200), _FakeResp(500, b"boom")):
        with patch.object(mod, "_lay_id_token", return_value=TOKEN_GIA), \
             patch("urllib.request.urlopen", return_value=resp):
            # Act
            _, out, err = _run_main(mod, '{"ticket_id": 51}', capsys)

        # Assert
        assert TOKEN_GIA not in out and TOKEN_GIA not in err


def test_work_started_emit_moi_nguon_token_can_bao_loi_khong_post(mod, capsys):
    # Arrange: avatar CLI fail + config tĩnh không có → _lay_id_token trả None.
    with patch.object(mod, "_lay_id_token", return_value=None), \
         patch("urllib.request.urlopen") as mock_open:
        # Act
        code, out, err = _run_main(mod, '{"ticket_id": 57}', capsys)

    # Assert: exit != 0, stderr tiếng Việt nêu mốc CHƯA ghi, KHÔNG gọi HTTP.
    assert code == 3
    assert "CHƯA được ghi" in err and "avatar login" in err
    mock_open.assert_not_called()


def test_work_started_emit_server_tra_500_bao_ro_moc_chua_ghi(mod, capsys):
    # Arrange: route fail-CLOSED trả 500 khi DB lỗi.
    with patch.object(mod, "_lay_id_token", return_value=TOKEN_GIA), \
         patch("urllib.request.urlopen", return_value=_FakeResp(500, b'{"error":"internal"}')):
        # Act
        code, out, err = _run_main(mod, '{"ticket_id": 296}', capsys)

    # Assert: exit != 0, KHÔNG in JSON ok, stderr nêu HTTP 500 + mốc chưa ghi.
    assert code == 5
    assert out == ""
    assert "HTTP 500" in err and "CHƯA được ghi" in err


def test_work_started_emit_loi_mang_bao_loai_loi_va_cach_thu_lai(mod, capsys):
    # Arrange: urlopen ném lỗi mạng (không phải HTTPError).
    with patch.object(mod, "_lay_id_token", return_value=TOKEN_GIA), \
         patch("urllib.request.urlopen", side_effect=OSError("connection refused")):
        # Act
        code, out, err = _run_main(mod, '{"ticket_id": 294}', capsys)

    # Assert: exit != 0, stderr nêu loại lỗi + lệnh chạy lại, không lộ chi tiết request.
    assert code == 4
    assert "OSError" in err and "thử lại" in err


@pytest.mark.parametrize("stdin_text", [
    "khong phai json",
    "{}",
    '{"ticket_id": "abc"}',
    '{"ticket_id": -3}',
    '{"ticket_id": 0}',
    '[298]',
    '{"ticket_id": true}',
    '{"ticket_id": 3.7}',
])
def test_work_started_emit_input_hong_tra_exit_2_khong_post(mod, capsys, stdin_text):
    # Arrange: mọi biến thể input hỏng.
    with patch("urllib.request.urlopen") as mock_open:
        # Act
        code, out, err = _run_main(mod, stdin_text, capsys)

    # Assert
    assert code == 2
    assert err != ""
    mock_open.assert_not_called()


def test_work_started_emit_moc_tu_stdin_duoc_dung_nguyen_van(mod, capsys):
    # Arrange: caller truyền mốc tường minh (ca receive ghi mốc ngay lúc move lane).
    moc = "2026-08-24T03:00:00+00:00"
    with patch.object(mod, "_lay_id_token", return_value=TOKEN_GIA), \
         patch("urllib.request.urlopen", return_value=_FakeResp(200)) as mock_open:
        # Act
        code, out, _ = _run_main(mod, json.dumps({"ticket_id": 297, "moc_bat_dau": moc}), capsys)

    # Assert
    assert code == 0
    payload = json.loads(mock_open.call_args[0][0].data.decode())
    assert payload["moc_bat_dau"] == moc
