# Planning Council Protocol (GĐ1)

Protocol chuẩn cho luồng lập kế hoạch GĐ1. Command `/avatar:plan*` load file này làm nguồn chung để mọi command con (fast/hard/parallel/ci/two) chạy cùng một quy trình, chống drift giữa các entry point.

Luồng gồm 8 phase (Phase 0 → Phase 7). Mỗi phase có input rõ, output rõ, và điều kiện chuyển tiếp. Không nhảy phase, không gộp phase.

---

## Phase 0 — Clarify & route

- Normalize `$ARGUMENTS` thành 3 phần: **goal** (kết quả cần đạt), **constraints** (ràng buộc bắt buộc), **unknowns** (điều chưa rõ cần làm rõ).
- Check `.claude/active-plan` **đúng 1 lần** ở entry command. Nếu reuse plan cũ → đọc stage hiện có và **tiếp tục đúng stage đó**. Command con **KHÔNG hỏi active-plan lần 2**.
- Nếu thiếu thông tin có thể **đổi scope hoặc architecture** → hỏi user **trước discovery**, không đoán.
- Chọn profile theo routing signals (fast / hard / parallel / ci / two).
- Tạo plan dir + ghi `.claude/active-plan` bằng **safe relative path** (chống symlink escape khỏi workspace).
- Router ghi **routing-log** nêu lý do chọn profile theo signals cụ thể — KHÔNG ghi free-form.
- **Plan-monitor init:** Main sinh `trace_id` (UUID4 mới, conceptually `planning_council_state.new_trace_id()`), ghi projection state khởi tạo `{trace_id, profile, stage: "route", plan_path: <safe-relative-plan-dir>}` vào `.claude/state/planning-council/<trace_id>.json`. `plan_path` = ĐÚNG safe relative path đã ghi vào `.claude/active-plan` (vd `plans/20260715-1504-…`) → cho phép `/avatar:debate` sau này recover trace_id của plan này để join debate thread vào cùng trace (§4a). Collector CHỈ ĐỌC file này read-only — CHỈ Main/command được ghi (xem §8 dưới + `planning_council_state.write_state`). Xem "Plan-monitor marker & event-block format" ở cuối file cho schema đầy đủ.

**Output:** goal/constraints/unknowns đã normalize, selected profile, plan dir, routing-log, `trace_id` + projection state khởi tạo.

---

## Phase 1 — Independent discovery

- Spawn **0–2 Researcher song song**, CHỈ khi có ít nhất một trigger: external dependency, version-sensitive, standards-compliance, package-upstream, prior-art cần verify, **infra/deploy** (task chạm pipeline CI/CD, Dockerfile/image, Helm/K8s/ArgoCD, migration DB dùng chung, biến môi trường/secret). Không trigger → không spawn Researcher.
- Trigger **infra/deploy** fire ⇒ MỘT trong các suất Researcher spawn bằng `subagent_type: devops-engineer` (lens `infra`) thay cho `researcher`. Vẫn tính vào trần 0–2, vẫn ghi vào `research/`, marker plan-monitor vẫn dùng role `researcher` (KHÔNG thêm role mới vào `ALLOWED_ROLES`).
- Spawn **ĐÚNG 1 Scout** độc lập (luôn có).
  - Field Scout đọc: `WS`, `TASK`, `REPOS` (repo tuyệt đối trong phạm vi, không mặc định cả `src/`), `QUESTIONS` (nếu có), `OUTPUT_PATH` (tuyệt đối, `{plan-dir}/scout/…`), `PROFILE` (`council` cho hard/two, `parallel`, `ci`), `TRACE_ID`.
- Mỗi Researcher dùng **lens khác nhau** + ghi `research_trigger` (lý do được spawn).
- Main truyền cho từng agent: task, scope, **explicit output_path**, artifact schema. Researcher nhận đúng các field trong `agents/researcher.md` §Input contract: `QUESTIONS` (đánh số, câu hỏi ngoài thật), `LENS`, `STACK` (đường dẫn manifest), `OUTPUT_PATH` (tuyệt đối), `TRIGGER`, `BUDGET`, `TRACE_ID`, `WS`.
- **KHÔNG cho agent đọc report của agent khác** (chống groupthink).
- Researcher ghi vào `research/`, Scout ghi vào `scout/`.
- **Plan-monitor markers (stage = `evidence_discovery`):**
  - Spawn Scout → marker `[PM:<trace-id>:evidence_discovery:scout:01:none:0]` vào Task `description`.
  - Spawn Researcher-NN → marker `[PM:<trace-id>:evidence_discovery:researcher:0N:none:0]` vào Task `description`.
  - Main truyền **full `trace_id`** (không phải short form) trong Task prompt cho từng agent, để agent echo lại đúng `trace_id` trong return block.
  - **Không trigger nào fire** (0 Researcher) → **KHÔNG** Task, **KHÔNG** marker, **KHÔNG** fake failure span. Thay vào đó Main ghi projection state `expected_researchers: "not_required"` (field allow-listed thật, xem `_ALLOWED_FIELDS`). Đây LÀ tín hiệu not_required — qua STATE WRITE, không qua block.
  - Có trigger fire (1–2 Researcher) → Main có thể ghi `expected_researchers: <int count>`.

**Output:** Scout report + 0–2 Researcher report, mỗi cái ở đúng thư mục; markers đã inject; `expected_researchers` đã ghi vào projection state.

---

## Phase 2 — Draft Shared Understanding

- Main đọc **mọi discovery report** → tạo `shared-understanding.md` (SU) theo `shared-understanding-contract.md`.
- **Dedupe** claims trùng.
- Tách rõ **fact / assumption / opinion**.
- Gắn **evidence** cho từng claim.
- Ghi rõ **contradiction** khi report mâu thuẫn — KHÔNG âm thầm chọn 1 bên.
- KHÔNG đưa **implementation steps** vào SU (SU là intent, không phải plan).
- KHÔNG chốt **architecture** khi evidence còn thiếu.

**Output:** `shared-understanding.md` status = DRAFT.

---

## Phase 3 — Inline functional review (thay 4-lens council)

- Main **tự đối chiếu** draft SU theo `functional-review-checklist.md` (4 góc: business / backend / frontend / test). **KHÔNG spawn agent** cho bước này.
- Mỗi góc cho ra: **confirmed** / **corrections** (có evidence) / **objections** / **DECISION_REQUIRED**.
- Merge corrections **có evidence**. Reject objection **không evidence** — ghi rationale vào section Dissent.
- Mâu thuẫn evidence → ưu tiên **current source-of-truth**. Không resolve được → chuyển thành **human decision** hoặc đánh dấu **unknown**.
- Evidence gap → giao **đúng 1 targeted follow-up** (Scout hoặc Researcher, phạm vi hẹp). KHÔNG mở open-ended loop.
- **Max 2 review passes.**
- Sau review: status = **CHALLENGED** (đã soi, còn technical điểm cần merge/chốt) hoặc **WAITING_USER_DECISION** (còn item phải hỏi user).
- **Plan-monitor (stage = `functional_review`):** sau khi inline review xong (≤2 passes), Main ghi projection state `per_lens_counts` = **FLAT 16-key** `{"<lens>_<disposition>": <int>}` cho 4 lens (`business`/`backend`/`frontend`/`test`) × 4 disposition (`confirmed`/`corrections`/`objections`/`decision_required`) + `stage: "functional_review"`, qua `planning_council_state.write_state`. **Ghi ĐÚNG 1 LẦN** sau khi CẢ 2 pass (nếu có) đã xong — **KHÔNG ghi giữa chừng** (giữa pass 1 và pass 2). Lý do: giữ một event duy nhất cho số cuối của Phase 3. `pm_event_id` của `inline_review_counts` gồm hash của counts: ghi lại cùng số thì dedupe, còn ghi 2 lần khác số sẽ ra 2 event (số giữa chừng không bị lọc mất, nhưng làm dashboard thấy số tạm). Chỉ số cuối cùng của Phase 3 mới được ghi. **METADATA-ONLY tuyệt đối:** chỉ SỐ ĐẾM nguyên, KHÔNG BAO GIỜ nội dung text của correction/objection/decision (nội dung đó ở lại SU/plan local, không gửi remote). Xem "Plan-monitor marker & event-block format" §3 cho schema `per_lens_counts` đầy đủ.

**Output:** SU đã review, status CHALLENGED hoặc WAITING_USER_DECISION; projection state có `per_lens_counts` + `stage: functional_review`.

---

## Phase 4 — SU user gate

- Main trình bày **tóm tắt ngắn**: goal / scope / acceptance criteria / assumptions quan trọng / dissent đã resolve / **toàn bộ human decision còn lại**.
- **Plan-monitor gate-write (waiting) — TRƯỚC khi DỪNG:** Main Read projection state file hiện có (`.claude/state/planning-council/<trace_id>.json`), merge `gates.understanding_user_gate = false` vào dict `gates` đã có (giữ nguyên gate khác nếu đã tồn tại, vd `plan_selection_gate` của profile `two`), rồi Write lại (Read-merge-Write — KHÔNG overwrite cả dict). Xem §3 "Projection-state API" cho field allowlist.
- **DỪNG**, chờ **explicit user response**. KHÔNG spawn Planner trước gate.
- User đồng ý → apply answers vào SU; status → **CONFIRMED**.
- **Plan-monitor gate-write (passed) — NGAY SAU CONFIRMED:** Read-merge-Write lại `gates.understanding_user_gate = true` (giữ gate khác trong dict).
- Tính `shared_understanding_sha256`.
- Ghi / update `.claude/state/plan-attestations/<plan-id>.json` — **1 attestation contract duy nhất** cho plan (SU hash + plan hash cùng file).
- KHÔNG lưu raw prompt / raw response của user vào state.

**Output:** SU status = CONFIRMED, SU hash, attestation file khởi tạo; projection state có `gates.understanding_user_gate` waiting(`false`)→passed(`true`).

---

## Phase 5 — Planner creates plan

- Spawn **đúng 1 Planner** cho profile fast/hard/parallel/ci. Profile **two** = spawn **2 Planner độc lập** (2 phương án so sánh).
- Planner **input bắt buộc**: confirmed SU path + SU hash; Scout/Researcher evidence paths **thật**; selected profile; **exact output dir**; existing code/docs/standards paths; artifact schema. Truyền đúng tên field agent đọc: `PROFILE`, `SU`, `SU_SHA256`, `EVIDENCE`, `OUTPUT_DIR` (tuyệt đối), `CONTEXT`, `DIRECTION` (chỉ `two`), `TRACE_ID`, `INSTANCE` (`01`/`02`), `WS`.
- Planner phải:
  - Coi SU là **immutable**.
  - Map **mọi acceptance criteria → ≥1 phase/task** + verification.
  - Ghi **source links** trỏ về SU cho từng quyết định.
  - KHÔNG thêm unrequested scope.
  - KHÔNG implement code.
  - KHÔNG ghi APPROVED (approval không thuộc thẩm quyền Planner).
- Nếu SU thiếu/sai → Planner **dừng**, trả `UNDERSTANDING_REOPEN_REQUIRED` kèm evidence. Main set SU = **DRIFTED**, quay lại Phase 2/4.
- **Plan-monitor markers (stage = `planning`):**
  - Spawn Planner → marker `[PM:<trace-id>:planning:planner:01:none:0]` vào Task `description`. Main truyền full `trace_id` trong prompt.
  - Profile **two** → spawn planner:01 VÀ planner:02, mỗi cái marker riêng (`...:planner:01:...` và `...:planner:02:...`), VÀ ghi projection state selection gate qua field allow-listed `gates`: `{"plan_selection_gate": false}` (đang chờ), flip `true` khi user chọn xong phương án. KHÔNG dùng field top-level `selection_gate` — không nằm trong `_ALLOWED_FIELDS`, sẽ bị drop.

**Output:** plan artifacts (`plan.md` + `phase-*.md`) trong output dir; markers đã inject; profile `two` có selection gate trong `gates`.

---

## Phase 6 — Automatic debate gate

- Sau khi plan artifacts viết xong, `/avatar:plan` **TỰ chạy debate** — user KHÔNG cần gọi `/avatar:debate` riêng.
- **Ngoại lệ profile `fast`:** KHÔNG tự debate. Chỉ khi task có `--debate` mới chạy **một** lượt `debate-skeptic` trên `model: sonnet`, không Refiner, không final rescan (chi tiết: `commands/avatar/plan/fast.md` bước 2). Phần còn lại của Phase 6 áp cho hard/parallel/two/ci.
- Model Skeptic theo blast radius: xem `commands/avatar/debate.md` Bước 0-rounds (`sonnet` khi thấp, `opus` cho vòng 1 + final_rescan khi cao).
- Debate review **toàn plan bundle**:
  - **read-only reference** = `shared-understanding.md`.
  - **writable** = `plan.md` + `phase-*.md`.
- Skeptic kiểm thêm (ngoài checklist debate mặc định):
  - Mọi acceptance criteria map task + verification.
  - Không plan claim nào mâu thuẫn SU.
  - Paths/patterns tồn tại hoặc được đánh dấu **create**.
  - Cross-phase dependency nhất quán.
  - Có rollback / failure handling.
  - Test/review gate **đo được**.
  - Không silent scope drift.
  - Profile **parallel**: mỗi phase có **exclusive file ownership** + dependency graph hợp lệ (không cycle).
- Refiner **chỉ sửa** `plan.md`/`phase-*.md` (SU read-only). Nếu blocking chỉ giải được bằng **đổi intent** → Refiner không sửa, debate trả **NEEDS_DECISION**.
- Terminal verdict:
  - **APPROVE** → final full re-scan → Phase 7.
  - **NEEDS_DECISION** → hỏi user. Đổi intent → reopen SU + re-plan + re-debate. Chỉ là design choice → update plan + re-debate.
  - **ESCALATE** → dừng, show blocking + evidence.
  - **CONTINUE** → Refiner sửa, vòng tiếp trong budget.

**Output:** debate verdict + plan bundle đã refine (nếu có).

---

## Phase 7 — Final user approval

- **Chỉ sau debate APPROVE.** Ngoại lệ profile `fast` (không có vòng debate, Phase 6): vào Phase 7 ngay sau Planner.
- Hiển thị: plan path / phase summary / major trade-offs / số debate rounds + verdict.
- **Plan-monitor gate-write (waiting) — TRƯỚC khi hỏi user:** Read projection state, merge `gates.plan_user_gate = false` vào dict `gates` đã có (giữ gate khác, vd `understanding_user_gate` đã `true` từ Phase 4), Write lại (Read-merge-Write). Xem §3.
- Hỏi user duyệt. **DỪNG**, chờ explicit response.
- User approve →
  - Tính 2 hash: `plan_content_sha256` = sha256 của riêng `plan.md`; `plan_bundle_sha256` = sha256 của danh sách `<sha256>  <tên file>` trên `plan.md` + mọi `phase-*.md`, sort theo tên — dùng `plan_stage_common.plan_bundle_sha256(plan_dir)` hoặc lệnh `cd <plan_dir> && shasum -a 256 phase-*.md plan.md | LC_ALL=C sort -k2 | shasum -a 256`.
  - Update attestation đang có: `plan_content_sha256`, `plan_bundle_sha256`, `plan_approved=true`, `plan_approved_at`, `debate_verdict=APPROVE` (profile `fast`: `debate_verdict=NONE` khi không có `--debate`, `SKEPTIC_ONLY` khi có — không bao giờ ghi `APPROVE` cho plan chưa qua debate).
  - **Plan-monitor gate-write (passed):** Read-merge-Write lại `gates.plan_user_gate = true` (giữ gate khác trong dict) và ghi luôn `stage: "completed"` trong CÙNG lần ghi đó. Không có bước nào khác ghi `completed`; thiếu dòng này dashboard không bao giờ thấy run "Hoàn tất" (audit P07).
  - Trả plan path + command tiếp theo.
  - **KHÔNG tự chạy** `/avatar:implement` (approve không auto-chain implement).
- Plan bị **edit sau approval** → hash mismatch → status **DRIFTED** (phải re-approve).

**Output:** plan approved, attestation hoàn chỉnh, command kế tiếp gợi ý; projection state có `gates.plan_user_gate` waiting(`false`)→passed(`true`).

---

## Deterministic guardrails

Ràng buộc bất biến áp cho toàn protocol:

- **Exactly 1 Scout** + **0–2 Researcher** (mỗi Researcher phải có trigger). Không quorum-by-count.
- Review GĐ1 là **inline bởi Main** — KHÔNG spawn reviewer agent ở Phase 3.
- **Max 2 inline review passes.**
- Prompt cho mọi agent phải có **explicit input path + output path + schema**.
- **Số lượng agent ≠ consensus.** Evidence mới là authority, không phải "đa số agent đồng ý".
- **Confirmed SU hash** là precondition để Planner chạy.
- **Debate APPROVE** là precondition của final user approval.
- **Final user approval** là precondition của `/avatar:implement` — APPROVE **không** auto-chain implement.
- Mọi **write path** trong workspace / plan dir phải **chống symlink escape** (resolve + verify nằm trong workspace).

---

## Attestation contract

Attestation là **1 file duy nhất per-plan** — nguồn sự thật cho stage + hash gate. **Command ghi trực tiếp** (không có hook riêng ghi state — tránh state cạnh tranh). 2 continuity hook (`sessionstart-inject-plan-stage.py`, `precompact-inject-plan-stage.py`) chỉ **đọc** file này để inject stage + next-action (fail-open).

**Path (duy nhất):**

```text
<WORKING-DIR>/.claude/state/plan-attestations/<plan-id>.json
```

`<plan-id>` = **basename** của plan dir (vd `20260715-1430-oauth-login`). MỘT contract cho cả SU hash lẫn plan hash — không tách file, không state song song.

**Schema — sau SU gate (Phase 4):**

```json
{
  "plan_path": "plans/<plan-id>",
  "status": "WAITING_PLAN_APPROVAL",
  "shared_understanding_sha256": "<sha256 của shared-understanding.md>",
  "understanding_approved": true,
  "understanding_approved_at": "<ISO8601>",
  "plan_content_sha256": null,
  "plan_bundle_sha256": null,
  "plan_approved": false
}
```

**Schema — bổ sung sau plan approval (Phase 7):** giữ nguyên field trên, thêm/ghi đè:

```json
{
  "status": "APPROVED",
  "plan_content_sha256": "<sha256 của plan.md>",
  "plan_bundle_sha256": "<sha256 của danh sách sha256 plan.md + phase-*.md, sort theo tên>",
  "plan_approved": true,
  "plan_approved_at": "<ISO8601>",
  "debate_verdict": "APPROVE"
}
```

**State machine (persist trong `status`, KHÔNG chỉ để trong prose):**

```text
CREATED → DISCOVERING → UNDERSTANDING_DRAFT → UNDERSTANDING_CHALLENGE
  → WAITING_UNDERSTANDING_APPROVAL → PLANNING → DEBATING
  → WAITING_PLAN_APPROVAL → APPROVED
```

Trạng thái phụ (rẽ nhánh bất kỳ đâu): `DRIFTED` (hash mismatch sau khi đã approve → phải re-debate/re-approve), `NEEDS_DECISION` (debate trả NEEDS_DECISION, chờ user quyết), `ESCALATED` (debate ESCALATE, dừng).

**Ràng buộc:**

- **KHÔNG lưu raw prompt / raw user response** trong state (chỉ lưu quyết định đã chuẩn hoá + hash + timestamp).
- **Active-plan entry validation (fail-closed, brief §12):**
  - Chưa có active plan → tạo **ĐÚNG 1** plan dir + ghi `.claude/active-plan` bằng **safe relative path** (nằm dưới WORKING-DIR).
  - Active path **invalid / out-of-workspace** (symlink escape / absolute path ngoài workspace / traversal `..`) → **REJECT, fail-closed**: KHÔNG write theo path đó, KHÔNG inject. Chỉ chấp nhận pointer là **relative path resolve nằm trong workspace**.
- Debate hash gate: hook so `plan_bundle_sha256` (plan.md + mọi `phase-*.md`, kể cả phase thêm sau) khi attestation có trường này, và luôn so `plan_content_sha256` (chỉ `plan.md`). Attestation cũ chỉ có `plan_content_sha256` ⇒ sửa file phase KHÔNG bị phát hiện; ghi thêm `plan_bundle_sha256` để phủ. Plan bị edit sau approve → hash mismatch → `status=DRIFTED`. Hash đã ghi mà KHÔNG tính lại được (file không đọc được; entry `phase-*.md` không phải file thường nằm trong plan dir, vd symlink trỏ ra ngoài — entry đó không bị đọc và cả bộ bị từ chối) → `KHÔNG XÁC MINH`: chặn như DRIFTED, không auto-proceed.

---

## Plan-monitor marker & event-block format

**Nguồn định nghĩa DUY NHẤT** cho marker/block plan-monitor — mọi phase ở trên, mọi command con, mọi agent prompt tham chiếu về ĐÚNG section này, không định nghĩa lại (DRY). Phải khớp 1:1 với collector thật: `tools/telemetry/hooks/shared/planning_council_monitor.py` (`_MARKER_RE`, `_BLOCK_RE`, `ALLOWED_ROLES`, `ALLOWED_KINDS`) + `planning_council_state.py` (`_ALLOWED_FIELDS`, `_ALLOWED_PAYLOAD_KEYS`).

### 1. Marker (PreToolUse Task `description`)

```text
[PM:<trace-id>:<stage>:<role>:<instance>:none:<round>]
```

- ĐÚNG 6 field cách nhau bởi `:`. Field 5 là literal `none` (chỗ dành cho phase sau, GĐ1 chưa dùng). Không field nào chứa `:` hoặc `]`.
- `<trace-id>` = **full `trace_id`** (UUID4, nguyên trạng — không cắt) — KHÔNG slug, KHÔNG path. Phải KHỚP với `trace_id` dùng trong projection state + event block (§2) để agent_started emit cùng khóa nhóm run với mọi event khác.
- `<role>` ∈ `{scout, researcher, planner, debate-skeptic, debate-refiner}` (`ALLOWED_ROLES`). Lifecycle (Phase 0→5, phase-03 scope) chỉ dùng `scout` / `researcher` / `planner`; role debate là phase-05, KHÔNG dùng ở đây.
- `<instance>` = số 2 chữ số zero-padded (`01`, `02`, …).
- `<stage>` = tên stage tại spawn point đó: Scout/Researcher ở Phase 1 → `evidence_discovery`; Planner ở Phase 5 → `planning`.
- `<round>` = `0` cho mọi spawn lifecycle (round chỉ có ý nghĩa trong debate, phase-05).

Ví dụ thật: `[PM:a1b2c3d4-e5f6-4789-a1b2-c3d4e5f6a7b8:evidence_discovery:scout:01:none:0]`, `[PM:a1b2c3d4-e5f6-4789-a1b2-c3d4e5f6a7b8:planning:planner:02:none:0]`.

### 2. Event block (cuối return của agent)

```text
<avatar-plan-monitor-event>{"kind":"AGENT_DONE","trace_id":"<full-uuid>","role":"scout","instance":"01","round":"0"}</avatar-plan-monitor-event>
```

- Body là JSON hợp lệ, strict. `kind` ∈ `{AGENT_DONE, AGENT_FAILED, NOT_REQUIRED, ROUND_STARTED, FINDINGS, REFINED, VERDICT}` (`ALLOWED_KINDS`). `trace_id` bắt buộc, non-empty, **full UUID** (không phải short form).
- Metadata key tuỳ chọn collector sẽ giữ lại: `role, instance, round, counts, verdict, finding_ids, contribution_id, reply_to, expected_researchers, findings`. Field khác bị strip (`assert_metadata_only`); short-string field bị cap 64 ký tự `[A-Za-z0-9_.\-]`, dict bị cap 32 entries; `finding_ids` là list opaque id (mỗi id ≤64 ký tự cùng charset, cap 64 phần tử) — entry blob/path/heading bị strip. `finding_ids` vẫn opaque (không đổi); `findings` mang nội dung có cấu trúc `{id,text,artifact_path}` — xem §4c để biết schema + cap chi tiết.
- **METADATA-ONLY, TUYỆT ĐỐI (áp cho MỌI field TRỪ `findings`):** block KHÔNG BAO GIỜ chứa prompt text, nội dung report, file path, URL, slug, secret, hay free prose. Chỉ metadata lifecycle/counts. `finding_ids` CHỈ được mang opaque id (B1/D2/N1…) — KHÔNG bao giờ `section`/`artifact_path`/`issue` text.
- **Ngoại lệ CÓ CHỦ ĐÍCH — field `findings` (đảo ngược invariant metadata-only, user chốt):** `findings` là list ≤20 dict, mỗi dict `{id: short-id [A-Za-z0-9_.\-] ≤64 ký tự, text: str ≤2000 ký tự, artifact_path: str ≤200 ký tự (optional)}`. `text` = nội dung phân tích agent-written (issue của blocking, tradeoff/why của decision, note của nit — xem debate.md §serialize). Guard **KHÔNG sanitize** `text`/`artifact_path` — chỉ validate shape (đúng key, đúng type) + cap length (hygiene strip control/bidi codepoint riêng theo plan §D2, KHÔNG che secret/path/URL). Text vượt cap → guard TRUNCATE `text[:1999]+"…"` giữ nguyên item (KHÔNG drop, tránh desync với `finding_ids`). KHÔNG cố ý nhét secret vào text, nhưng nếu có thì đây là rủi ro user đã chấp nhận (quyết định 2) — KHÔNG có bước redact nội dung hiển thị được.
- Agent lifecycle (scout/researcher/planner) chỉ emit `AGENT_DONE` (thành công, có thể kèm `counts`) hoặc `AGENT_FAILED` (thất bại). KHÔNG emit `ROUND_STARTED`/`FINDINGS`/`REFINED`/`VERDICT` — đó là debate (§4).

### 3. Projection-state API (Main/command-side, KHÔNG phải agent)

- `.claude/state/planning-council/<trace_id>.json` — ghi qua `planning_council_state.write_state(project_dir, trace_id, patch)`, patch chỉ giữ field trong `_ALLOWED_FIELDS`: `trace_id, profile, stage, expected_researchers, round, per_lens_counts, verdict, plan_path, gates, agents, updated_at`. **Lưu ý:** `findings` (§4c) là field trong PAYLOAD của event block (`_ALLOWED_PAYLOAD_KEYS`), KHÔNG phải projection-state field — `_ALLOWED_FIELDS` ở trên KHÔNG đổi, KHÔNG thêm `findings` vào đây.
- `new_trace_id()` → UUID4 mới cho mỗi plan-council run.
- **`plan_path`** = safe relative plan dir (vd `plans/20260715-1504-…`) ghi lúc Phase 0 để `/avatar:debate` sau này recover ĐÚNG trace_id của plan này (join debate thread vào cùng trace). CHỈ dùng local recovery — collector KHÔNG bao giờ emit `plan_path` (không nằm trong `_ALLOWED_PAYLOAD_KEYS`), nên KHÔNG lên wire (AC6).
- Collector CHỈ ĐỌC file này (read-only) — không bao giờ tự ghi. Collector tự động derive event khi state file **đổi** (so per-file fingerprint + watermark), **KHÔNG phụ thuộc tool nào ghi** — Bash/script `cat > <trace>.json` cũng bắt được y như Write/Edit. Trigger: mọi `PostToolUse` (matcher `Bash|Task|Agent|Write|Edit|AskUserQuestion`) + **`SessionEnd` làm backstop** — quét lần cuối lúc thoát phiên để bắt ca state đổi rồi không còn tool call theo sau.
- **not_required signal** = ghi state `expected_researchers: "not_required"` (string) khi 0 researcher trigger — KHÔNG dùng field `researchers_not_required` (không tồn tại, sẽ bị `write_state` silently drop).
- **Selection gate (`two`)** = ghi qua field `gates` (dict `{gate_name: bool}`), KHÔNG dùng field top-level `selection_gate` (không có trong allowlist). Ví dụ: `gates: {"plan_selection_gate": false}` → `true` khi user chọn xong.
- **User gates (`understanding_user_gate` / `plan_user_gate`, MỌI profile)** = cũng ghi qua field `gates` giống selection gate — Phase 4 ghi `gates.understanding_user_gate` (`false` TRƯỚC khi DỪNG chờ user, `true` NGAY SAU CONFIRMED); Phase 7 ghi `gates.plan_user_gate` (`false` TRƯỚC khi hỏi user, `true` NGAY SAU approve). **Read-merge-Write cả dict `gates`** mỗi lần (KHÔNG overwrite cả dict) — vì `write_state`/merge shallow ở field top-level, ghi `gates: {...}` mới sẽ XOÁ gate khác đã có nếu không merge trước (vd mất `plan_selection_gate` của profile `two`, hoặc mất `understanding_user_gate` khi Phase 7 ghi `plan_user_gate`).
- **`per_lens_counts` (Phase 3 inline review)** = dict **FLAT** (KHÔNG nested) tối đa 16 key dạng `"<lens>_<disposition>": <int>`, lens ∈ `{business, backend, frontend, test}`, disposition ∈ `{confirmed, corrections, objections, decision_required}`. Ví dụ: `{"business_confirmed": 2, "business_corrections": 1, "backend_objections": 0, ...}`. Value LUÔN là integer — `_clean_count_dict` strip mọi entry không phải `str→int`, cap 32 entries (16 đã dùng, còn dư). Ghi state này → collector tự động derive event `inline_review_counts` khi state file đổi (không phụ thuộc tool nào ghi — D6) (KHÔNG cần marker/block riêng, KHÔNG cần collector đổi).

### 4. Debate thread capture (/avatar:debate mode = plan_bundle)

**Áp dụng CHỈ khi `/avatar:debate` chạy trên plan-bundle (`--plan` trên plan dir).** Single-file debate (không có plan-monitor trace) → BỎ QUA toàn bộ mục này (không marker, không block, không verdict event). Capture qua **Task return-block + projection-state Write** — KHÔNG Bash (script `.py` chạy bằng `python3`, không thuộc allowlist read-only).

**4a. Trace recovery (B-A) — debate join vào trace của plan, KHÔNG mint mới.**

- Ở Bước 0 (guard còn OFF → Bash được phép), sau khi resolve `plan_dir` + `root`: tìm projection-state file trong `<root>/.claude/state/planning-council/*.json` có `plan_path` khớp `plan_dir` (relative-path so khớp). Match → dùng `trace_id` đó (full UUID). Không match / thư mục rỗng → plan-monitor OFF cho plan này → BỎ QUA capture (fail-open, debate chạy bình thường). KHÔNG mint trace_id mới (tránh orphan trace tách rời plan).
- Recovery đọc file read-only; KHÔNG ghi vào projection-state file cho tới bước verdict (4d).

**4b. Marker (spawn Skeptic/Refiner) — PreToolUse Task `description`.**

- Skeptic (Bước 2a/2e): `[PM:<trace-id>:debate:debate-skeptic:01:none:<round>]` — `<round>` = round debate THẬT (không phải `0`).
- Refiner (Bước 2g): `[PM:<trace-id>:debate:debate-refiner:01:none:<round>]`.
- `<stage>` = literal `debate`. `<instance>` = `01` (1 skeptic + 1 refiner mỗi round). Marker chỉ inject khi có `trace_id` (full UUID) từ 4a; không có → không marker.

**4c. Return block (cuối return của debate-skeptic / debate-refiner).**

- Skeptic: đầu return `ROUND_STARTED` (mở round), cuối return `FINDINGS`:
  `<avatar-plan-monitor-event>{"kind":"FINDINGS","trace_id":"<full-uuid>","role":"debate-skeptic","round":"<N>","counts":{"blocking":<int>,"decisions":<int>,"nit":<int>},"finding_ids":["B1","D1","N1"],"findings":[{"id":"B1","text":"total_count double-count khi retry POST — vi phạm AC4/NFR3","artifact_path":"phase-02.md:§Success Criteria"}]}</avatar-plan-monitor-event>`
- Refiner: cuối return `REFINED` (fixed/reopened/new counts):
  `<avatar-plan-monitor-event>{"kind":"REFINED","trace_id":"<full-uuid>","role":"debate-refiner","round":"<N>","counts":{"fixed":<int>,"reopened":<int>,"new":<int>},"finding_ids":["B1","B2"],"findings":[{"id":"B1","text":"FIXED: gate RPC trên events-insert-mới (.select() sau upsert)"}]}</avatar-plan-monitor-event>`
- `finding_ids` = CHỈ opaque id (B1/D2/N1). TUYỆT ĐỐI KHÔNG `section`/`artifact_path`/`issue` text (AC6 — collector strip defensive, nhưng agent phải tự KHÔNG gửi). `reply_to`/`contribution_id` (opaque) tùy chọn để nối thread. `trace_id` = full UUID recover ở 4a; không có trace → KHÔNG emit block.
- `findings` = list ≤20 dict `{id: short-id [A-Za-z0-9_.\-] ≤64 ký tự, text: str ≤2000 ký tự, artifact_path: str ≤200 ký tự (optional)}` — mang NỘI DUNG có cấu trúc, khác `finding_ids` (opaque). `text` = phân tích agent-written (issue/decision-rationale/nit note); guard KHÔNG sanitize nội dung, CHỈ check shape + cap length (hygiene strip control/bidi riêng, xem plan §D2). Text > 2000 ký tự → guard TRUNCATE `text[:1999]+"…"` (giữ item, KHÔNG drop). User chấp nhận rủi ro secret lộ trong text (quyết định 2, KHÔNG có bước sanitize/redact nội dung hiển thị).

**4d. Verdict event — projection-state Write (Bước 2f, SAU khi tắt session).**

- **Thứ tự bắt buộc (guard-safe):** projection-state file (`planning-council/<trace_id>.json`) KHÔNG nằm trong debate allowlist `{writable ∪ sidecar}` → ghi vào nó khi guard active sẽ bị DENY. Vì vậy verdict-state phải ghi **SAU** khi Bước 2f đã (1) ghi managed-block verdict vào plan.md [in allowlist] và (2) set `active=false` vào debate state-file [exempt]. Khi `active=false`, guard pass-through mọi tool → Write projection-state được phép. Trình tự: **managed-block → `active=false` → Write projection verdict-state**.
- Nội dung ghi: `write_state(root, trace_id, {"verdict": <V>, "round": <N>, "stage": "debate"})` với `trace_id` từ 4a. `<V>` = terminal verdict THẬT (Bước 2f): `APPROVE` / `NEEDS_DECISION` / `ESCALATE`. Command CHỈ ghi khi đạt terminal → **KHÔNG BAO GIỜ** ghi `APPROVE` cho debate dang dở. Collector derive event `verdict` khi state file đổi, không phụ thuộc tool nào ghi (D6) — `build_state_payloads` đọc `state.verdict`.
- **`interrupted` (R5)** = giá trị phía DASHBOARD (P06) suy khi trace debate treo không terminal — command KHÔNG ghi. `_ALLOWED_FIELDS`+guard giữ `interrupted` hợp lệ để P06 map được; nhưng nguồn duy nhất command ghi là 3 terminal verdict trên. Debate crash giữa chừng → không có verdict event → dashboard thấy ongoing (fail-open, KHÔNG tự APPROVE).
- `NEEDS_DECISION` → dashboard suy `plan_user_gate` amber (chờ user). `verdict` là enum ≤64 ký tự — KHÔNG kèm decisions text/plan content.
- **Fail-open:** nếu 4a không recover được trace (plan-monitor off) → BỎ QUA hoàn toàn 4d, KHÔNG ghi gì. Nếu Write projection-state lỗi → nuốt, verdict managed-block trên plan.md vẫn đúng (capture là best-effort, KHÔNG chặn debate — AC12).
