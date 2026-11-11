"""Regression tests for security-scanner rules, secret masking and CLI output.

Rules are matched against single source lines (no filesystem): the framework
scans line by line, so a line-level check exercises the same regexes.
Fake credentials are assembled at runtime so secret scanners do not flag this file.
"""
import importlib.util
import json
import sys
from pathlib import Path

SCRIPT_PATH = (
    Path(__file__).resolve().parent.parent
    / "scan-files-for-owasp-vulnerabilities-and-credential-leaks.py"
)
_spec = importlib.util.spec_from_file_location("security_scanner_under_test", SCRIPT_PATH)
scanner = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(scanner)

FAKE_STRIPE = "sk_" + "test_" + "abcdefghijklmnop1234"
FAKE_AWS = "AKIA" + "ABCDEFGHIJKLMNOP"
FAKE_GITHUB = "ghp_" + "abcdefghijklmnopqrstuvwxyz0123456789"


def labels_for(line):
    """Labels of every rule that matches `line`."""
    return [rule[2] for rule in scanner.RULES if rule[0].search(line)]


def has_label(labels, keyword):
    """Keyword match so a renamed label cannot make a negative test pass."""
    return any(keyword in label for label in labels)


# --- 1. cookie options -------------------------------------------------------

def test_security_scanner_cookie_with_httponly_and_secure_not_flagged():
    # Arrange
    line = 'res.cookie("s", t, { httpOnly: true, secure: true, sameSite: "lax" });'
    # Act
    labels = labels_for(line)
    # Assert
    assert not has_label(labels, "Cookie")


def test_security_scanner_cookie_without_httponly_flagged_high():
    # Arrange
    line = 'res.cookie("s", t, { secure: true, sameSite: "lax" });'
    # Act
    labels = labels_for(line)
    # Assert
    assert has_label(labels, "Cookie")


def test_security_scanner_cookie_with_secure_false_flagged_high():
    # Arrange
    line = 'cookies().set("s", t, { httpOnly: true, secure: false });'
    # Act
    labels = labels_for(line)
    # Assert
    assert has_label(labels, "Cookie")


# --- 2. masking --------------------------------------------------------------

def test_security_scanner_mask_secret_key_shaped_values_hidden_in_snippet():
    # Arrange
    snippet = f'const a = "{FAKE_STRIPE}"; const b = "{FAKE_AWS}"; const c = "{FAKE_GITHUB}";'
    # Act
    masked = scanner.mask_secret(snippet)
    # Assert
    for secret in (FAKE_STRIPE, FAKE_AWS, FAKE_GITHUB):
        assert secret not in masked
    assert "sk_test_abcd***" in masked
    assert "AKIAABCD***" in masked
    assert "ghp_abcd***" in masked


# --- 3. credential rules -----------------------------------------------------

def test_security_scanner_aws_access_key_id_flagged_critical():
    # Arrange
    line = f'const aws = "{FAKE_AWS}";'
    # Act
    labels = labels_for(line)
    # Assert
    assert "Exposed AWS access key ID" in labels


def test_security_scanner_github_token_flagged_critical():
    # Arrange
    line = f'const gh = "{FAKE_GITHUB}";'
    # Act
    labels = labels_for(line)
    # Assert
    assert "Exposed GitHub token" in labels


# --- 4. SQL injection shapes -------------------------------------------------

def test_security_scanner_sql_template_literal_interpolation_flagged():
    # Arrange
    line = "const q = `SELECT * FROM users WHERE id = ${id}`;"
    # Act
    labels = labels_for(line)
    # Assert
    assert "SQL built with template literal" in labels


def test_security_scanner_sql_python_fstring_interpolation_flagged():
    # Arrange
    line = "cur.execute(f\"select * from users where name = '{name}'\")"
    # Act
    labels = labels_for(line)
    # Assert
    assert "SQL built with f-string" in labels


def test_security_scanner_sql_delete_concatenation_flagged():
    # Arrange
    line = 'db.query("DELETE FROM users WHERE id = \'" + id + "\'");'
    # Act
    labels = labels_for(line)
    # Assert
    assert "SQL string concatenation" in labels


def test_security_scanner_sql_parameterized_query_not_flagged():
    # Arrange
    line = 'db.query("SELECT * FROM users WHERE id = $1", [id]);'
    # Act
    labels = labels_for(line)
    # Assert
    assert not has_label(labels, "SQL")


def test_security_scanner_ui_template_literal_without_sql_shape_not_flagged():
    # Arrange
    line = "const msg = `Select ${count} items to delete`;"
    # Act
    labels = labels_for(line)
    # Assert
    assert not has_label(labels, "SQL")


# --- 5. supabase-js filter injection -----------------------------------------

def test_security_scanner_supabase_or_with_template_literal_flagged_high():
    # Arrange
    line = 'supabase.from("t").select().or(`name.eq.${q},id.eq.1`);'
    # Act
    labels = labels_for(line)
    # Assert
    assert "supabase-js filter built from template literal" in labels


def test_security_scanner_array_filter_arrow_function_not_flagged():
    # Arrange
    line = "rows.filter((r) => `${r.name}`.includes(q));"
    # Act
    labels = labels_for(line)
    # Assert
    assert not has_label(labels, "supabase")


# --- 6. env access -----------------------------------------------------------

def test_security_scanner_plain_next_public_env_not_flagged():
    # Arrange
    lines = [
        "const url = process.env.NEXT_PUBLIC_SITE_URL;",
        "const anon = process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY;",
        "const db = process.env.DATABASE_URL;",
    ]
    # Act
    results = [labels_for(line) for line in lines]
    # Assert
    assert results == [[], [], []]


def test_security_scanner_secret_next_public_env_flagged_high():
    # Arrange
    line = "const k = process.env.NEXT_PUBLIC_STRIPE_SECRET_KEY;"
    # Act
    labels = labels_for(line)
    # Assert
    assert labels == ["Secret-looking NEXT_PUBLIC_ env var leaks to client bundle (NAL rule)"]


def test_security_scanner_deno_env_service_role_read_not_flagged():
    # Arrange
    line = 'const serviceRoleKey = Deno.env.get("SUPABASE_SERVICE_ROLE_KEY")!;'
    # Act
    labels = labels_for(line)
    # Assert
    assert labels == []


# --- 7. PII in logs ----------------------------------------------------------

def test_security_scanner_vn_phone_in_console_log_flagged_high():
    # Arrange
    line = 'console.log("call", user.name, "0901234567");'
    # Act
    labels = labels_for(line)
    # Assert
    assert has_label(labels, "PII")


def test_security_scanner_number_near_phone_word_without_log_not_flagged():
    # Arrange
    line = "const maxMobileWidth = 123456789; // mobile breakpoint"
    # Act
    labels = labels_for(line)
    # Assert
    assert not has_label(labels, "PII")


# --- 8. scanned extensions ---------------------------------------------------

def test_security_scanner_docs_and_data_extensions_not_scanned_as_code():
    # Arrange
    excluded = {".md", ".html", ".tpl", ".json"}
    # Act
    accepted = scanner.SecurityScanner.accepted_extensions
    # Assert
    assert excluded.isdisjoint(accepted)
    assert scanner.SECRET_FILE_PATTERNS.search("config/secrets.json")


# --- 9. JSON output with no files --------------------------------------------

def test_security_scanner_json_format_with_no_existing_files_prints_valid_json(
    monkeypatch, capsys,
):
    # Arrange
    monkeypatch.setattr(
        sys, "argv",
        ["scan", "--files", "/nonexistent/security-scanner-input.ts", "--format", "json"],
    )
    # Act
    code = scanner.main()
    # Assert
    payload = json.loads(capsys.readouterr().out)
    assert code == 0
    assert payload == {"files_scanned": 0, "findings_count": 0, "findings": []}


# --- regex cost on long (minified) lines ------------------------------------

def test_security_scanner_rules_long_minified_line_scans_under_one_second():
    # Arrange: nested lazy SQL gaps once took >120 s on lines like these
    lines = [
        'x="' + "select a from b where " * 3000 + '"',
        "x='" + "SELECT a FROM b where " * 3000 + "'",
        "`" + "select ${x} from " * 3000,
        'f"' + "{x} select update " * 3000 + '"',
        'var q="select "+' * 4000 + "1;",
    ]
    import time
    # Act
    start = time.perf_counter()
    for line in lines:
        labels_for(line)
    elapsed = time.perf_counter() - start
    # Assert: acceptance threshold 1 s for all lines together
    assert elapsed < 1.0, f"rules took {elapsed:.2f}s on long lines"
