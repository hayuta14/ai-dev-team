---
name: pr-gatekeeper-local
description: AI-powered PR review using 3-Tier Gates (Quality, Security, Impact) + GitNexus call-graph correlation + deterministic risk formula. Activate when reviewing a Pull Request or code diff, assessing merge risk, or analyzing blast radius / cross-repo impact of changes. Local-first — no Docker, no external AI API (Claude is the reviewer). This is the automated risk-scored merge gate; for the human-loop discipline of giving/receiving review feedback and gating completion claims use the `code-review` skill instead.
---

# PR Gatekeeper Local

Review PR dựa trên **tác động THẬT** của thay đổi (ai gọi, gãy gì, luồng nào) — quyết định
BLOCK/PASS tự động, nhất quán, có bằng chứng. Thay vì "code này trông ổn không?" (chủ quan)
→ "thay đổi này làm gãy cái gì, mức độ bao nhiêu, có được merge không?" (khách quan).

**Reviewer chính là Claude** (phiên đang chạy) — không gọi API ngoài, không cần key AI.

## 5 đảm bảo bản chất (phải giữ trong mọi review)
1. Mọi symbol đổi đều được tính Blast Radius qua call-graph (GitNexus)
2. Severity điều chỉnh theo ngữ cảnh thật (escalation/downgrade + Downgrade Guard)
3. Quyết định BLOCK/PASS deterministic — theo `risk-correlation-rules.md`, KHÔNG cảm tính
4. Evidence-based — mọi finding neo vào tool thật (diff + GitNexus), không phán bừa
5. Hiểu cross-repo (khi có ecosystem/group)

## 3-Tier Gates (bản local)

| Gate | Bản gốc | Bản local | Block khi |
|------|---------|-----------|-----------|
| **Quality** | SonarQube | Claude review diff | Quality FAILED + CRITICAL, hoặc breaking change tại vùng code kém |
| **Security** | Semgrep | Claude review diff | CRITICAL/HIGH security trên luồng có hàm gọi |
| **Impact** | GitNexus | GitNexus MCP (giữ nguyên) | Ảnh hưởng lan rộng vượt mức |

### Quality Gate — Claude tìm:
code smell, độ phức tạp cao, duplication trong diff, bug logic (off-by-one, thiếu null check, sai điều kiện), maintainability.

### Security Gate — Claude tìm:
injection (SQL/command/XSS), lộ secrets/hardcoded credentials, auth/authorization flaw, unsafe API, taint từ user input → sink nguy hiểm.

### Impact Gate — GitNexus cung cấp (KHÔNG fake bằng AI):
d=1 callers count, execution flows bị ảnh hưởng, breaking changes, caller ngoài PR diff.

## Review Workflow (port từ prompts_internal.py — 6 bước)

> **Code Content Rule:** Graph chứa BASELINE (main). PR changes KHÔNG có trong graph.
> → Đọc code thay đổi từ **git diff**, dùng GitNexus CHỈ cho quan hệ (callers, flows, imports).
> NEVER query nội dung hàm từ graph (trả code CŨ → sai).

**Step 1 — Analyze changes:**
- `detect_changes(scope: "compare", base_ref: <pr_base_sha>)` → changed symbols, flows, base risk
- Đọc git diff để hiểu bản chất thay đổi (feature/bugfix/refactor)
- Claude review diff theo Quality + Security gate → list findings `{file, line, type, severity}`

**Step 2 — Blast radius:**
- Với mỗi symbol đổi: `impact(target, direction: "upstream", includeTests: true, maxDepth: 3)`
- Checklist: d=1 callers có được update trong PR? Flow nào gãy? Consumer ngoài diff?
- API/HTTP change → `query()` tìm consumer dùng string literal (test, CI, client, docs)

**Step 3 — Test coverage:** từ `impact(includeTests: true)` — thiếu test cho code đổi → flag, +1 level.

**Step 3.5 — Gộp trùng + phản biện finding CRITICAL/HIGH** (trước correlation, vì một finding sai ở mức này đủ để BLOCK):
- **Gộp trùng theo đoạn code bị bắt lỗi**, không theo tiêu đề hay số dòng (Quality và Security hay bắt cùng một dòng với tên khác nhau): một finding mỗi đoạn code, giữ severity nặng nhất, ghi cả hai gate đã thấy nó.
- **Phản biện từng finding CRITICAL/HIGH còn lại** như thể mình là tác giả muốn bác nó: tìm guard ở upstream (middleware, wrapper, kiểm ở caller), test chứng minh ca đó đã xử lý, hoặc lý do đường đi không tới được. Bác chỉ khi trích được `file:line` của guard/test đó → hạ mức hoặc bỏ, ghi lý do (finding đã bị bác bằng bằng chứng không còn là finding; Downgrade Guard ở Step 6 chỉ áp cho finding còn đứng). Không tìm được bằng chứng bác ⇒ **giữ nguyên mức** (fail-closed; không chắc không phải lý do hạ security).
- MEDIUM/LOW đi thẳng sang Step 4, không phản biện.
- Báo cáo ghi số finding trước/sau gộp và từng finding đã bị bác kèm bằng chứng.

**Step 4 — Context deep-dive:** symbol HIGH-RISK (d=1 > 5 hoặc trên critical flow) → `context(name, include_content: false)`.

**Step 5 — Affected flows:** đọc `gitnexus://repo/<name>/processes` — flow nào bị ảnh hưởng + độ quan trọng.

**Step 6 — Correlation + Risk:** áp `risk-correlation-rules.md` (5 bước) → Risk TỔNG.

## Risk formula
→ Xem `risk-correlation-rules.md` (cùng thư mục). Áp dụng nguyên văn, deterministic.

## Báo cáo (tiếng Việt, evidence-based)
```
## 📊 Tóm tắt thay đổi
<symbols đổi, loại thay đổi>

## 🎯 Risk TỔNG: <LEVEL>
<lý do — rule nào khớp, bằng chứng caller/flow>

## 🔍 Findings (theo severity)
- [SEVERITY] <mô tả> (`file:line`) — bằng chứng: <caller count / flow / diff>

## ✅ Recommendation
<BLOCK / REQUEST CHANGES / NEEDS DISCUSSION / APPROVE>
```

## Fallback khi GitNexus rỗng/unavailable
- base risk = MEDIUM, ghi rõ "⚠️ Impact Gate unavailable — review AI-only, thiếu call-graph"
- Vẫn chạy Quality + Security gate. Cảnh báo độ tin cậy giảm (mất đảm bảo #1).
- Claude chủ động đọc thêm file liên quan qua Read/Grep để bù phần call-graph nếu cần.
