#!/usr/bin/env python3
"""Scan source files for OWASP Top 10 patterns + credential leaks + NAL rules.

Usage:
    python3 scan-files-for-owasp-vulnerabilities-and-credential-leaks.py \\
      --files "src/auth.ts src/payment.ts" \\
      --format markdown

Architecture (v0.4 refactor):
Scanner logic (file walk, per-extension comment skipping, render markdown/JSON,
exit-code mapping) lives in scripts/source_code_scanner_framework_base.py.
This file only declares the OWASP+NAL-specific pattern catalog plus a couple
of overrides: secret-file detection + secret masking in output snippets.
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

# Locate the shared framework. Same layout contract used by all team-ai-pack
# scripts: <root>/skills/<skill>/scripts/<this> → <root>/scripts/.
# If Avatar CLI ever changes that contract, this will fail loud at import time.
SCRIPT_DIR = Path(__file__).resolve().parent
TEAM_PACK_SCRIPTS = SCRIPT_DIR.parent.parent.parent / "scripts"
if not (TEAM_PACK_SCRIPTS / "source_code_scanner_framework_base.py").is_file():
    raise RuntimeError(
        f"team-ai-pack scanner framework not found at {TEAM_PACK_SCRIPTS}. "
        f"Expected layout: <root>/scripts/ and <root>/skills/<skill>/scripts/<file>. "
        f"If Avatar CLI changed the sync structure, set TEAM_PACK_ROOT env var."
    )
sys.path.insert(0, str(TEAM_PACK_SCRIPTS))

from source_code_scanner_framework_base import (  # noqa: E402
    Finding,
    SourceCodeScanner,
    read_files_from_args,
)

# Ép stdio về UTF-8. Claude Code gửi/nhận JSON UTF-8, còn Python trên Windows lấy bảng mã
# locale cho pipe: cp932 nuốt dấu `\` của JSON và không mã hoá được tiếng Việt.
for _stream, _errors in ((sys.stdin, "surrogateescape"), (sys.stdout, "backslashreplace"),
                         (sys.stderr, "backslashreplace")):
    try:
        _stream.reconfigure(encoding="utf-8", errors=_errors)
    except Exception:  # luồng bị thay (test double) hoặc đã đóng: giữ nguyên
        pass


def _sql_in_literal(body: str) -> str:
    """Lookahead: the literal whose characters match `body` holds a SQL shape
    (SELECT…FROM, INSERT INTO, UPDATE…SET, DELETE FROM; case via caller flags).

    Each keyword gets its own greedy lookahead bounded by the literal, so the
    cost stays linear per literal. Keyword ORDER is not checked: nested lazy
    gaps (`.*?SELECT.*?FROM`) backtrack cubically and hang on minified lines.
    """
    return (
        rf"(?=(?:{body}*\bINSERT\s+INTO\b|{body}*\bDELETE\s+FROM\b"
        rf"|(?={body}*\bSELECT\b){body}*\bFROM\b"
        rf"|(?={body}*\bUPDATE\b){body}*\bSET\b))"
    )


_DQ, _SQ, _BT = r'[^"\n]', r"[^'\n]", r"[^`]"


# (pattern, severity, label, suggestion, extra_dict_with_owasp_ref)
# The framework treats `extra` as opaque per-rule metadata. We use it to attach
# the OWASP Top 10 reference for display.
RULES = [
    # CRITICAL
    (
        re.compile(r'(?:api[_-]?key|secret|password|token)\s*[:=]\s*["\'](?!\.|process|env|\$)[^"\']{8,}["\']', re.IGNORECASE),
        "CRITICAL", "Hardcoded credential",
        "Move to env var: `process.env.X` and add to .env (gitignored).",
        {"OWASP": "A02 Cryptographic Failures"},
    ),
    (
        re.compile(r'(?:sk|pk|nal)_(?:live|test)_[A-Za-z0-9]{16,}'),
        "CRITICAL", "Exposed API key",
        "Rotate the key immediately, move to env var.",
        {"OWASP": "A02 Cryptographic Failures"},
    ),
    (
        re.compile(r'\bAKIA[0-9A-Z]{16}\b'),
        "CRITICAL", "Exposed AWS access key ID",
        "Deactivate the key in IAM, move credentials to env/secret manager.",
        {"OWASP": "A02 Cryptographic Failures"},
    ),
    (
        re.compile(r'\bghp_[A-Za-z0-9]{36}\b'),
        "CRITICAL", "Exposed GitHub token",
        "Revoke the token on GitHub, move to env var / CI secret.",
        {"OWASP": "A02 Cryptographic Failures"},
    ),
    (
        # "SELECT … FROM t WHERE id=" + id  (also INSERT/UPDATE/DELETE)
        re.compile(
            rf'(?:"{_sql_in_literal(_DQ)}{_DQ}*"|\'{_sql_in_literal(_SQ)}{_SQ}*\')\s*\+',
            re.IGNORECASE,
        ),
        "CRITICAL", "SQL string concatenation",
        "Use parameterized queries: `db.query('SELECT * FROM users WHERE id=$1', [id])`.",
        {"OWASP": "A03 Injection"},
    ),
    (
        # `SELECT … ${id}` — JS/TS template literal with interpolation
        re.compile(rf'`(?={_BT}*\$\{{){_sql_in_literal(_BT)}', re.IGNORECASE),
        "CRITICAL", "SQL built with template literal",
        "Use parameterized queries / query builder instead of `${…}` inside SQL.",
        {"OWASP": "A03 Injection"},
    ),
    (
        # f"SELECT … {uid}" — Python f-string with interpolation
        re.compile(
            rf'\b(?:[rR][fF]|[fF][rR]?)'
            rf'(?:"(?={_DQ}*\{{){_sql_in_literal(_DQ)}|\'(?={_SQ}*\{{){_sql_in_literal(_SQ)})',
            re.IGNORECASE,
        ),
        "CRITICAL", "SQL built with f-string",
        "Use driver placeholders: `cur.execute('SELECT … WHERE id = %s', (uid,))`.",
        {"OWASP": "A03 Injection"},
    ),
    (
        re.compile(r'dangerouslySetInnerHTML.*\{[^}]*(?:props|user|input|body|param)', re.IGNORECASE),
        "CRITICAL", "dangerouslySetInnerHTML with user input",
        "Sanitize via DOMPurify, or render as text.",
        {"OWASP": "A03 Injection (XSS)"},
    ),
    (
        re.compile(r'\beval\s*\('),
        "CRITICAL", "eval() usage",
        "Never use eval. Refactor logic to avoid runtime code execution.",
        {"OWASP": "A03 Injection"},
    ),
    (
        re.compile(r'new\s+Function\s*\('),
        "CRITICAL", "Function constructor",
        "Equivalent to eval — refactor without dynamic code generation.",
        {"OWASP": "A03 Injection"},
    ),

    # HIGH
    (
        re.compile(r'\b(?:md5|sha1)\s*\(', re.IGNORECASE),
        "HIGH", "Weak hash algorithm",
        "Use SHA-256+ for integrity, bcrypt/argon2 for passwords.",
        {"OWASP": "A02 Cryptographic Failures"},
    ),
    (
        re.compile(r'createCipher\s*\([^,)]*(?:DES|RC4)', re.IGNORECASE),
        "HIGH", "Weak cipher",
        "Use AES-256-GCM or ChaCha20-Poly1305.",
        {"OWASP": "A02 Cryptographic Failures"},
    ),
    (
        re.compile(r'Math\.random\(\).*(?:token|secret|session|key)', re.IGNORECASE),
        "HIGH", "Math.random for security",
        "Use crypto.randomBytes() / crypto.randomUUID() for security tokens.",
        {"OWASP": "A02 Cryptographic Failures"},
    ),
    (
        # Options object on the same line that does not set BOTH httpOnly and
        # secure (key present and not `false`).
        re.compile(
            r'\b(?:cookie|setCookie|cookie\.serialize|cookies(?:\(\))?\.set)\s*\([^{}\n]*\{'
            r'(?!(?=[^}]*\bhttpOnly\s*:(?!\s*false\b))(?=[^}]*\bsecure\s*:(?!\s*false\b)))'
            r'[^}]*\}',
            re.IGNORECASE,
        ),
        "HIGH", "Cookie missing httpOnly/secure",
        "Set `httpOnly: true, secure: true, sameSite: 'lax'` on cookies.",
        {"OWASP": "A05 Security Misconfiguration"},
    ),
    (
        re.compile(r'\bexec\s*\([^)]*(?:req\.|body|params|query|input)', re.IGNORECASE),
        "HIGH", "exec() with user input",
        "Use spawn() with arg array, NEVER concat user input into shell string.",
        {"OWASP": "A03 Injection (Command)"},
    ),
    (
        re.compile(r'jwt\.sign\([^,)]*,\s*["\'][^"\']{1,32}["\']'),
        "HIGH", "JWT secret short or hardcoded",
        "Use 256-bit+ secret from env var: `process.env.JWT_SECRET`.",
        {"OWASP": "A02 Cryptographic Failures"},
    ),
    (
        re.compile(r'console\.log\([^)]*(?:req\.body|req\.headers|password|token|secret)', re.IGNORECASE),
        "HIGH", "Sensitive data in log",
        "Mask sensitive fields before logging. Never log full req.body in prod.",
        {"OWASP": "A09 Security Logging Failures"},
    ),
    (
        # supabase-js: .or(`name.eq.${q}`) lets the caller inject extra filters
        re.compile(r'\.(?:or|filter)\(\s*`[^`]*\$\{'),
        "HIGH", "supabase-js filter built from template literal",
        "Validate/escape the value (allowlist), or use typed filters `.eq(col, value)`.",
        {"OWASP": "A03 Injection"},
    ),

    # MEDIUM
    (
        re.compile(r'JSON\.parse\([^)]*(?:req\.|body|params|query)'),
        "MEDIUM", "Unguarded JSON.parse on user input",
        "Wrap in try/catch + size limit. Better: use validator (zod).",
        {"OWASP": "A05 Security Misconfiguration"},
    ),
    (
        re.compile(r'new\s+RegExp\([^)]*(?:req\.|body|params|input)'),
        "MEDIUM", "RegExp from user input (ReDoS)",
        "Use allowlist regex literals, or escape user input with `escape-string-regexp`.",
        {"OWASP": "A05 Security Misconfiguration"},
    ),
    (
        re.compile(r'cors\(\{?\s*origin:\s*["\']\*["\']'),
        "MEDIUM", "Permissive CORS",
        "Allowlist specific origins, never `*` for endpoints with credentials.",
        {"OWASP": "A05 Security Misconfiguration"},
    ),
    (
        re.compile(r'https?://[^/\s"\']+:[^@\s"\']+@'),
        "MEDIUM", "URL with embedded credentials",
        "Pass credentials separately (Authorization header or body field).",
        {"OWASP": "A02 Cryptographic Failures"},
    ),

    # NAL-specific (HIGH severity)
    (
        # NEXT_PUBLIC_* is inlined into the client bundle. Public-by-design keys
        # (Supabase anon, Stripe publishable, reCAPTCHA site key) are excluded.
        re.compile(
            r'\bprocess\.env\.NEXT_PUBLIC_(?!\w*(?:ANON|PUBLISHABLE|SITE)_KEY\b)'
            r'(?:\w*_)?(?:KEY|SECRET|TOKEN|PASSWORD|PRIVATE)(?:_\w*)?\b'
        ),
        "HIGH", "Secret-looking NEXT_PUBLIC_ env var leaks to client bundle (NAL rule)",
        "Drop the NEXT_PUBLIC_ prefix and read the secret only on the server.",
        {"OWASP": "NAL Convention + A02"},
    ),
    (
        re.compile(r'(?:webhook[Ss]ecret|sepay[Ss]ecret).*===\s*'),
        "HIGH", "Webhook secret compared with === (NAL rule)",
        "Use `crypto.timingSafeEqual(Buffer.from(a), Buffer.from(b))` to prevent timing attack.",
        {"OWASP": "NAL Convention + A02"},
    ),
    (
        # Logging sink + VN phone (0xxxxxxxxx) or 12-digit CCCD on the same line
        re.compile(
            r'(?:\b(?:console|logger|logging)\.\w+|\bprint)\s*\(.*?(?:\b0\d{9}\b|\b\d{12}\b)'
        ),
        "HIGH", "Vietnam PII (phone/CCCD) in log output (NAL rule)",
        "Mask: `phone.slice(0,4) + '***' + phone.slice(-3)`.",
        {"OWASP": "NAL Convention + PDPD"},
    ),

    # LOW
    (
        re.compile(r'app\.listen\([^,)]+\)\s*;'),
        "LOW", "app.listen without host binding",
        "Bind to `127.0.0.1` in dev, env-controlled in prod.",
        {"OWASP": "Best practice"},
    ),
    (
        re.compile(r'TODO:?\s*security', re.IGNORECASE),
        "LOW", "Unfinished security work",
        "Either fix now or open ticket — don't ship 'TODO: security'.",
        {"OWASP": "Tech debt"},
    ),
]


# Whole-file flags: anything matching these patterns gets a CRITICAL finding
# at line 0 because the file *itself* shouldn't be in the repo.
#
# Detected:
#   .env, .env.local, .env.production, .env.staging, .env.development, etc.
#   .envrc (direnv — commonly contains `export SECRET_KEY=...`)
#   secrets.json, secrets.yaml, secrets.yml (case-insensitive)
# Whitelisted suffixes (templates, not real secrets):
#   .example, .sample, .tpl, .template
# Path-anchored so 'no-secrets.json' does NOT trigger but 'secrets.json' at any
# directory level does. Case-insensitive so 'SECRETS.JSON' is also caught.
SECRET_FILE_PATTERNS = re.compile(
    r"(?:^|/)\.env(?:\.(?!example|sample|tpl|template)[a-z0-9_-]+)?$"
    r"|(?:^|/)\.envrc$"
    r"|(?:^|/)secrets\.(?:json|ya?ml)$",
    re.IGNORECASE,
)


# Key-shaped tokens: keep the prefix + 4 chars, hide the rest.
_KEY_SHAPED = re.compile(r'\b((?:sk|pk|nal)_(?:live|test)_|ghp_|AKIA)([A-Za-z0-9]{4})\w*')


def mask_secret(snippet: str) -> str:
    """Hide credential-looking values inside a code snippet."""
    snippet = _KEY_SHAPED.sub(r'\1\2***', snippet)
    return re.sub(
        r'((?:api[_-]?key|secret|password|token)\s*[:=]\s*["\'])([^"\']{4})[^"\']*(["\'])',
        r'\1\2***\3',
        snippet,
        flags=re.IGNORECASE,
    )


# Severity-aware rendering: relabel `Reference` to use the OWASP value
def _render_markdown_with_owasp(findings: list[Finding], files_count: int) -> str:
    """Custom render that emits 'Reference:' line from extra['OWASP'] + Status verdict."""
    if not findings:
        return (
            f"## Security Scan Result\n\n"
            f"**Files scanned:** {files_count}\n"
            f"**Findings:** 0\n"
            f"**Status:** ✓ Clean\n"
        )

    by_severity: dict[str, list[Finding]] = {}
    for f in findings:
        by_severity.setdefault(f.severity, []).append(f)

    from source_code_scanner_framework_base import SEVERITY_BANDS
    counts = {sev: len(by_severity.get(sev, [])) for sev in SEVERITY_BANDS}
    summary = ", ".join(f"{n} {sev.lower()}" for sev, n in counts.items() if n)

    if counts.get("CRITICAL", 0) > 0:
        status = "⛔ BLOCK MERGE — fix CRITICAL findings first"
    elif counts.get("HIGH", 0) > 0:
        status = "⚠ FIX BEFORE DEPLOY — HIGH findings require action"
    else:
        status = "✓ Review MEDIUM/LOW findings"

    out = [
        "## Security Scan Result",
        "",
        f"**Files scanned:** {files_count}",
        f"**Findings:** {summary}",
        f"**Status:** {status}",
        "",
    ]
    for severity in sorted(by_severity.keys(), key=lambda s: SEVERITY_BANDS[s]):
        items = by_severity[severity]
        out.append(f"### {severity} ({len(items)})")
        out.append("")
        for f in items:
            loc = f"{f.file}:{f.line}:{f.col}" if f.line else f.file
            out.append(f"#### `{loc}` — {f.pattern}")
            out.append("```")
            out.append(f.snippet)
            out.append("```")
            owasp = (f.extra or {}).get("OWASP", "—")
            out.append(f"**Reference:** {owasp}")
            out.append(f"**Fix:** {f.suggestion}")
            out.append("")
    return "\n".join(out)


class SecurityScanner(SourceCodeScanner):
    """OWASP + NAL-rule scanner with secret masking + .env file detection."""
    rules = RULES
    accepted_extensions = {
        # Code only — docs/data (.md, .html, .json, .tpl) would turn SQL or key
        # examples into false CRITICALs. Secret files (.env, secrets.json) are
        # caught by name in scan_file() before this filter applies.
        ".js", ".jsx", ".ts", ".tsx", ".cjs", ".mjs",
        ".py", ".rb", ".go", ".java", ".php", ".cs",
        ".sh", ".bash", ".yml", ".yaml", ".sql",
    }
    report_title = "Security Scan Result"

    def __init__(self):
        super().__init__(snippet_processor=mask_secret)

    def scan_file(self, path: Path) -> list[Finding]:
        if not path.exists():
            return []
        # Block binary/build artifacts immediately
        if path.suffix in (".png", ".jpg", ".pdf", ".lock", ".log"):
            return []

        # Whole-file secret file → 1 finding then short-circuit
        # Use POSIX-style path so the (?:^|/) anchor works on both filename-only
        # and full-path inputs.
        if SECRET_FILE_PATTERNS.search(path.as_posix()):
            return [
                Finding(
                    file=str(path), line=0, col=0, severity="CRITICAL",
                    pattern=".env or secrets file in repo",
                    snippet="(entire file)",
                    suggestion="Add to .gitignore. If accidentally committed, rotate all secrets + git filter-repo.",
                    extra={"OWASP": "A02 Cryptographic Failures"},
                )
            ]

        # Delegate to framework for line-by-line scanning (extension filter +
        # comment-skip).
        return super().scan_file(path)


def main() -> int:
    files, output_format = read_files_from_args()
    files = [f for f in files if f.exists()]
    if not files:
        if output_format == "json":
            print(SecurityScanner.render_json([], 0))
        else:
            print("## Security Scan Result\n\nKhông có file để scan.\n")
        return 0

    scanner = SecurityScanner()
    all_findings: list[Finding] = []
    for f in files:
        all_findings.extend(scanner.scan_file(f))

    if output_format == "markdown":
        print(_render_markdown_with_owasp(all_findings, len(files)))
    else:
        print(scanner.render_json(all_findings, len(files)))

    return scanner.exit_code_for_findings(all_findings)


if __name__ == "__main__":
    sys.exit(main())
