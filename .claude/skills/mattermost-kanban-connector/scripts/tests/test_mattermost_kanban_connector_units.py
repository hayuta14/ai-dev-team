#!/usr/bin/env python3
"""Unit tests for Mattermost Kanban connector modules.

Test suite theo NAL test-standards.md:
- Đặt tên: test_[hệ thống]_[tình huống]_[kết quả mong đợi]
- Cấu trúc Arrange / Act / Assert rõ ràng
- Mock external dependencies (HTTP, filesystem) — KHÔNG gọi mm.nal.vn thật
- Unit test KHÔNG phụ thuộc external state — tự dọn dẹp

Modules under test:
- mattermost_credentials_reader_and_token_masker (load_credentials, mask_token)
- mattermost_api_http_client_with_bearer_auth (MattermostClient, build_card_edit_payload)
"""

import json
import sys
import time
from pathlib import Path
from unittest.mock import patch

import pytest

# Add scripts dir to path để import modules snake_case
SCRIPTS_DIR = Path(__file__).parent.parent.absolute()
if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))

import mattermost_credentials_reader_and_token_masker as creds_module
import mattermost_api_http_client_with_bearer_auth as client_module


@pytest.fixture(autouse=True)
def _isolate_watermark_state_for_every_test(monkeypatch, tmp_path):
    """Mọi ca trong file ghi state watermark vào thư mục TẠM, không đụng file thật.

    ⛔ Vì sao autouse ở MODULE-level chứ không theo từng ca: digest gọi
    `check_and_update_watermark` (#216) nên bất kỳ ca nào chạy digest đều GHI
    `.claude/state/kanban-cap-watermark.json`. Bỏ sót một ca là bộ test đẩy mốc
    production lên 11 (fixture có lane 11 card) ⇒ lần digest thật kế tiếp với
    board bình thường (max 10) khớp vị từ và bắn BÁO ĐỘNG GIẢ — bộ test tự đầu
    độc công cụ nó đang gác. Chặn ở đây thì ca viết THÊM sau này cũng an toàn
    mặc định, không phải nhớ.
    """
    monkeypatch.setenv("CLAUDE_PROJECT_DIR", str(tmp_path))


# ╔══════════════════════════════════════════════════════════════════════════╗
# ║ Tests: mattermost_credentials_reader_and_token_masker                    ║
# ╚══════════════════════════════════════════════════════════════════════════╝


class TestMaskToken:
    """Test suite cho mask_token(token: str) -> str."""

    def test_mask_token_long_token_shows_only_4_trailing_chars(self):
        """Arrange: Token dài 32 ký tự. Act: mask_token. Assert: Hiển thị ••••••••••••••••••••••••••XYZ4."""
        token = "a" * 28 + "XYZ4"
        result = creds_module.mask_token(token)
        assert result == "•" * 28 + "XYZ4"
        assert len(result) == 32

    def test_mask_token_empty_string_returns_empty_marker(self):
        """Arrange: Token rỗng. Act: mask_token. Assert: Trả "(rỗng)"."""
        result = creds_module.mask_token("")
        assert result == "(rỗng)"

    def test_mask_token_none_token_returns_empty_marker(self):
        """Arrange: Token None. Act: mask_token. Assert: Trả "(rỗng)"."""
        # Note: Function checks `if not token` which catches None and empty string
        result = creds_module.mask_token(None)
        assert result == "(rỗng)"

    def test_mask_token_exactly_4_chars_all_dots(self):
        """Arrange: Token 4 ký tự. Act: mask_token. Assert: Toàn dấu chấm."""
        result = creds_module.mask_token("abcd")
        assert result == "••••"

    def test_mask_token_1_char_all_dots(self):
        """Arrange: Token 1 ký tự. Act: mask_token. Assert: Một dấu chấm."""
        result = creds_module.mask_token("x")
        assert result == "•"

    def test_mask_token_5_chars_1_dot_4_chars(self):
        """Arrange: Token 5 ký tự 'abcde'. Act: mask_token. Assert: '•bcde'."""
        result = creds_module.mask_token("abcde")
        assert result == "•bcde"

    def test_mask_token_16_char_token(self):
        """Arrange: Token 16 ký tự (típ real token). Act: mask_token. Assert: ••••••••••••[4 cuối]."""
        token = "a1b2c3d4e5f6g7h8"
        result = creds_module.mask_token(token)
        assert result.endswith("g7h8")
        assert result.startswith("•" * 12)


class TestLoadCredentials:
    """Test suite cho load_credentials(workspace_root=None) -> dict."""

    def test_load_credentials_valid_file_with_all_6_fields_returns_dict(self, tmp_path):
        """Arrange: credentials.json đầy đủ 6 field. Act: load_credentials. Assert: Trả dict 6 field."""
        # Arrange
        cred_dir = tmp_path / ".mattermost"
        cred_dir.mkdir()
        cred_file = cred_dir / "credentials.json"
        creds = {
            "mattermostUrl": "https://mm.nal.vn",
            "botName": "avatar",
            "botToken": "fake-token-1234",
            "teamId": "team-1",
            "defaultChannelId": "ch-1",
            "defaultChannelName": "general",
            "extra": "ignored",  # Extra field tự động bỏ qua
        }
        cred_file.write_text(json.dumps(creds), encoding="utf-8")

        # Act
        result = creds_module.load_credentials(workspace_root=str(tmp_path))

        # Assert
        assert len(result) == 6
        assert result["mattermostUrl"] == "https://mm.nal.vn"
        assert result["botName"] == "avatar"
        assert result["botToken"] == "fake-token-1234"
        assert result["teamId"] == "team-1"
        assert result["defaultChannelId"] == "ch-1"
        assert result["defaultChannelName"] == "general"
        assert "extra" not in result

    def test_load_credentials_missing_file_raises_credentials_error(self, tmp_path):
        """Arrange: Workspace không có credentials.json. Act: load_credentials. Assert: CredentialsError + msg VN."""
        # Act & Assert
        with pytest.raises(creds_module.CredentialsError) as exc_info:
            creds_module.load_credentials(workspace_root=str(tmp_path))

        error_msg = str(exc_info.value)
        assert "Không tìm thấy" in error_msg or "Thiếu credentials" in error_msg
        assert "comm-connect" in error_msg
        assert ".mattermost" in error_msg

    def test_load_credentials_invalid_json_raises_credentials_error(self, tmp_path):
        """Arrange: credentials.json có JSON sai. Act: load_credentials. Assert: CredentialsError + 'parse'."""
        # Arrange
        cred_dir = tmp_path / ".mattermost"
        cred_dir.mkdir()
        cred_file = cred_dir / "credentials.json"
        cred_file.write_text("{invalid json", encoding="utf-8")

        # Act & Assert
        with pytest.raises(creds_module.CredentialsError) as exc_info:
            creds_module.load_credentials(workspace_root=str(tmp_path))

        error_msg = str(exc_info.value)
        assert "parse" in error_msg.lower()
        assert "comm-connect" in error_msg

    def test_load_credentials_missing_single_field_raises_credentials_error(self, tmp_path):
        """Arrange: credentials.json thiếu 1 field (botToken). Act: load_credentials. Assert: CredentialsError + field name."""
        # Arrange
        cred_dir = tmp_path / ".mattermost"
        cred_dir.mkdir()
        cred_file = cred_dir / "credentials.json"
        creds = {
            "mattermostUrl": "https://mm.nal.vn",
            "botName": "avatar",
            # Missing botToken
            "teamId": "team-1",
            "defaultChannelId": "ch-1",
            "defaultChannelName": "general",
        }
        cred_file.write_text(json.dumps(creds), encoding="utf-8")

        # Act & Assert
        with pytest.raises(creds_module.CredentialsError) as exc_info:
            creds_module.load_credentials(workspace_root=str(tmp_path))

        error_msg = str(exc_info.value)
        assert "botToken" in error_msg
        assert "thiếu" in error_msg.lower() or "missing" in error_msg.lower()

    def test_load_credentials_missing_multiple_fields_raises_credentials_error(self, tmp_path):
        """Arrange: credentials.json thiếu 3 field. Act: load_credentials. Assert: CredentialsError list 3 field."""
        # Arrange
        cred_dir = tmp_path / ".mattermost"
        cred_dir.mkdir()
        cred_file = cred_dir / "credentials.json"
        creds = {
            "mattermostUrl": "https://mm.nal.vn",
            # Missing: botName, botToken, teamId
            "defaultChannelId": "ch-1",
            "defaultChannelName": "general",
        }
        cred_file.write_text(json.dumps(creds), encoding="utf-8")

        # Act & Assert
        with pytest.raises(creds_module.CredentialsError) as exc_info:
            creds_module.load_credentials(workspace_root=str(tmp_path))

        error_msg = str(exc_info.value)
        assert "botName" in error_msg and "botToken" in error_msg and "teamId" in error_msg

    def test_load_credentials_no_workspace_root_finds_credentials_upward(self, tmp_path):
        """Arrange: Gọi từ subdir, credentials ở parent dir. Act: load_credentials(None). Assert: Tìm được."""
        # Arrange
        cred_dir = tmp_path / ".mattermost"
        cred_dir.mkdir()
        cred_file = cred_dir / "credentials.json"
        creds = {
            "mattermostUrl": "https://mm.nal.vn",
            "botName": "avatar",
            "botToken": "fake-token",
            "teamId": "team-1",
            "defaultChannelId": "ch-1",
            "defaultChannelName": "general",
        }
        cred_file.write_text(json.dumps(creds), encoding="utf-8")

        subdir = tmp_path / "specs" / "nested"
        subdir.mkdir(parents=True)

        # Mock CWD về subdir
        with patch("pathlib.Path.cwd", return_value=subdir):
            # Act
            result = creds_module.load_credentials(workspace_root=None)

        # Assert
        assert result["botName"] == "avatar"

    def test_load_credentials_file_with_empty_field_raises_credentials_error(self, tmp_path):
        """Arrange: credentials.json có botToken = "". Act: load_credentials. Assert: CredentialsError."""
        # Arrange
        cred_dir = tmp_path / ".mattermost"
        cred_dir.mkdir()
        cred_file = cred_dir / "credentials.json"
        creds = {
            "mattermostUrl": "https://mm.nal.vn",
            "botName": "avatar",
            "botToken": "",  # Empty
            "teamId": "team-1",
            "defaultChannelId": "ch-1",
            "defaultChannelName": "general",
        }
        cred_file.write_text(json.dumps(creds), encoding="utf-8")

        # Act & Assert
        with pytest.raises(creds_module.CredentialsError) as exc_info:
            creds_module.load_credentials(workspace_root=str(tmp_path))

        assert "botToken" in str(exc_info.value)


# ╔══════════════════════════════════════════════════════════════════════════╗
# ║ Tests: mattermost_api_http_client_with_bearer_auth                       ║
# ╚══════════════════════════════════════════════════════════════════════════╝


class TestMattermostClientFriendly:
    """Test suite cho MattermostClient._friendly(code, body) -> str."""

    def test_mattermost_client_friendly_401_returns_token_error_message(self):
        """Arrange: HTTP 401. Act: _friendly(401, ...). Assert: Message về token sai + comm-connect."""
        result = client_module.MattermostClient._friendly(401, "Unauthorized")
        assert "Token" in result and ("sai" in result.lower() or "hết hạn" in result.lower())
        assert "401" in result
        assert "comm-connect" in result

    def test_mattermost_client_friendly_403_returns_permission_error_message(self):
        """Arrange: HTTP 403. Act: _friendly(403, ...). Assert: Message về quyền/team + admin."""
        result = client_module.MattermostClient._friendly(403, "Forbidden")
        assert ("quyền" in result.lower() or "permission" in result.lower())
        assert ("team" in result.lower() or "channel" in result.lower())
        assert "403" in result

    def test_mattermost_client_friendly_404_returns_not_found_message(self):
        """Arrange: HTTP 404 + body "card not found". Act: _friendly(404, body). Assert: 404 + body."""
        body = "Card not found"
        result = client_module.MattermostClient._friendly(404, body)
        assert "404" in result
        assert body in result

    def test_mattermost_client_friendly_422_returns_validation_error_message(self):
        """Arrange: HTTP 422 + body JSON. Act: _friendly(422, body). Assert: 422 + body."""
        body = '{"error":"Invalid field"}'
        result = client_module.MattermostClient._friendly(422, body)
        assert "422" in result
        assert "Invalid field" in result

    def test_mattermost_client_friendly_500_generic_error_message(self):
        """Arrange: HTTP 500. Act: _friendly(500, body). Assert: 500 + generic message."""
        result = client_module.MattermostClient._friendly(500, "Internal error")
        assert "500" in result
        assert "Internal error" in result

    def test_mattermost_client_friendly_400_session_error_returns_vietnamese_token_message(self):
        """Arrange: HTTP 400 + body session error (kanban plugin bad-token case).
        Act: _friendly(400, body).
        Assert: Message tiếng Việt về token/comm-connect, KHÔNG lộ nguyên văn tiếng Anh."""
        body = "We encountered an error finding the session."
        result = client_module.MattermostClient._friendly(400, body)
        assert "Token" in result and ("sai" in result.lower() or "hết hạn" in result.lower())
        assert "comm-connect" in result
        assert "finding the session" not in result

    def test_mattermost_client_friendly_400_non_session_falls_through_to_generic(self):
        """Arrange: HTTP 400 + body KHÔNG liên quan session (vd validation lỗi field).
        Act: _friendly(400, body).
        Assert: Rơi vào generic fallthrough (chứa 400 + body), không bị nuốt bởi nhánh session."""
        body = "invalid field foo"
        result = client_module.MattermostClient._friendly(400, body)
        assert "400" in result
        assert body in result


class TestMattermostClientInit:
    """Test suite cho MattermostClient.__init__()."""

    def test_mattermost_client_init_stores_base_url_token_team_id(self):
        """Arrange: Init với URL + token + teamId. Act: Tạo client. Assert: Lưu đúng giá trị."""
        # Arrange
        base_url = "https://mm.nal.vn"
        token = "fake-token-abc"
        team_id = "team-xyz"

        # Act
        client = client_module.MattermostClient(base_url, token, team_id)

        # Assert
        assert client.base_url == base_url
        assert client._token == token
        assert client.team_id == team_id

    def test_mattermost_client_init_strips_trailing_slash_from_base_url(self):
        """Arrange: URL có trailing slash. Act: Init. Assert: Slash bị xoá."""
        # Arrange
        base_url = "https://mm.nal.vn/"

        # Act
        client = client_module.MattermostClient(base_url, "token", "team")

        # Assert
        assert client.base_url == "https://mm.nal.vn"

    def test_mattermost_client_init_multiple_trailing_slashes(self):
        """Arrange: URL có 3 trailing slash. Act: Init. Assert: Tất cả xoá."""
        base_url = "https://mm.nal.vn///"
        client = client_module.MattermostClient(base_url, "token", "team")
        assert client.base_url == "https://mm.nal.vn"

    # ── P2 A3 — URL hardening (ép https cho host non-local; KHÔNG allowlist) ──

    def test_mattermost_client_init_accepts_https_mm_nal_vn_with_port(self):
        """Arrange: https mm.nal.vn:443. Act: Init. Assert: KHÔNG raise."""
        client = client_module.MattermostClient("https://mm.nal.vn:443", "token", "team")
        assert client.base_url == "https://mm.nal.vn:443"

    def test_mattermost_client_init_rejects_http_mm_nal_vn_tls_downgrade(self):
        """Arrange: http mm.nal.vn (non-local). Act+Assert: raise ValueError (chống TLS downgrade)."""
        with pytest.raises(ValueError, match="https"):
            client_module.MattermostClient("http://mm.nal.vn", "token", "team")

    def test_mattermost_client_init_accepts_arbitrary_https_chatops_host(self):
        """Arrange: https host chatops khác (ghi đè D1 2026-09-21). Act: Init. Assert: KHÔNG raise."""
        client = client_module.MattermostClient("https://app.chatops.vn", "token", "team")
        assert client.base_url == "https://app.chatops.vn"

    def test_mattermost_client_init_accepts_arbitrary_https_host_with_custom_port(self):
        """Arrange: https host tuỳ ý + port lạ. Act: Init. Assert: KHÔNG raise."""
        client = client_module.MattermostClient("https://chat.example.com:8443", "token", "team")
        assert client.base_url == "https://chat.example.com:8443"

    def test_mattermost_client_init_rejects_http_arbitrary_host_tls_downgrade(self):
        """Arrange: http host non-local tuỳ ý. Act+Assert: raise (https vẫn bắt buộc)."""
        with pytest.raises(ValueError, match="https"):
            client_module.MattermostClient("http://app.chatops.vn", "token", "team")

    def test_mattermost_client_init_rejects_garbage_url(self):
        """Arrange: URL rác không parse ra host. Act+Assert: reject."""
        with pytest.raises(ValueError, match="không hợp lệ|host"):
            client_module.MattermostClient("not a url", "token", "team")

    def test_mattermost_client_init_allows_http_localhost_dev(self):
        """Arrange: http localhost:8065 (dev, D1). Act: Init. Assert: KHÔNG raise."""
        client = client_module.MattermostClient("http://localhost:8065", "token", "team")
        assert client.base_url == "http://localhost:8065"

    def test_mattermost_client_init_allows_http_loopback_ip_dev(self):
        """Arrange: http 127.0.0.1:8065 (dev, D1). Act: Init. Assert: KHÔNG raise."""
        client = client_module.MattermostClient("http://127.0.0.1:8065", "token", "team")
        assert client.base_url == "http://127.0.0.1:8065"


class TestMattermostClientHeaders:
    """Test suite cho MattermostClient._headers()."""

    def test_mattermost_client_headers_includes_bearer_token(self):
        """Arrange: Client với token. Act: _headers(). Assert: Authorization header + Bearer."""
        client = client_module.MattermostClient("https://mm.nal.vn", "mytoken123", "team")
        headers = client._headers()

        assert "Authorization" in headers
        assert headers["Authorization"] == "Bearer mytoken123"

    def test_mattermost_client_headers_includes_x_requested_with(self):
        """Arrange: Client. Act: _headers(). Assert: X-Requested-With = XMLHttpRequest."""
        client = client_module.MattermostClient("https://mm.nal.vn", "token", "team")
        headers = client._headers()

        assert "X-Requested-With" in headers
        assert headers["X-Requested-With"] == "XMLHttpRequest"

    def test_mattermost_client_headers_merges_extra_headers(self):
        """Arrange: Client. Act: _headers(extra={'X-Custom': 'val'}). Assert: Custom header merged."""
        client = client_module.MattermostClient("https://mm.nal.vn", "token", "team")
        headers = client._headers(extra={"X-Custom": "value"})

        assert headers["X-Custom"] == "value"
        assert headers["Authorization"] == "Bearer token"


class TestBuildCardEditPayload:
    """Test suite cho build_card_edit_payload(card, **overrides) -> dict."""

    def test_build_card_edit_payload_happy_path_all_fields(self):
        """Arrange: Card board-shape đầy đủ + override file_ids. Act: build payload. Assert: snake_case payload."""
        # Arrange
        card = {
            "id": "card-1",
            "title": "Task 1",
            "description": "Old description",
            "reminder": 0,
            "isComplete": False,
            "ownerOnly": False,
            "deadline": "2024-12-31",
            "fileIds": ["file-1"],
            "tags": ["tag1"],
            "assignUsers": ["user1"],
            "data": {
                "tags": ["tag1"],
                "assignUsers": ["user1"],
            },
        }

        # Act
        result = client_module.build_card_edit_payload(
            card,
            file_ids=["file-2", "file-3"],
            description="New description",
            tags=["tag2"],
            assign_users=["user2", "user3"],
        )

        # Assert
        assert result["id"] == "card-1"
        assert result["title"] == "Task 1"
        assert result["description"] == "New description"
        assert result["file_ids"] == ["file-2", "file-3"]  # snake_case
        assert result["is_complete"] is False  # snake_case
        assert result["data"]["tags"] == ["tag2"]
        assert result["data"]["assignUsers"] == ["user2", "user3"]

    def test_build_card_edit_payload_preserves_fields_when_override_is_none(self):
        """Arrange: Card + no override cho description. Act: build payload. Assert: Description giữ nguyên."""
        # Arrange
        card = {
            "id": "card-1",
            "title": "Task",
            "description": "Original description",
            "reminder": 0,
            "isComplete": True,
            "ownerOnly": False,
            "deadline": "",
            "fileIds": ["f1"],
        }

        # Act
        result = client_module.build_card_edit_payload(card, description=None)

        # Assert
        assert result["description"] == "Original description"

    def test_build_card_edit_payload_empty_description_override_works(self):
        """Arrange: Card + override description="". Act: build payload. Assert: Description=""."""
        card = {
            "id": "card-1",
            "title": "Task",
            "description": "Old",
            "reminder": 0,
            "isComplete": False,
            "ownerOnly": False,
            "deadline": "",
            "fileIds": [],
        }

        result = client_module.build_card_edit_payload(card, description="")
        assert result["description"] == ""

    def test_build_card_edit_payload_tags_override_replaces_original(self):
        """Arrange: Card có tags, override với tags baru. Act: build payload. Assert: Tags baru."""
        card = {
            "id": "c1",
            "title": "T",
            "description": "",
            "reminder": 0,
            "isComplete": False,
            "ownerOnly": False,
            "deadline": "",
            "fileIds": [],
            "data": {"tags": ["old1", "old2"], "assignUsers": []},
        }

        result = client_module.build_card_edit_payload(card, tags=["new1"])
        assert result["data"]["tags"] == ["new1"]

    def test_build_card_edit_payload_assign_users_override(self):
        """Arrange: Card có assignUsers, override. Act: build payload. Assert: assignUsers mới."""
        card = {
            "id": "c1",
            "title": "T",
            "description": "",
            "reminder": 0,
            "isComplete": False,
            "ownerOnly": False,
            "deadline": "",
            "fileIds": [],
            "data": {"tags": [], "assignUsers": ["user-old"]},
        }

        result = client_module.build_card_edit_payload(card, assign_users=["user-new1", "user-new2"])
        assert result["data"]["assignUsers"] == ["user-new1", "user-new2"]

    def test_build_card_edit_payload_file_ids_override(self):
        """Arrange: Card có fileIds, override với rỗng. Act: build payload. Assert: file_ids=[]."""
        card = {
            "id": "c1",
            "title": "T",
            "description": "",
            "reminder": 0,
            "isComplete": False,
            "ownerOnly": False,
            "deadline": "",
            "fileIds": ["old-file"],
        }

        result = client_module.build_card_edit_payload(card, file_ids=[])
        assert result["file_ids"] == []

    def test_build_card_edit_payload_no_data_field_uses_empty_dict(self):
        """Arrange: Card KHÔNG có 'data' field. Act: build payload. Assert: data = {tags:[], assignUsers:[]}."""
        card = {
            "id": "c1",
            "title": "T",
            "description": "",
            "reminder": 0,
            "isComplete": False,
            "ownerOnly": False,
            "deadline": "",
            "fileIds": [],
            # No 'data' field
        }

        result = client_module.build_card_edit_payload(card)
        assert result["data"]["tags"] == []
        assert result["data"]["assignUsers"] == []

    def test_build_card_edit_payload_data_is_dict_uses_it_as_base(self):
        """Arrange: Card.data = {}. Act: build payload. Assert: data dùng dict rỗng."""
        card = {
            "id": "c1",
            "title": "T",
            "description": "",
            "reminder": 0,
            "isComplete": False,
            "ownerOnly": False,
            "deadline": "",
            "fileIds": [],
            "data": {},
        }

        result = client_module.build_card_edit_payload(card)
        assert "tags" in result["data"]
        assert "assignUsers" in result["data"]

    def test_build_card_edit_payload_is_complete_converts_camel_case(self):
        """Arrange: Card isComplete=True (camelCase). Act: build payload. Assert: is_complete=True (snake_case)."""
        card = {
            "id": "c1",
            "title": "T",
            "description": "",
            "reminder": 0,
            "isComplete": True,  # camelCase
            "ownerOnly": False,
            "deadline": "",
            "fileIds": [],
        }

        result = client_module.build_card_edit_payload(card)
        assert "is_complete" in result  # snake_case
        assert result["is_complete"] is True
        assert "isComplete" not in result


class TestResolveFileNames:
    """Test suite cho MattermostClient.resolve_file_names(file_ids) -> [{id,name}]."""

    def test_resolve_file_names_single_file_returns_real_name(self, monkeypatch):
        """Arrange: 1 file_id, get_json trả {"name": "hello-world.html"}.
        Act: resolve_file_names. Assert: [{"id","name":"hello-world.html"}].
        """
        client = client_module.MattermostClient("https://mm.nal.vn", "token", "team")
        monkeypatch.setattr(
            client_module.MattermostClient, "get_json",
            lambda self, path: {"name": "hello-world.html", "size": 221},
        )

        result = client.resolve_file_names(["sk4qcqch123"])

        assert result == [{"id": "sk4qcqch123", "name": "hello-world.html"}]

    def test_resolve_file_names_api_error_falls_back_to_short_id(self, monkeypatch):
        """Arrange: get_json raises MattermostApiError (vd 404). Act: resolve_file_names.
        Assert: fallback {"id","name": id[:8]+'…'}, KHÔNG raise, list vẫn trả đủ."""
        client = client_module.MattermostClient("https://mm.nal.vn", "token", "team")

        def raise_error(self, path):
            raise client_module.MattermostApiError("Không tìm thấy tài nguyên (404)")

        monkeypatch.setattr(client_module.MattermostClient, "get_json", raise_error)

        result = client.resolve_file_names(["abcdefgh12345678"])

        assert result == [{"id": "abcdefgh12345678", "name": "abcdefgh…"}]

    def test_resolve_file_names_one_file_error_does_not_break_others(self, monkeypatch):
        """Arrange: 2 files — file 1 lỗi, file 2 OK. Act: resolve_file_names.
        Assert: file 1 fallback, file 2 tên thật — 1 lỗi không hỏng cả list."""
        client = client_module.MattermostClient("https://mm.nal.vn", "token", "team")

        def fake_get_json(self, path):
            if "bad-file" in path:
                raise client_module.MattermostApiError("404")
            return {"name": "good-file.pdf"}

        monkeypatch.setattr(client_module.MattermostClient, "get_json", fake_get_json)

        result = client.resolve_file_names(["bad-file-id", "good-file-id"])

        assert result[0]["name"] == "bad-file…"
        assert result[1]["name"] == "good-file.pdf"

    def test_resolve_file_names_empty_list_returns_empty_list(self):
        """Arrange: file_ids rỗng. Act: resolve_file_names. Assert: trả []."""
        client = client_module.MattermostClient("https://mm.nal.vn", "token", "team")
        result = client.resolve_file_names([])
        assert result == []


class TestMattermostClientKanbanBase:
    """Test suite cho MattermostClient.kanban_base()."""

    def test_mattermost_client_kanban_base_appends_plugin_path(self):
        """Arrange: Client với URL. Act: kanban_base(). Assert: URL + /plugins/chatops-kanban-plugin."""
        client = client_module.MattermostClient("https://mm.nal.vn", "token", "team")
        result = client.kanban_base()
        assert result == "https://mm.nal.vn/plugins/chatops-kanban-plugin"

    def test_mattermost_client_kanban_base_no_double_slash(self):
        """Arrange: Base URL không có trailing slash. Act: kanban_base(). Assert: Không double slash."""
        client = client_module.MattermostClient("https://mm.nal.vn", "token", "team")
        result = client.kanban_base()
        assert "//" not in result.replace("https://", "")  # Allow https:// but no others


# ╔══════════════════════════════════════════════════════════════════════════╗
# ║ Integration tests: Delivery map hash (logic thuần, dễ mock)              ║
# ╚══════════════════════════════════════════════════════════════════════════╝


class TestDeliveryMapHash:
    """Test suite cho sha256 hash logic từ delivery-map script."""

    def test_delivery_map_sha256_generates_valid_hash_format(self, tmp_path):
        """Arrange: File spec. Act: Tính sha256. Assert: Format 'sha256:hexstring'."""
        # Arrange
        spec_file = tmp_path / "spec.md"
        spec_file.write_text("# Spec content", encoding="utf-8")

        # Act
        import hashlib
        content = spec_file.read_bytes()
        h = hashlib.sha256(content).hexdigest()
        result = f"sha256:{h}"

        # Assert
        assert result.startswith("sha256:")
        assert len(result) == 7 + 64  # "sha256:" (7) + hex (64)

    def test_delivery_map_sha256_different_files_different_hashes(self, tmp_path):
        """Arrange: 2 files khác nhau. Act: Hash cả 2. Assert: Hash khác nhau."""
        # Arrange
        file1 = tmp_path / "file1.md"
        file2 = tmp_path / "file2.md"
        file1.write_text("Content A", encoding="utf-8")
        file2.write_text("Content B", encoding="utf-8")

        # Act
        import hashlib
        h1 = hashlib.sha256(file1.read_bytes()).hexdigest()
        h2 = hashlib.sha256(file2.read_bytes()).hexdigest()

        # Assert
        assert h1 != h2

    def test_delivery_map_sha256_same_content_same_hash(self, tmp_path):
        """Arrange: 2 files nội dung giống. Act: Hash cả 2. Assert: Hash giống."""
        # Arrange
        file1 = tmp_path / "file1.md"
        file2 = tmp_path / "file2.md"
        content = "Same content"
        file1.write_text(content, encoding="utf-8")
        file2.write_text(content, encoding="utf-8")

        # Act
        import hashlib
        h1 = hashlib.sha256(file1.read_bytes()).hexdigest()
        h2 = hashlib.sha256(file2.read_bytes()).hexdigest()

        # Assert
        assert h1 == h2


# ╔══════════════════════════════════════════════════════════════════════════╗
# ║ Edge cases & error scenarios                                             ║
# ╚══════════════════════════════════════════════════════════════════════════╝


class TestMattermostClientEdgeCases:
    """Test suite cho edge cases trong HTTP client."""

    def test_mattermost_client_url_construction_with_absolute_path(self):
        """Arrange: Client. Act: _url(path) với absolute URL. Assert: Return absolute URL."""
        client = client_module.MattermostClient("https://mm.nal.vn", "token", "team")
        result = client._url("https://other.com/path")
        assert result == "https://other.com/path"

    def test_mattermost_client_url_construction_with_relative_path(self):
        """Arrange: Client. Act: _url('/api/v4/...'). Assert: Prepend base_url."""
        client = client_module.MattermostClient("https://mm.nal.vn", "token", "team")
        result = client._url("/api/v4/teams")
        assert result == "https://mm.nal.vn/api/v4/teams"

    def test_mattermost_client_url_construction_no_leading_slash(self):
        """Arrange: Client. Act: _url('api/v4/...'). Assert: Prepend base_url."""
        client = client_module.MattermostClient("https://mm.nal.vn", "token", "team")
        result = client._url("api/v4/teams")
        assert result == "https://mm.nal.vn" + "api/v4/teams"


class TestCredentialsErrorExceptionHandling:
    """Test suite cho CredentialsError exception."""

    def test_credentials_error_is_exception(self):
        """Arrange: CredentialsError. Act: Raise. Assert: Catchable as Exception."""
        with pytest.raises(Exception):
            raise creds_module.CredentialsError("Test error")

    def test_credentials_error_message_Vietnamese(self):
        """Arrange: Raise CredentialsError. Act: Catch. Assert: Message tiếng Việt."""
        try:
            raise creds_module.CredentialsError("Lỗi: Thiếu field")
        except creds_module.CredentialsError as e:
            assert "Thiếu field" in str(e)


class TestMattermostApiErrorExceptionHandling:
    """Test suite cho MattermostApiError exception."""

    def test_mattermost_api_error_is_exception(self):
        """Arrange: MattermostApiError. Act: Raise. Assert: Catchable as Exception."""
        with pytest.raises(Exception):
            raise client_module.MattermostApiError("API error")

    def test_mattermost_api_error_message(self):
        """Arrange: Raise MattermostApiError. Act: Catch. Assert: Message preserved."""
        try:
            raise client_module.MattermostApiError("Token sai (401)")
        except client_module.MattermostApiError as e:
            assert "Token" in str(e)


# ╔══════════════════════════════════════════════════════════════════════════╗
# ║ Tests: mattermost-list-channel-members-for-assignee-resolve entry script ║
# ╚══════════════════════════════════════════════════════════════════════════╝
# Ported từ po-ai-pack (07/07) cho /avatar:specs:done resolve assignee.


class TestListChannelMembersScript:
    """Test suite cho member list logic: filter bots + build member dict.

    Script mattermost-list-channel-members-for-assignee-resolve.py:
    1. GET /api/v4/users?in_channel={channelId}
    2. Filter out is_bot=True (kể cả @avatar)
    3. Build dict {"username", "fullName", "nickname"} (fullName = first+last)
    4. Return JSON list

    Strategy: Import entry script via importlib, monkeypatch client.get_json,
    call main() & check stdout JSON.
    """

    def test_list_members_filters_out_bots(self, capsys, tmp_path, monkeypatch):
        """Arrange: API trả 3 user (2 human + 1 bot @avatar). Act: Parse members.
        Assert: Bot filtered out, result có 2 member.
        """
        # Arrange
        import importlib.util
        entry_file = Path(__file__).parent.parent / "mattermost-list-channel-members-for-assignee-resolve.py"
        spec = importlib.util.spec_from_file_location("list_members_entry", entry_file)
        list_members_module = importlib.util.module_from_spec(spec)

        api_users = [
            {"username": "hung", "first_name": "Hùng", "last_name": "Nguyễn", "nickname": "Hun", "is_bot": False},
            {"username": "avatar", "first_name": "avatar", "last_name": "", "nickname": "", "is_bot": True},
            {"username": "minh", "first_name": "Minh", "last_name": "Pham", "nickname": "MP", "is_bot": False},
        ]

        # Mock credentials & client
        fake_creds = {
            "mattermostUrl": "https://mm.nal.vn",
            "botToken": "fake-token",
            "teamId": "team-1",
            "defaultChannelId": "ch-1",
        }

        def mock_load_creds():
            return fake_creds

        def mock_client_get_json(self, path):
            return api_users

        monkeypatch.setattr(
            "mattermost_credentials_reader_and_token_masker.load_credentials",
            mock_load_creds,
        )
        monkeypatch.setattr(
            "mattermost_api_http_client_with_bearer_auth.MattermostClient.get_json",
            mock_client_get_json,
        )

        # Act
        spec.loader.exec_module(list_members_module)
        result_code = list_members_module.main()
        captured = capsys.readouterr()
        members = json.loads(captured.out)

        # Assert
        assert result_code == 0
        assert len(members) == 2  # Bot filtered
        usernames = [m["username"] for m in members]
        assert "avatar" not in usernames
        assert "hung" in usernames and "minh" in usernames

    def test_list_members_builds_fullname_from_first_and_last(self, capsys, tmp_path, monkeypatch):
        """Arrange: User có first_name='Hùng' + last_name='Nguyễn'. Act: Build fullName.
        Assert: fullName = 'Hùng Nguyễn'.
        """
        import importlib.util
        entry_file = Path(__file__).parent.parent / "mattermost-list-channel-members-for-assignee-resolve.py"
        spec = importlib.util.spec_from_file_location("list_members_entry", entry_file)
        list_members_module = importlib.util.module_from_spec(spec)

        api_users = [
            {"username": "hung", "first_name": "Hùng", "last_name": "Nguyễn", "nickname": "Hun", "is_bot": False},
        ]

        fake_creds = {
            "mattermostUrl": "https://mm.nal.vn",
            "botToken": "fake-token",
            "teamId": "team-1",
            "defaultChannelId": "ch-1",
        }

        monkeypatch.setattr(
            "mattermost_credentials_reader_and_token_masker.load_credentials",
            lambda: fake_creds,
        )
        monkeypatch.setattr(
            "mattermost_api_http_client_with_bearer_auth.MattermostClient.get_json",
            lambda self, path: api_users,
        )

        # Act
        spec.loader.exec_module(list_members_module)
        result_code = list_members_module.main()
        captured = capsys.readouterr()
        members = json.loads(captured.out)

        # Assert
        assert result_code == 0
        assert members[0]["fullName"] == "Hùng Nguyễn"
        assert members[0]["username"] == "hung"
        assert members[0]["nickname"] == "Hun"

    def test_list_members_handles_user_with_only_firstname(self, capsys, tmp_path, monkeypatch):
        """Arrange: User có first_name='Hùng' nhưng last_name=None/rỗng. Act: Build fullName.
        Assert: fullName = 'Hùng' (chỉ first_name).
        """
        import importlib.util
        entry_file = Path(__file__).parent.parent / "mattermost-list-channel-members-for-assignee-resolve.py"
        spec = importlib.util.spec_from_file_location("list_members_entry", entry_file)
        list_members_module = importlib.util.module_from_spec(spec)

        api_users = [
            {"username": "hung", "first_name": "Hùng", "last_name": "", "nickname": "Hun", "is_bot": False},
        ]

        fake_creds = {
            "mattermostUrl": "https://mm.nal.vn",
            "botToken": "fake-token",
            "teamId": "team-1",
            "defaultChannelId": "ch-1",
        }

        monkeypatch.setattr(
            "mattermost_credentials_reader_and_token_masker.load_credentials",
            lambda: fake_creds,
        )
        monkeypatch.setattr(
            "mattermost_api_http_client_with_bearer_auth.MattermostClient.get_json",
            lambda self, path: api_users,
        )

        # Act
        spec.loader.exec_module(list_members_module)
        result_code = list_members_module.main()
        captured = capsys.readouterr()
        members = json.loads(captured.out)

        # Assert
        assert result_code == 0
        assert members[0]["fullName"] == "Hùng"

    def test_list_members_handles_user_with_only_lastname(self, capsys, tmp_path, monkeypatch):
        """Arrange: User có last_name='Nguyễn' nhưng first_name=None/rỗng. Act: Build fullName.
        Assert: fullName = 'Nguyễn'.
        """
        import importlib.util
        entry_file = Path(__file__).parent.parent / "mattermost-list-channel-members-for-assignee-resolve.py"
        spec = importlib.util.spec_from_file_location("list_members_entry", entry_file)
        list_members_module = importlib.util.module_from_spec(spec)

        api_users = [
            {"username": "nguyen", "first_name": "", "last_name": "Nguyễn", "nickname": "", "is_bot": False},
        ]

        fake_creds = {
            "mattermostUrl": "https://mm.nal.vn",
            "botToken": "fake-token",
            "teamId": "team-1",
            "defaultChannelId": "ch-1",
        }

        monkeypatch.setattr(
            "mattermost_credentials_reader_and_token_masker.load_credentials",
            lambda: fake_creds,
        )
        monkeypatch.setattr(
            "mattermost_api_http_client_with_bearer_auth.MattermostClient.get_json",
            lambda self, path: api_users,
        )

        # Act
        spec.loader.exec_module(list_members_module)
        result_code = list_members_module.main()
        captured = capsys.readouterr()
        members = json.loads(captured.out)

        # Assert
        assert result_code == 0
        assert members[0]["fullName"] == "Nguyễn"

    def test_list_members_handles_user_with_no_firstname_or_lastname(self, capsys, tmp_path, monkeypatch):
        """Arrange: User không có first_name và last_name (rỗng). Act: Build fullName.
        Assert: fullName = '' (rỗng, OK per spec).
        """
        import importlib.util
        entry_file = Path(__file__).parent.parent / "mattermost-list-channel-members-for-assignee-resolve.py"
        spec = importlib.util.spec_from_file_location("list_members_entry", entry_file)
        list_members_module = importlib.util.module_from_spec(spec)

        api_users = [
            {"username": "bot_user", "first_name": "", "last_name": "", "nickname": "botname", "is_bot": False},
        ]

        fake_creds = {
            "mattermostUrl": "https://mm.nal.vn",
            "botToken": "fake-token",
            "teamId": "team-1",
            "defaultChannelId": "ch-1",
        }

        monkeypatch.setattr(
            "mattermost_credentials_reader_and_token_masker.load_credentials",
            lambda: fake_creds,
        )
        monkeypatch.setattr(
            "mattermost_api_http_client_with_bearer_auth.MattermostClient.get_json",
            lambda self, path: api_users,
        )

        # Act
        spec.loader.exec_module(list_members_module)
        result_code = list_members_module.main()
        captured = capsys.readouterr()
        members = json.loads(captured.out)

        # Assert
        assert result_code == 0
        assert members[0]["fullName"] == ""
        assert members[0]["nickname"] == "botname"

    def test_list_members_returns_2_on_credentials_error(self, capsys, monkeypatch):
        """Arrange: load_credentials() raises CredentialsError. Act: main().
        Assert: Exit code 2 + error on stderr.
        """
        import importlib.util
        entry_file = Path(__file__).parent.parent / "mattermost-list-channel-members-for-assignee-resolve.py"
        spec = importlib.util.spec_from_file_location("list_members_entry", entry_file)
        list_members_module = importlib.util.module_from_spec(spec)

        def raise_creds_error():
            raise creds_module.CredentialsError("Credentials missing")

        monkeypatch.setattr(
            "mattermost_credentials_reader_and_token_masker.load_credentials",
            raise_creds_error,
        )

        # Act
        spec.loader.exec_module(list_members_module)
        result_code = list_members_module.main()
        captured = capsys.readouterr()

        # Assert
        assert result_code == 2
        assert "Credentials missing" in captured.err

    def test_list_members_returns_2_on_api_error(self, capsys, monkeypatch):
        """Arrange: client.get_json() raises MattermostApiError. Act: main().
        Assert: Exit code 2 + error on stderr.
        """
        import importlib.util
        entry_file = Path(__file__).parent.parent / "mattermost-list-channel-members-for-assignee-resolve.py"
        spec = importlib.util.spec_from_file_location("list_members_entry", entry_file)
        list_members_module = importlib.util.module_from_spec(spec)

        fake_creds = {
            "mattermostUrl": "https://mm.nal.vn",
            "botToken": "fake-token",
            "teamId": "team-1",
            "defaultChannelId": "ch-1",
        }

        def raise_api_error(self, path):
            raise client_module.MattermostApiError("Connection timeout")

        monkeypatch.setattr(
            "mattermost_credentials_reader_and_token_masker.load_credentials",
            lambda: fake_creds,
        )
        monkeypatch.setattr(
            "mattermost_api_http_client_with_bearer_auth.MattermostClient.get_json",
            raise_api_error,
        )

        # Act
        spec.loader.exec_module(list_members_module)
        result_code = list_members_module.main()
        captured = capsys.readouterr()

        # Assert
        assert result_code == 2
        assert "Connection timeout" in captured.err

    def test_list_members_json_output_includes_all_required_fields(self, capsys, monkeypatch):
        """Arrange: API trả user đầy đủ. Act: main() output JSON. Assert: JSON valid + all 3 fields."""
        import importlib.util
        entry_file = Path(__file__).parent.parent / "mattermost-list-channel-members-for-assignee-resolve.py"
        spec = importlib.util.spec_from_file_location("list_members_entry", entry_file)
        list_members_module = importlib.util.module_from_spec(spec)

        api_users = [
            {"username": "alice", "first_name": "Alice", "last_name": "Smith", "nickname": "AS", "is_bot": False},
        ]

        fake_creds = {
            "mattermostUrl": "https://mm.nal.vn",
            "botToken": "fake-token",
            "teamId": "team-1",
            "defaultChannelId": "ch-1",
        }

        monkeypatch.setattr(
            "mattermost_credentials_reader_and_token_masker.load_credentials",
            lambda: fake_creds,
        )
        monkeypatch.setattr(
            "mattermost_api_http_client_with_bearer_auth.MattermostClient.get_json",
            lambda self, path: api_users,
        )

        # Act
        spec.loader.exec_module(list_members_module)
        result_code = list_members_module.main()
        captured = capsys.readouterr()
        members = json.loads(captured.out)

        # Assert
        assert result_code == 0
        assert len(members) == 1
        member = members[0]
        assert "username" in member
        assert "fullName" in member
        assert "nickname" in member
        assert set(member.keys()) == {"username", "fullName", "nickname"}


# ╔══════════════════════════════════════════════════════════════════════════╗
# ║ Tests: kanban-board-digest-fetch-and-summarize                          ║
# ╚══════════════════════════════════════════════════════════════════════════╝


class TestKanbanBoardDigest:
    """Test suite cho kanban-board-digest-fetch-and-summarize.py — digest logic."""

    def test_digest_calculates_lanes_count_correctly(self, capsys, monkeypatch):
        """Arrange: Board có 2 lanes (Todo=3 cards, InProgress=1). Act: digest.
        Assert: lanes_count={Todo: 3, InProgress: 1}, total=4.
        """
        import importlib.util
        entry_file = Path(__file__).parent.parent / "kanban-board-digest-fetch-and-summarize.py"
        spec = importlib.util.spec_from_file_location("digest_entry", entry_file)
        digest_module = importlib.util.module_from_spec(spec)

        fake_board = {
            "lanes": [
                {
                    "id": "lane-1",
                    "title": "Todo",
                    "cards": [
                        {"id": "c1", "title": "Card 1", "assignUsers": []},
                        {"id": "c2", "title": "Card 2", "assignUsers": ["user1"]},
                        {"id": "c3", "title": "Card 3", "assignUsers": []},
                    ],
                },
                {
                    "id": "lane-2",
                    "title": "InProgress",
                    "cards": [
                        {"id": "c4", "title": "Card 4", "assignUsers": ["user1"]},
                    ],
                },
            ],
        }

        fake_creds = {
            "mattermostUrl": "https://mm.nal.vn",
            "botToken": "fake-token",
            "teamId": "team-1",
            "defaultChannelId": "ch-1",
        }

        monkeypatch.setattr(
            "mattermost_credentials_reader_and_token_masker.load_credentials",
            lambda: fake_creds,
        )
        monkeypatch.setattr(
            "mattermost_api_http_client_with_bearer_auth.MattermostClient.get_json",
            lambda self, path: fake_board,
        )

        # Act
        spec.loader.exec_module(digest_module)
        result_code = digest_module.main()
        captured = capsys.readouterr()
        digest = json.loads(captured.out)

        # Assert
        assert result_code == 0
        assert digest["lanes"]["Todo"] == 3
        assert digest["lanes"]["InProgress"] == 1
        assert digest["total"] == 4

    def test_digest_counts_waiting_assigned_in_todo_lane(self, capsys, monkeypatch):
        """Arrange: Todo lane có 2 cards: 1 với assignUsers, 1 không.
        Act: digest. Assert: waiting_assigned=1.
        """
        import importlib.util
        entry_file = Path(__file__).parent.parent / "kanban-board-digest-fetch-and-summarize.py"
        spec = importlib.util.spec_from_file_location("digest_entry", entry_file)
        digest_module = importlib.util.module_from_spec(spec)

        fake_board = {
            "lanes": [
                {
                    "id": "lane-1",
                    "title": "Todo",
                    "cards": [
                        {"id": "c1", "title": "Card 1", "assignUsers": ["user1"]},
                        {"id": "c2", "title": "Card 2", "assignUsers": []},
                    ],
                },
            ],
        }

        fake_creds = {
            "mattermostUrl": "https://mm.nal.vn",
            "botToken": "fake-token",
            "teamId": "team-1",
            "defaultChannelId": "ch-1",
        }

        monkeypatch.setattr(
            "mattermost_credentials_reader_and_token_masker.load_credentials",
            lambda: fake_creds,
        )
        monkeypatch.setattr(
            "mattermost_api_http_client_with_bearer_auth.MattermostClient.get_json",
            lambda self, path: fake_board,
        )

        # Act
        spec.loader.exec_module(digest_module)
        result_code = digest_module.main()
        captured = capsys.readouterr()
        digest = json.loads(captured.out)

        # Assert
        assert result_code == 0
        assert digest["waiting_assigned"] == 1

    def test_digest_counts_unassigned_in_todo_lane(self, capsys, monkeypatch):
        """Arrange: Todo lane có 3 cards: 1 assigned, 2 unassigned.
        Act: digest. Assert: unassigned=2.
        """
        import importlib.util
        entry_file = Path(__file__).parent.parent / "kanban-board-digest-fetch-and-summarize.py"
        spec = importlib.util.spec_from_file_location("digest_entry", entry_file)
        digest_module = importlib.util.module_from_spec(spec)

        fake_board = {
            "lanes": [
                {
                    "id": "lane-1",
                    "title": "Todo",
                    "cards": [
                        {"id": "c1", "title": "Card 1", "assignUsers": ["user1"]},
                        {"id": "c2", "title": "Card 2", "assignUsers": []},
                        {"id": "c3", "title": "Card 3", "assignUsers": []},
                    ],
                },
            ],
        }

        fake_creds = {
            "mattermostUrl": "https://mm.nal.vn",
            "botToken": "fake-token",
            "teamId": "team-1",
            "defaultChannelId": "ch-1",
        }

        monkeypatch.setattr(
            "mattermost_credentials_reader_and_token_masker.load_credentials",
            lambda: fake_creds,
        )
        monkeypatch.setattr(
            "mattermost_api_http_client_with_bearer_auth.MattermostClient.get_json",
            lambda self, path: fake_board,
        )

        # Act
        spec.loader.exec_module(digest_module)
        result_code = digest_module.main()
        captured = capsys.readouterr()
        digest = json.loads(captured.out)

        # Assert
        assert result_code == 0
        assert digest["unassigned"] == 2

    def test_digest_counts_overdue_cards_with_past_deadline(self, capsys, monkeypatch):
        """Arrange: Board có 4 cards:
        - InProgress card với deadline quá khứ (overdue)
        - Done card với deadline quá khứ (KHÔNG count, lane=Done)
        - Todo card với deadline tương lai (NOT overdue)
        - Todo card không deadline (NOT overdue).
        Act: digest. Assert: overdue=1 (chỉ InProgress past deadline).
        """
        import importlib.util
        entry_file = Path(__file__).parent.parent / "kanban-board-digest-fetch-and-summarize.py"
        spec = importlib.util.spec_from_file_location("digest_entry", entry_file)
        digest_module = importlib.util.module_from_spec(spec)

        now_ms = int(time.time() * 1000)
        past_ms = now_ms - 86400000  # 1 day ago
        future_ms = now_ms + 86400000  # 1 day later

        fake_board = {
            "lanes": [
                {
                    "id": "lane-1",
                    "title": "Todo",
                    "cards": [
                        {
                            "id": "c1",
                            "title": "With future deadline",
                            "assignUsers": [],
                            "deadline": future_ms,
                        },
                        {
                            "id": "c2",
                            "title": "No deadline",
                            "assignUsers": [],
                            "deadline": 0,
                        },
                    ],
                },
                {
                    "id": "lane-2",
                    "title": "InProgress",
                    "cards": [
                        {
                            "id": "c3",
                            "title": "Overdue",
                            "assignUsers": ["user1"],
                            "deadline": past_ms,
                        },
                    ],
                },
                {
                    "id": "lane-3",
                    "title": "Done",
                    "cards": [
                        {
                            "id": "c4",
                            "title": "Done but past deadline",
                            "assignUsers": [],
                            "deadline": past_ms,
                        },
                    ],
                },
            ],
        }

        fake_creds = {
            "mattermostUrl": "https://mm.nal.vn",
            "botToken": "fake-token",
            "teamId": "team-1",
            "defaultChannelId": "ch-1",
        }

        monkeypatch.setattr(
            "mattermost_credentials_reader_and_token_masker.load_credentials",
            lambda: fake_creds,
        )
        monkeypatch.setattr(
            "mattermost_api_http_client_with_bearer_auth.MattermostClient.get_json",
            lambda self, path: fake_board,
        )

        # Act
        spec.loader.exec_module(digest_module)
        result_code = digest_module.main()
        captured = capsys.readouterr()
        digest = json.loads(captured.out)

        # Assert
        assert result_code == 0
        assert digest["overdue"] == 1, f"Expected overdue=1, got {digest['overdue']}"

    def test_digest_includes_lane_ids_with_all_lanes(self, capsys, monkeypatch):
        """Arrange: Board có 3 lanes (Todo, InProgress, Done).
        Act: digest. Assert: lane_ids=[{id,title}, ...] for all 3 lanes.
        """
        import importlib.util
        entry_file = Path(__file__).parent.parent / "kanban-board-digest-fetch-and-summarize.py"
        spec = importlib.util.spec_from_file_location("digest_entry", entry_file)
        digest_module = importlib.util.module_from_spec(spec)

        fake_board = {
            "lanes": [
                {"id": "lane-1", "title": "Todo", "cards": []},
                {"id": "lane-2", "title": "InProgress", "cards": []},
                {"id": "lane-3", "title": "Done", "cards": []},
            ],
        }

        fake_creds = {
            "mattermostUrl": "https://mm.nal.vn",
            "botToken": "fake-token",
            "teamId": "team-1",
            "defaultChannelId": "ch-1",
        }

        monkeypatch.setattr(
            "mattermost_credentials_reader_and_token_masker.load_credentials",
            lambda: fake_creds,
        )
        monkeypatch.setattr(
            "mattermost_api_http_client_with_bearer_auth.MattermostClient.get_json",
            lambda self, path: fake_board,
        )

        # Act
        spec.loader.exec_module(digest_module)
        result_code = digest_module.main()
        captured = capsys.readouterr()
        digest = json.loads(captured.out)

        # Assert
        assert result_code == 0
        assert "lane_ids" in digest
        assert len(digest["lane_ids"]) == 3
        assert digest["lane_ids"][0] == {"id": "lane-1", "title": "Todo"}
        assert digest["lane_ids"][1] == {"id": "lane-2", "title": "InProgress"}
        assert digest["lane_ids"][2] == {"id": "lane-3", "title": "Done"}

    def test_digest_comprehensive_scenario(self, capsys, monkeypatch):
        """Arrange: Realistic board với mix cards (assigned, unassigned, overdue).
        Act: digest. Assert: Verify waiting_assigned=1, unassigned=1, overdue=1, total=4.
        """
        import importlib.util
        entry_file = Path(__file__).parent.parent / "kanban-board-digest-fetch-and-summarize.py"
        spec = importlib.util.spec_from_file_location("digest_entry", entry_file)
        digest_module = importlib.util.module_from_spec(spec)

        now_ms = int(time.time() * 1000)
        past_ms = now_ms - 86400000  # 1 day ago

        fake_board = {
            "lanes": [
                {
                    "id": "lane-1",
                    "title": "Todo",
                    "cards": [
                        {
                            "id": "c1",
                            "title": "Todo assigned",
                            "assignUsers": ["user1"],
                        },
                        {
                            "id": "c2",
                            "title": "Todo unassigned",
                            "assignUsers": [],
                        },
                    ],
                },
                {
                    "id": "lane-2",
                    "title": "InProgress",
                    "cards": [
                        {
                            "id": "c3",
                            "title": "InProgress overdue",
                            "assignUsers": ["user2"],
                            "deadline": past_ms,
                        },
                    ],
                },
                {
                    "id": "lane-3",
                    "title": "Done",
                    "cards": [
                        {
                            "id": "c4",
                            "title": "Done (no overdue count)",
                            "assignUsers": [],
                            "deadline": past_ms,
                        },
                    ],
                },
            ],
        }

        fake_creds = {
            "mattermostUrl": "https://mm.nal.vn",
            "botToken": "fake-token",
            "teamId": "team-1",
            "defaultChannelId": "ch-1",
        }

        monkeypatch.setattr(
            "mattermost_credentials_reader_and_token_masker.load_credentials",
            lambda: fake_creds,
        )
        monkeypatch.setattr(
            "mattermost_api_http_client_with_bearer_auth.MattermostClient.get_json",
            lambda self, path: fake_board,
        )

        # Act
        spec.loader.exec_module(digest_module)
        result_code = digest_module.main()
        captured = capsys.readouterr()
        digest = json.loads(captured.out)

        # Assert
        assert result_code == 0
        assert digest["waiting_assigned"] == 1
        assert digest["unassigned"] == 1
        assert digest["overdue"] == 1
        assert digest["total"] == 4
        assert digest["lanes"]["Todo"] == 2
        assert digest["lanes"]["InProgress"] == 1
        assert digest["lanes"]["Done"] == 1

    def test_digest_returns_2_on_credentials_error(self, capsys, monkeypatch):
        """Arrange: load_credentials() raises CredentialsError. Act: digest.
        Assert: Exit code 2 + error on stderr.
        """
        import importlib.util
        entry_file = Path(__file__).parent.parent / "kanban-board-digest-fetch-and-summarize.py"
        spec = importlib.util.spec_from_file_location("digest_entry", entry_file)
        digest_module = importlib.util.module_from_spec(spec)

        def raise_creds_error():
            raise creds_module.CredentialsError("Credentials missing")

        monkeypatch.setattr(
            "mattermost_credentials_reader_and_token_masker.load_credentials",
            raise_creds_error,
        )

        # Act
        spec.loader.exec_module(digest_module)
        result_code = digest_module.main()
        captured = capsys.readouterr()

        # Assert
        assert result_code == 2
        assert "Credentials missing" in captured.err

    def test_digest_returns_2_on_api_error(self, capsys, monkeypatch):
        """Arrange: client.get_json() raises MattermostApiError. Act: digest.
        Assert: Exit code 2 + error on stderr.
        """
        import importlib.util
        entry_file = Path(__file__).parent.parent / "kanban-board-digest-fetch-and-summarize.py"
        spec = importlib.util.spec_from_file_location("digest_entry", entry_file)
        digest_module = importlib.util.module_from_spec(spec)

        fake_creds = {
            "mattermostUrl": "https://mm.nal.vn",
            "botToken": "fake-token",
            "teamId": "team-1",
            "defaultChannelId": "ch-1",
        }

        def raise_api_error(self, path):
            raise client_module.MattermostApiError("Connection timeout")

        monkeypatch.setattr(
            "mattermost_credentials_reader_and_token_masker.load_credentials",
            lambda: fake_creds,
        )
        monkeypatch.setattr(
            "mattermost_api_http_client_with_bearer_auth.MattermostClient.get_json",
            raise_api_error,
        )

        # Act
        spec.loader.exec_module(digest_module)
        result_code = digest_module.main()
        captured = capsys.readouterr()

        # Assert
        assert result_code == 2
        assert "Connection timeout" in captured.err

    def test_digest_handles_enddate_fallback_when_deadline_missing(self, capsys, monkeypatch):
        """Arrange: Card sử dụng endDate instead of deadline. Act: digest check overdue.
        Assert: overdue logic hoạt động với endDate field.
        """
        import importlib.util
        entry_file = Path(__file__).parent.parent / "kanban-board-digest-fetch-and-summarize.py"
        spec = importlib.util.spec_from_file_location("digest_entry", entry_file)
        digest_module = importlib.util.module_from_spec(spec)

        now_ms = int(time.time() * 1000)
        past_ms = now_ms - 86400000  # 1 day ago

        fake_board = {
            "lanes": [
                {
                    "id": "lane-1",
                    "title": "InProgress",
                    "cards": [
                        {
                            "id": "c1",
                            "title": "Card with endDate",
                            "assignUsers": ["user1"],
                            "endDate": past_ms,
                        },
                    ],
                },
            ],
        }

        fake_creds = {
            "mattermostUrl": "https://mm.nal.vn",
            "botToken": "fake-token",
            "teamId": "team-1",
            "defaultChannelId": "ch-1",
        }

        monkeypatch.setattr(
            "mattermost_credentials_reader_and_token_masker.load_credentials",
            lambda: fake_creds,
        )
        monkeypatch.setattr(
            "mattermost_api_http_client_with_bearer_auth.MattermostClient.get_json",
            lambda self, path: fake_board,
        )

        # Act
        spec.loader.exec_module(digest_module)
        result_code = digest_module.main()
        captured = capsys.readouterr()
        digest = json.loads(captured.out)

        # Assert
        assert result_code == 0
        assert digest["overdue"] == 1, "endDate field should be recognized for overdue check"

    def test_digest_output_json_includes_all_required_fields(self, capsys, monkeypatch):
        """Arrange: Minimal valid board. Act: digest.
        Assert: Output JSON has all 11 required fields.

        ⛔ ĐỐI CHỨNG KHOÁ CONTRACT — phép so là `==`, KHÔNG phải `issubset`.
        Thêm key mới vào digest ⇒ test này ĐỎ theo THIẾT KẾ: cập nhật tập tên ở
        dưới, TUYỆT ĐỐI không nới `==` thành `<=`. Nới phép so là tự tay mở đường
        cho lần thêm key im lặng tiếp theo — đúng loài lỗi #194 sinh ra để diệt.
        (`fake_board = {"lanes": []}` ⇒ 4 key cắt cụt vẫn phải có mặt, vì chúng
        LUÔN CÓ MẶT ở mọi lần chạy chứ không "chỉ xuất hiện khi tripwire nổ".)
        """
        import importlib.util
        entry_file = Path(__file__).parent.parent / "kanban-board-digest-fetch-and-summarize.py"
        spec = importlib.util.spec_from_file_location("digest_entry", entry_file)
        digest_module = importlib.util.module_from_spec(spec)

        fake_board = {"lanes": []}

        fake_creds = {
            "mattermostUrl": "https://mm.nal.vn",
            "botToken": "fake-token",
            "teamId": "team-1",
            "defaultChannelId": "ch-1",
        }

        monkeypatch.setattr(
            "mattermost_credentials_reader_and_token_masker.load_credentials",
            lambda: fake_creds,
        )
        monkeypatch.setattr(
            "mattermost_api_http_client_with_bearer_auth.MattermostClient.get_json",
            lambda self, path: fake_board,
        )

        # Act
        spec.loader.exec_module(digest_module)
        result_code = digest_module.main()
        captured = capsys.readouterr()
        digest = json.loads(captured.out)

        # Assert
        assert result_code == 0
        required_fields = {
            "lanes", "lane_ids", "waiting_assigned", "unassigned", "overdue",
            "total", "cards",  # cards[] mọi lane (thêm cho /avatar:specs:done resolve #ref)
            # 5 key cắt cụt — LUÔN có mặt, kể cả board rỗng:
            # 4 key đầu từ #194 (một snapshot), key thứ 5 từ #216 (lịch sử nhiều
            # lần chạy — chiều cap GIẢM mà 4 key kia mù):
            "cap", "truncated", "truncated_lanes", "cap_changed",
            "cap_drop_suspected",
        }
        assert set(digest.keys()) == required_fields


# ╔══════════════════════════════════════════════════════════════════════════╗
# ║ Tests: --todo-detail (avatar:specs:receive expanded card fields)          ║
# ╚══════════════════════════════════════════════════════════════════════════╝


class TestTodoDetail:
    """Test suite cho _todo_detail(board, client) -> {"cards":[...]}.

    Field mới (phase nâng cấp digest+receive): descriptionShort, deadline, files.
    Field cũ giữ nguyên (receive.md đang dùng): id, cardNumberRef, title,
    assignUsers, fileIds, threadId.
    """

    def _make_digest_module(self):
        """Trả (spec, module) CHƯA exec — caller phải monkeypatch trước rồi mới
        gọi spec.loader.exec_module(module) (đúng thứ tự các test khác trong file
        này dùng: patch import target trước, exec_module sau, để import-time
        binding `from X import load_credentials` lấy đúng bản monkeypatch)."""
        import importlib.util
        entry_file = Path(__file__).parent.parent / "kanban-board-digest-fetch-and-summarize.py"
        spec = importlib.util.spec_from_file_location("digest_entry_todo_detail", entry_file)
        module = importlib.util.module_from_spec(spec)
        return spec, module

    def test_todo_detail_includes_description_short_and_deadline(self, capsys, monkeypatch):
        """Arrange: Card Todo có description dài + deadline tương lai.
        Act: --todo-detail. Assert: cards[0] có descriptionShort rút gọn + deadline epoch ms.
        """
        spec, digest_module = self._make_digest_module()
        future_ms = int(time.time() * 1000) + 86400000

        fake_board = {
            "lanes": [
                {
                    "id": "lane-1",
                    "title": "Todo",
                    "cards": [
                        {
                            "id": "card-1",
                            "cardNumberRef": "10",
                            "title": "Hello World",
                            "description": "Dòng mô tả đầu tiên.",
                            "assignUsers": ["minh"],
                            "deadline": future_ms,
                            "fileIds": [],
                        },
                    ],
                },
            ],
        }
        fake_creds = {
            "mattermostUrl": "https://mm.nal.vn", "botToken": "fake-token",
            "teamId": "team-1", "defaultChannelId": "ch-1",
        }

        monkeypatch.setattr(
            "mattermost_credentials_reader_and_token_masker.load_credentials",
            lambda: fake_creds,
        )
        monkeypatch.setattr(
            "mattermost_api_http_client_with_bearer_auth.MattermostClient.get_json",
            lambda self, path: fake_board,
        )
        monkeypatch.setattr(sys, "argv", ["prog", "--todo-detail"])

        # Act
        spec.loader.exec_module(digest_module)
        result_code = digest_module.main()
        captured = capsys.readouterr()
        result = json.loads(captured.out)

        # Assert
        assert result_code == 0
        card = result["cards"][0]
        assert card["descriptionShort"] == "Dòng mô tả đầu tiên."
        assert card["deadline"] == future_ms

    def test_todo_detail_no_deadline_returns_null(self, capsys, monkeypatch):
        """Arrange: Card Todo không đặt deadline (0). Act: --todo-detail.
        Assert: cards[0]["deadline"] is None.
        """
        spec, digest_module = self._make_digest_module()

        fake_board = {
            "lanes": [
                {
                    "id": "lane-1", "title": "Todo",
                    "cards": [{"id": "c1", "cardNumberRef": "1", "title": "No deadline", "deadline": 0}],
                },
            ],
        }
        fake_creds = {
            "mattermostUrl": "https://mm.nal.vn", "botToken": "fake-token",
            "teamId": "team-1", "defaultChannelId": "ch-1",
        }

        monkeypatch.setattr(
            "mattermost_credentials_reader_and_token_masker.load_credentials",
            lambda: fake_creds,
        )
        monkeypatch.setattr(
            "mattermost_api_http_client_with_bearer_auth.MattermostClient.get_json",
            lambda self, path: fake_board,
        )
        monkeypatch.setattr(sys, "argv", ["prog", "--todo-detail"])

        # Act
        spec.loader.exec_module(digest_module)
        digest_module.main()
        captured = capsys.readouterr()
        result = json.loads(captured.out)

        # Assert
        assert result["cards"][0]["deadline"] is None

    def test_todo_detail_resolves_real_file_names(self, capsys, monkeypatch):
        """Arrange: Card Todo có 1 fileId; board GET + file info GET mock theo path.
        Act: --todo-detail. Assert: cards[0]["files"] == [{"id","name":"hello-world.html"}],
        fileIds giữ nguyên (backward-compat).
        """
        spec, digest_module = self._make_digest_module()

        fake_board = {
            "lanes": [
                {
                    "id": "lane-1", "title": "Todo",
                    "cards": [
                        {
                            "id": "card-1", "cardNumberRef": "10", "title": "Hello World",
                            "assignUsers": ["minh"], "fileIds": ["sk4qcqch"],
                        },
                    ],
                },
            ],
        }
        fake_creds = {
            "mattermostUrl": "https://mm.nal.vn", "botToken": "fake-token",
            "teamId": "team-1", "defaultChannelId": "ch-1",
        }

        def fake_get_json(self, path):
            if path.startswith("/plugins/"):
                return fake_board
            return {"name": "hello-world.html", "size": 221}

        monkeypatch.setattr(
            "mattermost_credentials_reader_and_token_masker.load_credentials",
            lambda: fake_creds,
        )
        monkeypatch.setattr(
            "mattermost_api_http_client_with_bearer_auth.MattermostClient.get_json",
            fake_get_json,
        )
        monkeypatch.setattr(sys, "argv", ["prog", "--todo-detail"])

        # Act
        spec.loader.exec_module(digest_module)
        result_code = digest_module.main()
        captured = capsys.readouterr()
        result = json.loads(captured.out)

        # Assert
        assert result_code == 0
        card = result["cards"][0]
        assert card["fileIds"] == ["sk4qcqch"]
        assert card["files"] == [{"id": "sk4qcqch", "name": "hello-world.html"}]

    def test_todo_detail_no_files_returns_empty_files_list(self, capsys, monkeypatch):
        """Arrange: Card Todo không có fileIds. Act: --todo-detail.
        Assert: cards[0]["files"] == [].
        """
        spec, digest_module = self._make_digest_module()

        fake_board = {
            "lanes": [
                {
                    "id": "lane-1", "title": "Todo",
                    "cards": [{"id": "c1", "cardNumberRef": "1", "title": "No file"}],
                },
            ],
        }
        fake_creds = {
            "mattermostUrl": "https://mm.nal.vn", "botToken": "fake-token",
            "teamId": "team-1", "defaultChannelId": "ch-1",
        }

        monkeypatch.setattr(
            "mattermost_credentials_reader_and_token_masker.load_credentials",
            lambda: fake_creds,
        )
        monkeypatch.setattr(
            "mattermost_api_http_client_with_bearer_auth.MattermostClient.get_json",
            lambda self, path: fake_board,
        )
        monkeypatch.setattr(sys, "argv", ["prog", "--todo-detail"])

        # Act
        spec.loader.exec_module(digest_module)
        digest_module.main()
        captured = capsys.readouterr()
        result = json.loads(captured.out)

        # Assert
        assert result["cards"][0]["files"] == []

    def test_todo_detail_preserves_existing_fields_for_backward_compat(self, capsys, monkeypatch):
        """Arrange: Card Todo đầy đủ field cũ (receive.md đang dùng).
        Act: --todo-detail. Assert: id, cardNumberRef, title, assignUsers, fileIds,
        threadId vẫn có mặt & đúng giá trị — không bị field mới ghi đè/xoá.
        """
        spec, digest_module = self._make_digest_module()

        fake_board = {
            "lanes": [
                {
                    "id": "lane-1", "title": "Todo",
                    "cards": [
                        {
                            "id": "card-xyz", "cardNumberRef": "42", "title": "Ticket cũ",
                            "assignUsers": ["hung"], "fileIds": [],
                            "props": {"threadId": "thread-abc"},
                        },
                    ],
                },
            ],
        }
        fake_creds = {
            "mattermostUrl": "https://mm.nal.vn", "botToken": "fake-token",
            "teamId": "team-1", "defaultChannelId": "ch-1",
        }

        monkeypatch.setattr(
            "mattermost_credentials_reader_and_token_masker.load_credentials",
            lambda: fake_creds,
        )
        monkeypatch.setattr(
            "mattermost_api_http_client_with_bearer_auth.MattermostClient.get_json",
            lambda self, path: fake_board,
        )
        monkeypatch.setattr(sys, "argv", ["prog", "--todo-detail"])

        # Act
        spec.loader.exec_module(digest_module)
        digest_module.main()
        captured = capsys.readouterr()
        result = json.loads(captured.out)

        # Assert
        card = result["cards"][0]
        assert card["id"] == "card-xyz"
        assert card["cardNumberRef"] == "42"
        assert card["title"] == "Ticket cũ"
        assert card["assignUsers"] == ["hung"]
        assert card["fileIds"] == []
        assert card["threadId"] == "thread-abc"

    def test_todo_detail_ignores_non_todo_lanes(self, capsys, monkeypatch):
        """Arrange: Board có Todo (1 card) + InProgress (1 card). Act: --todo-detail.
        Assert: cards chỉ chứa card của lane Todo.
        """
        spec, digest_module = self._make_digest_module()

        fake_board = {
            "lanes": [
                {"id": "lane-1", "title": "Todo", "cards": [{"id": "c1", "cardNumberRef": "1", "title": "Todo card"}]},
                {"id": "lane-2", "title": "InProgress", "cards": [{"id": "c2", "cardNumberRef": "2", "title": "InProgress card"}]},
            ],
        }
        fake_creds = {
            "mattermostUrl": "https://mm.nal.vn", "botToken": "fake-token",
            "teamId": "team-1", "defaultChannelId": "ch-1",
        }

        monkeypatch.setattr(
            "mattermost_credentials_reader_and_token_masker.load_credentials",
            lambda: fake_creds,
        )
        monkeypatch.setattr(
            "mattermost_api_http_client_with_bearer_auth.MattermostClient.get_json",
            lambda self, path: fake_board,
        )
        monkeypatch.setattr(sys, "argv", ["prog", "--todo-detail"])

        # Act
        spec.loader.exec_module(digest_module)
        digest_module.main()
        captured = capsys.readouterr()
        result = json.loads(captured.out)

        # Assert
        assert len(result["cards"]) == 1
        assert result["cards"][0]["title"] == "Todo card"


# ╔══════════════════════════════════════════════════════════════════════════╗
# ║ Tests: cờ cắt cụt cap/truncated/truncated_lanes/cap_changed (#194)        ║
# ╚══════════════════════════════════════════════════════════════════════════╝


def _board_with_lane_sizes(sizes):
    """Dựng board giả từ {tên lane: SỐ CARD}.

    ⛔ Số truyền vào PHẢI là literal (10 / 11 / 3). Gọi hàm này với
    `mod.LANE_CARD_CAP` là PHÁ positive control: hằng số (trong module) và
    fixture (trong test) phải là HAI NGUỒN ĐỘC LẬP. Nếu fixture bám theo hằng thì
    đảo hằng 10 → 99 sẽ sinh board 99 card, quan hệ len ↔ cap được bảo toàn ⇒
    không ca nào đỏ ⇒ control chứng minh số 0 mà vẫn "trông như đã làm".
    """
    return {
        "lanes": [
            {
                "id": f"lane-{idx}",
                "title": title,
                "cards": [
                    {
                        "id": f"{title}-c{n}", "cardNumberRef": str(n),
                        "title": f"card {n}", "assignUsers": [], "fileIds": [],
                    }
                    for n in range(size)
                ],
            }
            for idx, (title, size) in enumerate(sizes.items())
        ],
    }


def _make_card_update_module():
    """Trả (spec, module) CHƯA exec cho entry script `update`.

    Tên file có dấu gạch ngang ⇒ phải nạp qua importlib. Cùng khuôn
    `TestTodoDetail._make_digest_module`; đặt ở module-level để KHÔNG chép khối
    importlib lần thứ ba. Caller phải monkeypatch TRƯỚC rồi mới `exec_module`
    (import-time binding `from X import load_credentials`).
    """
    import importlib.util
    entry_file = Path(__file__).parent.parent / "kanban-card-create-and-update-lane-fileids.py"
    spec = importlib.util.spec_from_file_location("card_update_entry_truncation", entry_file)
    module = importlib.util.module_from_spec(spec)
    return spec, module


class TestDigestTruncationFlag:
    """Test suite cho truncation_report() — 4 key cắt cụt ở CẢ hai nhánh output.

    Tái dùng helper dựng module của TestTodoDetail (tên file có dấu gạch ngang ⇒
    phải nạp qua importlib), không copy khối importlib lần thứ ba.
    """

    _make_digest_module = TestTodoDetail._make_digest_module

    _FAKE_CREDS = {
        "mattermostUrl": "https://mm.nal.vn", "botToken": "fake-token",
        "teamId": "team-1", "defaultChannelId": "ch-1",
    }

    def _run_digest(self, monkeypatch, capsys, board, argv):
        """Arrange chung: patch creds + get_json, exec module, gọi main().

        State watermark được cô lập bởi fixture module-level
        `_isolate_watermark_state_for_every_test` — xem chú thích ở đó.
        """
        spec, digest_module = self._make_digest_module()
        monkeypatch.setattr(
            "mattermost_credentials_reader_and_token_masker.load_credentials",
            lambda: self._FAKE_CREDS,
        )
        monkeypatch.setattr(
            "mattermost_api_http_client_with_bearer_auth.MattermostClient.get_json",
            lambda self, path: board,
        )
        monkeypatch.setattr(sys, "argv", argv)
        spec.loader.exec_module(digest_module)
        result_code = digest_module.main()
        return result_code, capsys.readouterr()

    def test_digest_truncation_lane_at_cap_sets_truncated_true(self, capsys, monkeypatch):
        """Arrange: lane Backlog có ĐÚNG 10 card (chạm cap), Todo 3 card.
        Act: digest. Assert: truncated bật, Backlog nằm trong truncated_lanes,
        Todo thì không.
        """
        # Arrange
        board = _board_with_lane_sizes({"Backlog": 10, "Todo": 3})

        # Act
        result_code, captured = self._run_digest(monkeypatch, capsys, board, ["prog"])
        digest = json.loads(captured.out)

        # Assert
        assert result_code == 0
        assert digest["truncated"] is True
        assert set(digest["truncated_lanes"]) == {"Backlog"}
        assert digest["cap"] == 10

    def test_digest_truncation_all_lanes_below_cap_sets_truncated_false(self, capsys, monkeypatch):
        """CA ÂM — Arrange: 3 lane đều DƯỚI cap (3/4/2 card).
        Act: digest. Assert: truncated tắt, truncated_lanes rỗng, cap_changed
        tắt NHƯNG key vẫn CÓ MẶT (bắt ca "key vắng mặt im lặng").
        """
        # Arrange
        board = _board_with_lane_sizes({"Backlog": 3, "Todo": 4, "Done": 2})

        # Act
        result_code, captured = self._run_digest(monkeypatch, capsys, board, ["prog"])
        digest = json.loads(captured.out)

        # Assert
        assert result_code == 0
        assert digest["truncated"] is False
        assert digest["truncated_lanes"] == []
        assert "cap_changed" in digest
        assert digest["cap_changed"] is False

    def test_digest_truncation_lane_above_cap_sets_cap_changed_true(self, capsys, monkeypatch):
        """TRIPWIRE — Arrange: lane có 11 card, VƯỢT cap 10.
        Act: digest. Assert: cap_changed bật (hằng số trong pack đã lỗi thời) và
        truncated cũng bật.
        """
        # Arrange
        board = _board_with_lane_sizes({"Backlog": 11, "Todo": 2})

        # Act
        result_code, captured = self._run_digest(monkeypatch, capsys, board, ["prog"])
        digest = json.loads(captured.out)

        # Assert
        assert result_code == 0
        assert digest["cap_changed"] is True
        assert digest["truncated"] is True

    def test_digest_truncation_todo_detail_branch_includes_flag(self, capsys, monkeypatch):
        """Arrange: board mọi lane dưới cap, chạy nhánh --todo-detail.
        Act: digest --todo-detail. Assert: đủ 4 key cắt cụt ở root và cards
        không đổi. Ca này CHỈ kiểm key CÓ MẶT, không đọc giá trị cờ.
        """
        # Arrange
        board = _board_with_lane_sizes({"Todo": 3, "Done": 2})

        # Act
        result_code, captured = self._run_digest(
            monkeypatch, capsys, board, ["prog", "--todo-detail"],
        )
        result = json.loads(captured.out)

        # Assert
        assert result_code == 0
        for key in ("cap", "truncated", "truncated_lanes", "cap_changed"):
            assert key in result, f"nhánh --todo-detail thiếu key {key}"
        assert len(result["cards"]) == 3

    def test_digest_truncation_warning_goes_to_stderr_not_stdout(self, capsys, monkeypatch):
        """Arrange: lane chạm cap ⇒ có cảnh báo.
        Act: digest. Assert: stdout vẫn là JSON hợp lệ (cảnh báo KHÔNG lẫn vào),
        stderr khác rỗng và nêu tên lane.
        """
        # Arrange
        board = _board_with_lane_sizes({"Backlog": 10, "Todo": 2})

        # Act
        result_code, captured = self._run_digest(monkeypatch, capsys, board, ["prog"])

        # Assert
        assert result_code == 0
        digest = json.loads(captured.out)  # vỡ ở đây = cảnh báo lọt stdout
        assert digest["truncated"] is True
        assert captured.err != ""
        assert "Backlog" in captured.err


class TestCardUpdateTruncationAwareness:
    """Test suite cho `do_update()` — lời khai "không tìm thấy card" phải RẼ theo
    cờ cắt cụt thay vì khẳng định một chiều (#222).

    Board bị server cắt ở `cap` card/lane ⇒ `card is None` là dữ kiện về RESPONSE,
    không phải về sự tồn tại của card. Ca 1 pin đúng bug gốc; ca 2 giữ lời khai
    ĐÚNG khi board không bị cắt (đừng "vá" bằng cách luôn nói mơ hồ).
    """

    _FAKE_CREDS = {
        "mattermostUrl": "https://mm.nal.vn", "botToken": "fake-token",
        "teamId": "team-1", "defaultChannelId": "ch-1",
    }

    def _run_update(self, monkeypatch, capsys, board, payload, put_result=None):
        """Arrange chung: patch creds + get_json + put_json, exec module, gọi do_update.

        ⚠️ `put_result=None` CHỈ hợp lệ cho ca không-tìm-thấy (chúng `return 3`
        trước khi PUT). Ca đi đường thành công phải truyền dict, vì `do_update`
        đọc `res["id"]` — để `None` sẽ ném TypeError chứ không fail assert.
        """
        spec, module = _make_card_update_module()
        put_calls = []
        monkeypatch.setattr(
            "mattermost_credentials_reader_and_token_masker.load_credentials",
            lambda: self._FAKE_CREDS,
        )
        monkeypatch.setattr(
            "mattermost_api_http_client_with_bearer_auth.MattermostClient.get_json",
            lambda self, path: board,
        )
        monkeypatch.setattr(
            "mattermost_api_http_client_with_bearer_auth.MattermostClient.put_json",
            lambda self, path, body: (put_calls.append((path, body)), put_result)[1],
        )
        spec.loader.exec_module(module)
        return module.do_update(payload), capsys.readouterr(), put_calls

    def test_card_update_not_found_on_truncated_board_omits_deleted_by_hand_claim(
        self, capsys, monkeypatch
    ):
        """Arrange: lane Backlog chạm cap (10 card literal), card cần tìm KHÔNG có
        trong response. Act: do_update. Assert: rc=3 nhưng KHÔNG khẳng định card bị
        xoá — nêu 2 khả năng + tên lane bị cắt. Đây là bug gốc #222.
        """
        # Arrange
        board = _board_with_lane_sizes({"Backlog": 10, "Todo": 3})

        # Act
        result_code, captured, _ = self._run_update(
            monkeypatch, capsys, board, {"cardId": "card-ngoai-trang-dau"})

        # Assert
        assert result_code == 3
        assert "đã bị xoá tay" not in captured.err
        assert "2 khả năng" in captured.err
        assert "Backlog" in captured.err

    def test_card_update_not_found_on_untruncated_board_keeps_deleted_by_hand_message(
        self, capsys, monkeypatch
    ):
        """CA ÂM — Arrange: mọi lane DƯỚI cap (3/4 card literal) ⇒ board không bị cắt.
        Act: do_update với cardId vắng mặt. Assert: giữ NGUYÊN VĂN câu cũ, KHÔNG
        chuyển sang câu mơ hồ (mất lời khai đúng cũng là hồi quy).
        """
        # Arrange
        board = _board_with_lane_sizes({"Backlog": 3, "Todo": 4})

        # Act
        result_code, captured, _ = self._run_update(
            monkeypatch, capsys, board, {"cardId": "card-bi-xoa-that"})

        # Assert
        assert result_code == 3
        assert "đã bị xoá tay" in captured.err
        assert "2 khả năng" not in captured.err

    def test_card_update_found_card_on_truncated_board_still_performs_update(
        self, capsys, monkeypatch
    ):
        """ĐỐI CHỨNG NGƯỢC — Arrange: board bị cắt NHƯNG card có thật trong response.
        Act: do_update. Assert: đường thành công KHÔNG rẽ nhầm — vẫn PUT, rc=0,
        stdout đúng một dòng JSON, stderr rỗng.
        """
        # Arrange
        board = _board_with_lane_sizes({"Backlog": 10})
        put_result = {"id": "Backlog-c3", "cardNumberRef": "3", "laneId": "lane-0"}

        # Act
        result_code, captured, put_calls = self._run_update(
            monkeypatch, capsys, board, {"cardId": "Backlog-c3"}, put_result=put_result)

        # Assert
        assert result_code == 0
        assert len(put_calls) == 1
        assert json.loads(captured.out)["id"] == "Backlog-c3"
        assert captured.err == ""

    def test_card_update_not_found_with_cap_changed_warns_stale_cap_constant(
        self, capsys, monkeypatch
    ):
        """Arrange: lane trả 11 card (literal > cap 10) ⇒ cap phía server đã đổi.
        Act: do_update với cardId vắng. Assert: có cảnh báo hằng số lỗi thời.
        """
        # Arrange
        board = _board_with_lane_sizes({"Backlog": 11})

        # Act
        result_code, captured, _ = self._run_update(
            monkeypatch, capsys, board, {"cardId": "card-vang-mat"})

        # Assert
        assert result_code == 3
        assert "LANE_CARD_CAP" in captured.err and "lỗi thời" in captured.err
        assert "đã bị xoá tay" not in captured.err

    def test_card_update_not_found_message_excludes_card_titles(self, capsys, monkeypatch):
        """CA BẢO MẬT — Arrange: board bị cắt, fixture sinh title `card {n}`.
        Act: do_update với cardId vắng. Assert: KHÔNG tiêu đề card nào lọt stderr
        (stderr chảy vào log CI). ⛔ Không assert `"card" not in err`: thông điệp
        hợp lệ có chứa cụm "card/lane" ⇒ dương tính giả.
        """
        # Arrange
        board = _board_with_lane_sizes({"Backlog": 10})

        # Act
        result_code, captured, _ = self._run_update(
            monkeypatch, capsys, board, {"cardId": "card-vang-mat"})

        # Assert
        assert result_code == 3
        for n in range(10):
            assert f"card {n}" not in captured.err

    def test_truncation_detector_module_exports_cap_and_report_for_entry_scripts(self):
        """LAYOUT CONTRACT — Arrange: module dùng chung phải import được BẰNG TÊN.
        Act: import + gọi. Assert: đủ 3 export và report đủ 4 key.
        """
        # Arrange + Act
        import kanban_board_truncation_cap_detector as detector

        # Assert
        assert detector.LANE_CARD_CAP == 10
        assert callable(detector.truncation_report)
        assert callable(detector.cap_changed_hint)
        assert set(detector.truncation_report({"lanes": []})) == {
            "cap", "truncated", "truncated_lanes", "cap_changed",
        }


# ╔══════════════════════════════════════════════════════════════════════════╗
# ║ Tests: watermark cap — bắt chiều cap GIẢM qua nhiều lần chạy (#216)      ║
# ╚══════════════════════════════════════════════════════════════════════════╝


class TestCapWatermarkStateTracker:
    """Test suite cho kanban_cap_watermark_state_tracker.

    ⛔ Mọi ca ghi state vào `tmp_path` — KHÔNG đụng `.claude/state/` thật (luật
    "unit test không phụ thuộc external state"). Số cap truyền vào là LITERAL,
    không lấy từ `detector.LANE_CARD_CAP`, giữ nguyên kỷ luật positive control
    của `_board_with_lane_sizes`.
    """

    @staticmethod
    def _tracker():
        import kanban_cap_watermark_state_tracker as tracker
        return tracker

    def test_cap_watermark_no_previous_state_creates_file_without_suspicion(self, tmp_path):
        """Arrange: chưa có file state, lane đông nhất 10 card.
        Act: check_and_update. Assert: không nghi ngờ (chưa có mốc để so), file
        state được tạo với mốc 10.
        """
        # Arrange
        state = tmp_path / "kanban-cap-watermark.json"

        # Act
        verdict = self._tracker().check_and_update_watermark(10, 10, state_path=state)

        # Assert
        assert verdict["cap_drop_suspected"] is False
        assert verdict["watermark"] is None
        assert json.loads(state.read_text(encoding="utf-8"))["observed_max"] == 10

    def test_cap_watermark_observed_equal_to_watermark_no_suspicion(self, tmp_path):
        """CA ÂM — Arrange: mốc cũ 10, lần này vẫn 10.
        Act: check_and_update. Assert: không nghi (board không hề tụt).
        """
        # Arrange
        state = tmp_path / "s.json"
        state.write_text(json.dumps({"observed_max": 10}), encoding="utf-8")

        # Act
        verdict = self._tracker().check_and_update_watermark(10, 10, state_path=state)

        # Assert
        assert verdict["cap_drop_suspected"] is False
        assert verdict["watermark"] == 10

    def test_cap_watermark_observed_above_watermark_raises_watermark_no_suspicion(self, tmp_path):
        """Arrange: mốc cũ 10, lần này 12 (cap phía server TĂNG).
        Act: check_and_update. Assert: không nghi GIẢM, mốc được nâng lên 12
        (chiều tăng đã có `cap_changed` lo, tracker không được cướp việc).
        """
        # Arrange
        state = tmp_path / "s.json"
        state.write_text(json.dumps({"observed_max": 10}), encoding="utf-8")

        # Act
        verdict = self._tracker().check_and_update_watermark(12, 10, state_path=state)

        # Assert
        assert verdict["cap_drop_suspected"] is False
        assert json.loads(state.read_text(encoding="utf-8"))["observed_max"] == 12

    def test_cap_watermark_observed_below_watermark_at_cap_suspects_drop(self, tmp_path):
        """CA CHÍNH — Arrange: từng thấy lane đầy 10 (== cap), lần này tối đa 5.
        Act: check_and_update + cap_drop_hint. Assert: bật nghi ngờ, câu cảnh báo
        nêu cả hai số VÀ nêu điểm mù "board vơi thật".
        """
        # Arrange
        state = tmp_path / "s.json"
        state.write_text(json.dumps({"observed_max": 10}), encoding="utf-8")
        tracker = self._tracker()

        # Act
        verdict = tracker.check_and_update_watermark(5, 10, state_path=state)
        hint = tracker.cap_drop_hint(verdict, 10)

        # Assert
        assert verdict["cap_drop_suspected"] is True
        assert "10" in hint and "5" in hint
        assert "VƠI THẬT" in hint
        assert "MỘT lần" in hint
        assert json.loads(state.read_text(encoding="utf-8"))["observed_max"] == 5

    def test_cap_watermark_below_watermark_never_reached_cap_no_suspicion(self, tmp_path):
        """CA ÂM then chốt — Arrange: mốc cũ 7, CHƯA từng chạm cap 10; nay còn 3.
        Act: check_and_update. Assert: KHÔNG nghi — board chưa bao giờ đầy tới
        ngưỡng cắt thì việc nó vơi đi không mang thông tin gì về cap.
        """
        # Arrange
        state = tmp_path / "s.json"
        state.write_text(json.dumps({"observed_max": 7}), encoding="utf-8")

        # Act
        verdict = self._tracker().check_and_update_watermark(3, 10, state_path=state)

        # Assert
        assert verdict["cap_drop_suspected"] is False
        assert self._tracker().cap_drop_hint(verdict, 10) is None

    def test_cap_watermark_corrupted_state_file_treated_as_no_watermark(self, tmp_path):
        """FAIL-SAFE — Arrange: file state chứa rác không phải JSON.
        Act: check_and_update. Assert: không ném, coi như chưa có mốc, và GHI ĐÈ
        được bằng mốc mới (state hỏng không được kẹt vĩnh viễn).
        """
        # Arrange
        state = tmp_path / "s.json"
        state.write_text("{khong-phai-json", encoding="utf-8")

        # Act
        verdict = self._tracker().check_and_update_watermark(9, 10, state_path=state)

        # Assert
        assert verdict["watermark"] is None
        assert verdict["cap_drop_suspected"] is False
        assert json.loads(state.read_text(encoding="utf-8"))["observed_max"] == 9

    def test_cap_watermark_unwritable_state_dir_does_not_raise(self, tmp_path):
        """FAIL-SAFE — Arrange: thư mục state không có quyền ghi.
        Act: check_and_update. Assert: KHÔNG ném (cảnh báo phụ trợ tuyệt đối
        không được làm chết digest), vẫn trả đủ 3 key.
        """
        # Arrange
        locked = tmp_path / "locked"
        locked.mkdir()
        locked.chmod(0o500)
        try:
            # Act
            verdict = self._tracker().check_and_update_watermark(
                4, 10, state_path=locked / "sub" / "s.json")

            # Assert
            assert set(verdict) == {"cap_drop_suspected", "watermark", "observed_max", "state_path"}
            assert verdict["cap_drop_suspected"] is False
        finally:
            locked.chmod(0o700)

    def test_cap_watermark_observed_still_at_or_above_cap_no_suspicion(self, tmp_path):
        """CA ÂM (N1) — Arrange: mốc cũ 12 (cap từng cao hơn), cap hiện 10, nay 11.
        Act: check_and_update. Assert: KHÔNG nghi — 11 >= cap 10 nghĩa là board VẪN
        chạm ngưỡng cắt, cap không thể đã tụt xuống dưới 11. Thiếu vế này thì tụt
        mốc-cao-hơn-cap nào cũng kêu oan.
        """
        # Arrange
        state = tmp_path / "s.json"
        state.write_text(json.dumps({"observed_max": 12}), encoding="utf-8")

        # Act
        verdict = self._tracker().check_and_update_watermark(11, 10, state_path=state)

        # Assert
        assert verdict["cap_drop_suspected"] is False

    @pytest.mark.parametrize("bad_value", ["10", True, 10.9, None, [1, 2], {"a": 1}])
    def test_cap_watermark_wrong_typed_observed_max_treated_as_no_watermark(
        self, tmp_path, bad_value,
    ):
        """FAIL-SAFE (N2) — Arrange: state JSON hợp lệ nhưng `observed_max` sai KIỂU.
        Act: check_and_update. Assert: coi như chưa có mốc, không ném.
        `True` phải bị loại riêng vì bool LÀ int trong Python (lọt = mốc 1).
        """
        # Arrange
        state = tmp_path / "s.json"
        state.write_text(json.dumps({"observed_max": bad_value}), encoding="utf-8")

        # Act
        verdict = self._tracker().check_and_update_watermark(6, 10, state_path=state)

        # Assert
        assert verdict["watermark"] is None
        assert verdict["cap_drop_suspected"] is False

    def test_cap_watermark_stays_at_high_water_across_runs_without_suspicion(self, tmp_path):
        """N3 — Arrange: mốc 7 (CHƯA từng chạm cap 10), rồi quan sát 3 và 5.
        Act: chạy 2 lần. Assert: mốc GIỮ 7 cả hai lần — clamp đơn điệu `max()` là
        cơ chế cốt lõi của high-water mark; bỏ nó thì mốc trôi theo lần cuối và
        cảnh báo mất trí nhớ.
        """
        # Arrange
        state = tmp_path / "s.json"
        state.write_text(json.dumps({"observed_max": 7}), encoding="utf-8")
        tracker = self._tracker()

        # Act
        tracker.check_and_update_watermark(3, 10, state_path=state)
        after_first = json.loads(state.read_text(encoding="utf-8"))["observed_max"]
        tracker.check_and_update_watermark(5, 10, state_path=state)

        # Assert
        assert after_first == 7
        assert json.loads(state.read_text(encoding="utf-8"))["observed_max"] == 7

    def test_cap_watermark_suspicion_fires_once_then_rebaselines(self, tmp_path):
        """Q1-B — Arrange: mốc 10 (== cap), board tụt còn 5 rồi giữ 5.
        Act: chạy 2 lần liên tiếp. Assert: lần 1 NGHI, lần 2 IM (mốc đã đặt lại
        về 5). Cảnh báo kêu mãi mà thao tác thường không tắt được thì thành nhiễu
        — nhiễu giết đúng mục tiêu của #194.
        """
        # Arrange
        state = tmp_path / "s.json"
        state.write_text(json.dumps({"observed_max": 10}), encoding="utf-8")
        tracker = self._tracker()

        # Act
        first = tracker.check_and_update_watermark(5, 10, state_path=state)
        second = tracker.check_and_update_watermark(5, 10, state_path=state)

        # Assert
        assert first["cap_drop_suspected"] is True
        assert second["cap_drop_suspected"] is False
        assert second["watermark"] == 5

    def test_cap_watermark_write_uses_per_process_tmp_and_spares_foreign_tmp(
        self, tmp_path, monkeypatch,
    ):
        """RACE GHI STATE — Arrange: đặt sẵn 2 file tmp "của tiến trình khác":
        một mang PID lạ (`.tmp.99999`) và một KHÔNG mang PID (`.tmp` — đúng đường
        mà bản trước bản vá dùng, cũng là dạng rác pack cũ chưa sync để lại).
        Act: ghi mốc đường thật, rồi hoãn `os.replace` để tmp ở lại và ghi tiếp
        dưới HAI PID giả khác nhau.
        Assert: state đúng, hai tmp lạ NGUYÊN VẸN, và hai lượt ghi rơi vào HAI
        đường tmp khác nhau. Dùng chung một tên tmp thì lượt sau truncate đúng
        file lượt trước đang `os.replace` để promote ⇒ state nhận JSON CỤT, mà
        `_read_watermark` nuốt `ValueError` nên mốc mất KHÔNG dấu vết — máy đó mù
        vĩnh viễn với đợt cap tụt kế tiếp. Deterministic: không đua đồng hồ,
        không spawn tiến trình.
        """
        # Arrange
        tracker = self._tracker()
        state = tmp_path / "s.json"
        foreign_pid_tmp = tmp_path / "s.json.tmp.99999"
        foreign_pid_tmp.write_text("TMP-CUA-TIEN-TRINH-KHAC", encoding="utf-8")
        no_pid_tmp = tmp_path / "s.json.tmp"
        no_pid_tmp.write_text("TMP-KHONG-MANG-PID", encoding="utf-8")

        # Act
        verdict = tracker.check_and_update_watermark(5, 10, state_path=state)
        monkeypatch.setattr(tracker.os, "replace", lambda *a, **k: None)
        monkeypatch.setattr(tracker.os, "getpid", lambda: 111)
        tracker._write_watermark(state, 6, 5)
        monkeypatch.setattr(tracker.os, "getpid", lambda: 222)
        tracker._write_watermark(state, 7, 6)
        tmp_names = {f.name for f in tmp_path.iterdir() if ".tmp" in f.name}

        # Assert
        assert verdict["cap_drop_suspected"] is False
        assert json.loads(state.read_text(encoding="utf-8"))["observed_max"] == 5
        assert foreign_pid_tmp.read_text(encoding="utf-8") == "TMP-CUA-TIEN-TRINH-KHAC"
        assert no_pid_tmp.read_text(encoding="utf-8") == "TMP-KHONG-MANG-PID"
        assert {"s.json.tmp.111", "s.json.tmp.222"} <= tmp_names

    def test_observed_max_lane_size_empty_board_returns_zero(self):
        """Arrange: board 0 lane và board 3 lane cỡ 2/9/4.
        Act: observed_max_lane_size. Assert: 0 và 9 — hàm THUẦN, không I/O.
        """
        # Arrange
        import kanban_board_truncation_cap_detector as detector
        board = _board_with_lane_sizes({"A": 2, "B": 9, "C": 4})

        # Act + Assert
        assert detector.observed_max_lane_size({"lanes": []}) == 0
        assert detector.observed_max_lane_size(board) == 9


class TestDigestCapDropIntegration:
    """Digest phải mang cờ `cap_drop_suspected` ra CẢ hai nhánh output."""

    _make_digest_module = TestTodoDetail._make_digest_module
    _run_digest = TestDigestTruncationFlag._run_digest
    _FAKE_CREDS = TestDigestTruncationFlag._FAKE_CREDS

    def test_digest_cap_drop_key_present_in_both_output_modes(
        self, capsys, monkeypatch, tmp_path,
    ):
        """Arrange: state trỏ tmp_path (KHÔNG đụng state thật), board 3 lane nhỏ.
        Act: chạy digest cả chế độ thường lẫn --todo-detail.
        Assert: key `cap_drop_suspected` CÓ MẶT ở cả hai (key vắng mặt im lặng
        đúng là loài lỗi #194), và 4 key cũ không bị mất.
        """
        # Arrange
        board = _board_with_lane_sizes({"Backlog": 3, "Todo": 2, "Done": 4})

        # Act
        _, captured_plain = self._run_digest(monkeypatch, capsys, board, ["prog"])
        _, captured_detail = self._run_digest(
            monkeypatch, capsys, board, ["prog", "--todo-detail"])

        # Assert
        for captured in (captured_plain, captured_detail):
            digest = json.loads(captured.out)
            assert "cap_drop_suspected" in digest
            assert digest["cap_drop_suspected"] is False
            for key in ("cap", "truncated", "truncated_lanes", "cap_changed"):
                assert key in digest

    def test_digest_cap_drop_after_watermark_at_cap_warns_on_stderr(
        self, capsys, monkeypatch, tmp_path,
    ):
        """CA CHÍNH đầu-cuối — Arrange: lần 1 board có lane đầy 10 (ghi mốc), lần 2
        board tối đa 5 card.
        Act: chạy digest hai lần liên tiếp.
        Assert: lần 2 bật `cap_drop_suspected` trong JSON VÀ in cảnh báo ra stderr.
        """
        # Arrange
        board_full = _board_with_lane_sizes({"Backlog": 10, "Todo": 2})
        board_shrunk = _board_with_lane_sizes({"Backlog": 5, "Todo": 2})

        # Act
        self._run_digest(monkeypatch, capsys, board_full, ["prog"])
        _, captured = self._run_digest(monkeypatch, capsys, board_shrunk, ["prog"])

        # Assert
        assert json.loads(captured.out)["cap_drop_suspected"] is True
        assert "NGHI cap phía server đã GIẢM" in captured.err


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
