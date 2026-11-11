# Autopilot — startbuild v2: triage + phỏng vấn TRƯỚC BLUEPRINT (nhánh A0 / B)

> Dùng bởi `commands/avatar/startbuild.md` Bước 0 (triage), nhánh A0 (chưa có blueprint) và
> nhánh B (việc trên hệ có sẵn). Nguồn: spec startbuild v2 (plan 20260927-1137) §3–§6.
> Khác `clarify-questions.md`: file này hỏi **trước** khi có BLUEPRINT (đầu vào = ý tưởng/task);
> clarify hỏi **sau** khi có draft (6 nhóm, chỉ hỏi điều draft chưa trả lời).

## Luật lô (kế thừa clarify)

- ≤ 10 câu/lô, ≤ 2 lượt; mỗi câu có **default + hệ quả nếu dùng default**; `id` ổn định giữa các lượt.
- `required: true` **chỉ** cho câu thật sự chặn (thiếu ⇒ không viết được BLUEPRINT hợp lệ, hoặc init
  từ chối G0). Câu "biết thì tốt" ⇒ `required: false`: dùng default, ghi "default được ủy nhiệm".
- Hình dạng câu theo `interview.schema.json` (xem `clarify-questions.md` "Hình dạng câu hỏi").
  Không đặt id nào có tiền tố `<ticket-id>-needs-decision` — đó là không gian id của controller
  (câu tự đẻ `<ticket-id>-needs-decision-<8 hex>`, id theo nội dung).
- Câu required chưa có đáp án sau 2 lượt ⇒ **dừng chờ người**, không đoán cho đủ.
- Câu còn treo khi đi qua init: đóng gói vào init request (bước 6) — initializer ghi
  `.avatar/interview.json`; startbuild **không** tự ghi worktree.

## Bước 0 — Triage

| id | Câu | type | required | default | hệ quả nếu dùng default |
|---|---|---|---|---|---|
| `q-mode` | Bạn đang **(A)** xây hệ thống mới hay **(B)** làm việc trên hệ có sẵn? | single: A / B | ✓ | suy từ repo: HEAD rỗng hoặc chưa có `.avatar/BLUEPRINT.md` ở HEAD ⇒ A, ngược lại B — người **xác nhận**, không im lặng | chọn sai nhánh ⇒ phỏng vấn thừa, hoặc thiếu BLUEPRINT để G0 |
| `q-repo` | (chỉ khi workspace nhiều repo và thiếu `--repo`) Repo nào? | single: `src/<repo>` | ✓ | — | không đoán repo gần nhất |

Có truyền `<blueprint.html|md>` ⇒ bỏ Bước 0, vào nhánh A1 (7 bước ở `startbuild.md`).

## Nhánh A0 — chưa có blueprint: lô 1

| id | Câu | type | required | default | hệ quả nếu dùng default |
|---|---|---|---|---|---|
| `a1-problem` | Vấn đề gì, ai đang gặp, workaround hiện tại? | text | ✓ | — | — |
| `a2-outcome` | Xong thì **quan sát được gì** (hành vi, không phải "code chạy")? → acceptance | text | ✓ | — | — |
| `a3-user` | Người dùng chính + 1 kịch bản chính | text | ✓ | — | — |
| `a4-nongoal` | ≥ 1 điều **KHÔNG** làm đợt này | text | ✓ | — | init từ chối G0 nếu "Ngoài phạm vi" rỗng |
| `a5-sensitive` | Có hành động phá hoại, dữ liệu cá nhân hoặc compliance cần xác nhận thêm? | single: không / có (liệt kê) | ✗ | không | áp policy an toàn nghiêm nhất của repo; quyết định chạm phần này luôn hỏi người |
| `a6-stack` | Ràng buộc tech stack? | single: theo đề nghị của agent / bắt buộc dùng X | ✗ | theo đề nghị | agent đề nghị, người xem lại ở G0 |
| `a7-deploy` | Deploy target? (**hỏi ngay lô 1**, không để cuối) | single: local-only / qa / staging / production | ✓ | local-only | — |
| `a8-resources` | Tài nguyên **ngoài repo** được đụng (`<loại>:<định danh>`) → `resource_names` | text | ✗ | `[]` | G2 cần duyệt (người hoặc Claude ủy nhiệm) thay vì tự waive |
| `a9-nfr-cost` | Ràng buộc hiệu năng / uptime / ngân sách | text | ✗ | `limits.*` mặc định của config | không tự đặt số mới |
| `a10-approver` | Ai duyệt G0–G3, kênh Mattermost cho mission thật | text | ✓ | — | channel thử `test-avatar-po` KHÔNG dùng cho mission thật |

Sau lô 1, agent **tự làm, không hỏi**:
1. Đề nghị tech stack (khi `a6-stack` = theo đề nghị): ≤ 5 dòng, lý do gắn với a1–a3 → mục
   `## Tech stack đề nghị` của BLUEPRINT.
2. Đề xuất chia milestone: **1 mission = 1 milestone**, mục tiêu ≤ `g2_ticket_threshold` (default 15)
   ticket hiệu lực; milestone 1 = lát dọc mỏng end-to-end + lát integration; milestone sau = chạy lại
   startbuild nhánh B với BLUEPRINT revision mới → mục `## Milestone`.
3. Điền BLUEPRINT draft theo `templates/autopilot/BLUEPRINT.tpl.md` (đủ Tech stack đề nghị, Deploy
   target, Milestone; mục Vận hành ghi yêu cầu lát integration cuối).
4. Lô 2 (mục dưới).

## Nhánh A0 — lô 2

Lô 2 = Clarify 6 nhóm (`clarify-questions.md`) **chỉ** với điều draft chưa trả lời, **cộng** câu ủy
nhiệm dưới (vẫn ≤ 10 câu/lô). Nhánh A1 (bước 3), B và A1-lite: hỏi `a11-decision-policy` cùng lô
Clarify — mọi nhánh mà startbuild viết/sửa BLUEPRINT draft.

| id | Câu | type | required | default | hệ quả nếu dùng default |
|---|---|---|---|---|---|
| `a11-decision-policy` | Khi worker cần chọn giữa các phương án **trong** ranh giới tự xử (mục dưới), autopilot được **tự áp khuyến nghị** (`auto`: trần mặc định 3 lần/mission, ghi sổ `status --decisions`, đảo bằng `@avatar redirect`) hay **luôn hỏi bạn** (`ask`)? | single: auto / ask | ✗ | ask | mỗi `needs_decision` dừng mission chờ `@avatar answer` |

Luật ủy nhiệm (spec V2 §4.1 V2-1p):
- **luôn** hỏi (cờ `decision_policy` bắt buộc ở probe bước 1 của `startbuild.md`) — kể cả khi lô 2
  không còn câu clarify nào khác.
- Chỉ ghi `decision_policy: auto` khi người trả lời **tường minh** `a11-decision-policy` = `auto`.
  Im lặng, bỏ qua, trả lời mơ hồ ("tuỳ", "ok", "theo khuyến nghị") ⇒ `ask`. Cấm suy ra `auto` từ câu
  khác (`b3-touch`, mức tin tưởng chung, "cứ làm tiếp"…).
- Ghi đúng dòng máy đọc trong `## Quyền ủy nhiệm G0` — cách ghi ở `startbuild.md` bước 4. Ghi chú
  ủy nhiệm trong mục đó không trích id `a11-decision-policy` hay tên khoá (CLI hạ về `ask`); tự kiểm
  bằng Grep: mục đó có đúng 1 dòng khớp `decision[_-]policy`.

## Nhánh B — việc trên hệ có sẵn

**B1 Kiểm cấu hình** (agent chạy/hướng dẫn, không hỏi): `avatar autopilot doctor`; kiểm
`.avatar/BLUEPRINT.md` có ở HEAD. Không có ⇒ **A1-lite**: draft BLUEPRINT tối thiểu cho hệ hiện có
(Tầm nhìn, Trong/Ngoài phạm vi với ≥ 1 non-goal thật, Deploy target); người commit + duyệt G0.

**B2 Câu hỏi:**

| id | Câu | type | required | default |
|---|---|---|---|---|
| `b1-task` | Task là gì (kết quả quan sát được)? | text | ✓ | — |
| `b2-size` | Độ lớn: nhỏ (≤ 3 ticket) / vừa / lớn — agent ước lượng, người xác nhận | single | ✓ | ước lượng của agent |
| `b3-touch` | Có chạm scope ngoài BLUEPRINT / tiền / secret / deploy không? | single: không / có | ✓ | không (khi agent không thấy dấu hiệu) |

**B3 Đường đi:** `b2-size = nhỏ` **và** `b3-touch = không` ⇒ gợi ý làm interactive
(`/avatar:implement` hoặc sửa trực tiếp), **không tạo mission** — in lý do + lệnh gợi ý rồi dừng.
Ngược lại ⇒ mission như nhánh A1; task là đầu vào cho plan; G2 theo "Chính sách G2" của BLUEPRINT.

**B4 Điểm cân nhắc lúc mission chạy:** worker trả `needs_decision` ⇒ controller đẻ câu
`<ticket-id>-needs-decision-<8 hex>` (required, id theo nội dung). BLUEPRINT đã duyệt G0 khai
`decision_policy: auto` + lựa chọn khuyến nghị trong ranh giới ⇒ controller tự áp, ghi sổ
(`status --decisions`); còn lại mission **dừng chờ `@avatar answer`** với nguyên id đó.

## Ranh giới "tự xử" — áp khuyến nghị debate mà không hỏi (A0/A1/B)

Tự áp khi **đủ cả 3**:
1. **Đảo ngược được**: sửa text BLUEPRINT/PLAN **trước** G0/G2; chọn giữa các phương án kỹ thuật
   không đổi hành vi sản phẩm.
2. Nằm trong "Trong phạm vi" và **không** đổi "Ngoài phạm vi".
3. **Không chạm**: `resource_names`, tiền/ngân sách, secret, deploy target, `base_ref`, người duyệt,
   dữ liệu cá nhân/compliance (debate nêu quyết định chạm phần này ⇒ **ngoài** ranh giới ⇒ required).

Mỗi lần áp ⇒ ghi "default được ủy nhiệm" vào Quyền ủy nhiệm G0 / Sổ quyết định (không ghi "Luke
chọn"). Không đủ ⇒ câu hỏi required `d-<slug>` trong lô 2, chờ người. Sau G0 mọi sửa bytes
BLUEPRINT ⇒ G0 tự huỷ ⇒ debate + áp khuyến nghị phải xong **trước** khi người commit file để duyệt.

## Checklist tài nguyên theo stack (bước 5 của `startbuild.md`)

Kiểm **tồn tại**, không lưu/in giá trị. Nguồn: Tech stack đề nghị + Deploy target + `a8-resources`.
Cột env key (cờ `secrets_mount` bắt buộc): key thử ghi "nạp `test.env` sau init (`doctor` kiểm)", key
release ghi "stdin lúc G3" — không tính là thiếu, và **không** bảo export credential production vào
shell.

| Stack / tài nguyên | Tool (`command -v`) | Env key (nguồn theo `secrets_mount`) | Probe read-only |
|---|---|---|---|
| Node/TS | node, npm/pnpm | `NPM_TOKEN` (registry riêng) | `npm whoami` |
| Python | python3, pip/uv | — | `python3 --version` |
| Postgres/Supabase | psql, supabase | `DATABASE_URL`, `SUPABASE_*` | `psql -c 'select 1'` / `supabase projects list` |
| Git remote | git | PAT qua credential helper | `git ls-remote origin` |
| Mattermost | — | — (không qua env, xem câu dưới) | `avatar autopilot doctor` |
| Deploy (theo `a7-deploy`) | tool của target | key của target | `--dry-run` nếu có |

Sự thật CLI phải nói rõ với người: worker `claude` chỉ nhận env allowlist hệ thống + `AVATAR_*`
(**không nhận secret dự án**); recipe verify/deploy nhận env qua `env_allowlist`; worktree mission
bị `git clean -fd` khi recover ⇒ **không** đặt file secret untracked trong worktree. Nguồn giá trị
(spec V2 §4.2):
- Credential **thử** ⇒ `~/.avatar/secrets/<mission_id>/test.env` (tạo sau
  `init` khi đã có mission id; thư mục 0700, file 0600, `KEY=VALUE`, không `export`; `avatar autopilot
  doctor` kiểm quyền + tên key thiếu; cấm key `ANTHROPIC_*` — doctor FAIL, `run` chặn; giá trị < 8 ký tự
  không được che theo giá trị); còn credential production **không** ghi vào file nào, kể cả `test.env`
  (worker cùng OS user đọc được): tới G3 thì pipe vào `avatar autopilot run --mission <id>
  --release-secrets-stdin` (stdin phải là pipe, chỉ giữ trong bộ nhớ, chỉ recipe release sau G3 nhận).

Mattermost: CLI đọc `<workspace>/.mattermost/credentials.json` (tạo bằng `avatar comm-connect
--comm-channel <kênh> --comm-bot-token-stdin`, token vào Keychain) + `approvers[]` trong
`~/.avatar/autopilot-config.json`; không đọc biến môi trường MATTERMOST nào. Thiếu ⇒ mục "Checklist thiếu quyền" của resource-request → G1.

## Output của file này

- BLUEPRINT draft (staging) đủ template, "Ngoài phạm vi" ≥ 1 mục thật, 3 mục mới đã điền.
- Câu chưa trả lời ⇒ "Quyết định mở" của BLUEPRINT hoặc resource-request, kèm default + hệ quả.
- Nhánh B task nhỏ ⇒ **không** mission, chỉ gợi ý lệnh interactive.
