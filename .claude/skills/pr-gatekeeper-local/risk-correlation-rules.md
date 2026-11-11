# Risk Correlation Rules — PR Gatekeeper Local

> Công thức tính Risk TỔNG, port nguyên từ PR Gatekeeper (`RISK_ASSESSMENT_FORMULA.md`).
> **Đây là logic DETERMINISTIC (rule-based). Claude áp dụng đúng từng bước, KHÔNG tự "cảm tính" quyết định risk.**
> Risk tổng hợp từ 3 nguồn: AI-Quality + AI-Security + GitNexus-Impact (call-graph).

## Nguyên tắc chung

Risk tính theo **5 bước tuần tự**, rule đầu tiên khớp là **dừng** (short-circuit evaluation).

```
RISK_TỔNG = f(base_risk, quality_findings, security_findings, gitnexus_impact)
```

Trong bản local:
- `base_risk` ← từ GitNexus `detect_changes` (nếu index có). Nếu index rỗng → base = MEDIUM (thận trọng).
- `quality_findings` ← Claude tự review diff (thay SonarQube)
- `security_findings` ← Claude tự review diff (thay Semgrep)
- `gitnexus_impact` ← GitNexus `impact()` cho caller count + flows

---

## Step 1 — Base Risk (từ GitNexus detect_changes)

`detect_changes` trả về: changed symbols, affected flows, breaking changes, `risk_level`.

| detect_changes risk | Base risk |
|---------------------|-----------|
| LOW                 | LOW       |
| MEDIUM              | MEDIUM    |
| HIGH                | HIGH      |
| CRITICAL            | CRITICAL  |

> **Lưu ý:** đây là BASE risk — chỉ đổi khi bước sau có bằng chứng cụ thể.
> Nếu GitNexus rỗng/không chạy → base = MEDIUM + ghi rõ "Impact Gate unavailable" trong report.
> **Base chỉ tính symbol PRODUCTION.** Symbol trong **test file** và **section markdown** (vd `gitnexus analyze` tự sửa `.md`) KHÔNG tính vào `changed_count` của base — nếu không base bị thổi phồng (case 260716: 22 changed_symbols nhưng 13 là test harness + 2 là section `.md`). Đọc base ở mức tương ứng riêng symbol production.

---

## Step 2 — BLOCK Check (ưu tiên cao nhất)

Nếu **bất kỳ** điều kiện nào thỏa → **BLOCK** ngay, dừng:

| # | Điều kiện | Giải thích |
|---|-----------|------------|
| 1 | Quality gate FAILED + có bất kỳ CRITICAL issue | Code không đạt + vấn đề nghiêm trọng |
| 2 | detect_changes CRITICAL + có CRITICAL security/quality trong changed files | Breaking change + critical bug = không merge |
| 3 | Breaking change (GitNexus) + có code smells trong cùng symbols | API đổi + quality kém = phải refactor |

**Kết quả:** `BLOCK` → PR bị chặn.

---

## Step 3 — Escalation Rules

Nếu không BLOCK, áp dụng **rule KHỚP ĐẦU TIÊN** (theo thứ tự ưu tiên):

| # | Điều kiện | Escalation |
|---|-----------|------------|
| 1 | CRITICAL security + **5+ d=1 callers** | → **CRITICAL** |
| 2 | CRITICAL security + symbol trên **user-input flow** (injection path) | → **CRITICAL** |
| 3 | CRITICAL security + symbol trên **critical execution flow** | → **HIGH** |
| 4 | Quality gate FAILED (không có CRITICAL) | → **HIGH** |
| 5 | HIGH security + **3+ d=1 callers** | → **HIGH** |
| 6 | HIGH security + symbol trên **critical flow** | → **HIGH** |
| 7 | MAJOR code smell + **5+ d=1 callers** | → **HIGH** |
| 8 | base risk + **3+ d=1 callers ngoài PR diff** | → **+1 level** |
| 9 | impact() có d=1 callers nhưng PR **không có test files** | → **+1 level** |

### Thuật ngữ
| Thuật ngữ | Ý nghĩa |
|-----------|---------|
| **d=1 callers** | Direct callers — hàm/class gọi trực tiếp symbol đổi. Không update → SẼ BREAK |
| **user-input flow** | Flow từ HTTP/API endpoint → symbol đổi → DB/output. Risk injection (SQLi, XSS) |
| **critical flow** | Flow quan trọng: auth, payment, data persistence, security |
| **ngoài PR diff** | Caller tồn tại nhưng PR không update file đó → breaking change |

---

## Step 4 — Downgrade Rules

Chỉ áp dụng nếu **KHÔNG có escalation nào khớp** ở Step 3:

| # | Điều kiện | Kết quả |
|---|-----------|---------|
| 1 | CRITICAL/HIGH security nhưng **0 callers** (dead code) | → **MEDIUM** |
| 2 | MAJOR code smell nhưng **0 callers** + không trong flow | → **LOW** |
| 3 | **PR sạch**: quality gate PASS + **0 security** + **0 smell** + **0 d=1 caller ngoài PR diff** + PR **có test** | → **hạ tới sàn MEDIUM** (CRITICAL→MEDIUM · HIGH→MEDIUM · MEDIUM→LOW · LOW giữ nguyên) |

> **Rule 3 (chống kẹt gate khi PR 0 finding):** base risk từ `detect_changes` thuần cơ học — sinh từ SỐ execution flow bị chạm, không từ chất lượng code; chỉ "chạm" một hàm hub (route handler, `syncAction` của `avatar sync`) đã đủ ra HIGH hoặc `critical`. Khi PR hoàn toàn sạch (0 finding, 0 caller ngoài diff bị break) thì rule 1&2 (đều cần *có* finding để hạ) KHÔNG có đường hạ → PR càng sạch càng kẹt. Vì vậy rule 3 hạ **tới sàn MEDIUM**, KHÔNG phải cứng 1 nấc: bản cũ mở đúng 1 nấc nên chữa được base HIGH (VD6) nhưng base `critical` chỉ rơi xuống HIGH ⇒ `pretooluse-pr-review-gate-hook.py` vẫn deny, mà lại KHÔNG có finding nào để "fix cho hết deny" (ca #227, 260819 — bế tắc kín, phải hở gate 22s mới push được). Sàn là MEDIUM và KHÔNG BAO GIỜ xuống LOW khi base ≥ HIGH: base cao nghĩa là blast radius thật sự rộng, vẫn đáng một lượt người đọc (MEDIUM = NEEDS DISCUSSION — push được, nhưng không tự động APPROVE). Rule chỉ khớp khi **0 finding tuyệt đối** nên không đụng rule 1&2 (cần finding). Ba vế chặn giữ NGUYÊN răng: có security issue ⇒ rule 3 không khớp (đòi 0 security) và Guard bên dưới vẫn giữ sàn MEDIUM · có 3+ caller ngoài diff (breaking) hoặc thiếu test ⇒ Step 3 rule 8/9 escalation khớp ⇒ **Step 4 không chạy**, rule 3 không với tới (VD8·VD9·VD10).

### 🛡️ Downgrade Guard (BẮT BUỘC)
Nếu PR chứa BẤT KỲ issue thuộc `security` / `vulnerability` / `security_hotspot`:
→ **CHẶN HOÀN TOÀN** việc hạ risk tổng xuống `LOW`. Mức tối thiểu = **MEDIUM**.
Lý do: API có thể bị gọi qua reflection/external → an toàn tuyệt đối, bắt buộc human review.

---

## Step 5 — Final Decision

| Risk TỔNG | Recommendation | Merge? |
|-----------|----------------|--------|
| **BLOCK** | 🛑 BLOCK — fix hết CRITICAL mới merge | ❌ |
| **CRITICAL** | ⚠️ REQUEST CHANGES — cần review senior | ❌ |
| **HIGH** | ⚠️ REQUEST CHANGES — fix trước khi merge | ❌ |
| **MEDIUM** | 💬 NEEDS DISCUSSION — merge sau khi discuss | ⚠️ cần approve |
| **LOW** | ✅ APPROVE — an toàn merge | ✅ |

---

## Ví dụ self-verify (phải ra đúng kết quả này)

**VD1 — BLOCK:** detect=MEDIUM, quality FAILED + 5 CRITICAL, security 2 HIGH (SQLi)
→ Step 2 rule 1 khớp → **BLOCK**

**VD2 — CRITICAL:** detect=LOW, 1 CRITICAL SQLi (quality PASS), impact 8 d=1 callers
→ Step 3 rule 1 (CRITICAL + 8≥5) → **CRITICAL**

**VD3 — HIGH:** detect=MEDIUM, 1 HIGH XSS, impact 4 callers
→ Step 3 rule 5 (HIGH + 4≥3) → **HIGH**

**VD4 — LOW:** detect=LOW, 3 MAJOR (dead code), 0 callers, không security
→ Step 4 rule 2 → **LOW**

**VD5 — MEDIUM (Guard):** 1 HIGH security trong dead code (0 callers)
→ Step 4 rule 1 → MEDIUM (Guard chặn xuống LOW) → **MEDIUM**

**VD6 — MEDIUM (PR sạch, base HIGH):** detect=HIGH (chỉ vì chạm route handler), quality PASS, 0 security, 0 smell, 0 d=1 caller ngoài diff, PR có test (case `63a515f`, 260716)
→ Step 2 no BLOCK · Step 3 no escalation (không finding) · Step 4 rule 3 (PR sạch) → hạ 1 level HIGH→**MEDIUM** (hết kẹt HIGH). Guard không áp (0 security).

**VD7 — MEDIUM (PR sạch, base CRITICAL):** detect=CRITICAL (chạm `syncAction`, 17 flow), quality PASS, 0 security, 0 smell, d=1 caller = 1 **và được update trong diff** (0 caller ngoài diff), PR có test 4 ca (case #227, 260819)
→ Step 2 no BLOCK (0 CRITICAL finding) · Step 3 no escalation (rule 8 đòi 3+ caller ngoài diff, có 0; rule 9 đòi thiếu test, PR có test) · Step 4 rule 3 (PR sạch) → CRITICAL→**MEDIUM**. Guard không áp (0 security). ⚠️ Bản rules cũ (hạ cứng 1 nấc) ra HIGH ⇒ gate deny mà không có finding nào để fix — chính là lỗi #279.

**VD8 — MEDIUM (có security finding ⇒ rule 3 KHÔNG khớp):** detect=CRITICAL, 1 HIGH security trong dead code, 0 callers, PR có test
→ Step 3 rule 5/6 không khớp (0 caller, không trên critical flow) · Step 4 rule 3 KHÔNG khớp (đòi 0 security) · rule 1 khớp (HIGH security + 0 callers) → MEDIUM, Guard chặn xuống LOW → **MEDIUM**. Sàn MEDIUM của rule 3 KHÔNG phải cửa hậu cho PR có security issue.

**VD9 — CRITICAL (breaking change ⇒ Step 4 không chạy):** detect=CRITICAL, 0 finding, PR có test, nhưng **4 d=1 caller ngoài diff** không được update
→ Step 3 rule 8 khớp (3+ caller ngoài diff) → +1 level, trần là CRITICAL → **CRITICAL**. Step 4 KHÔNG chạy (đã có escalation) ⇒ rule 3 không với tới. Ca 1–2 caller ngoài diff: rule 8 chưa khớp, nhưng rule 3 đòi **0** caller ngoài diff ⇒ cũng không hạ, giữ nguyên base.

**VD10 — CRITICAL (0 finding nhưng KHÔNG có test):** detect=CRITICAL, 0 finding, impact() có 2 d=1 caller, PR 0 file test
→ Step 3 rule 9 khớp (có d=1 caller + PR không có test) → +1 level, trần CRITICAL → **CRITICAL**. Step 4 không chạy. Rule 3 cũng đòi "PR có test" ⇒ hai lớp chặn cùng chiều.
