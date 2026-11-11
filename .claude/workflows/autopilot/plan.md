# Autopilot — Plan playbook

> Dùng bởi adapter `plan-v1`: CLI nạp file này theo kind ticket (`plan`). Nguồn: dogfood V2.1 lần 4, F-24/F-26/F-27. Khuôn lát + DAG: `templates/autopilot/PLAN.tpl.md`.

## Result của ticket plan

- Ticket plan có `allowed_paths: []` ⇒ `changed_files: []`. Không sửa file repo nào ⇒ luôn `[]`; bản nháp trong staging `.avatar/attempt-output/<run_id>/` chỉ liệt kê trong `summary`.
- CẤM điền giá trị giả cho mảng không có gì để khai (`"/dev/null"`, `"none"`, `"-"`): schema chặn đường dẫn tuyệt đối ⇒ attempt bị từ chối.
- Ticket mới CHỈ qua `proposed_changes` op `create` (`content` theo `proposed-change-content.schema.json`, không có `id`); `proposed_tickets` luôn `[]` — khác rỗng ⇒ done bị từ chối, tính **một lần thất bại** (`counted_failures` + 1): ticket về `todo`, attempt kế nhận lý do ở mục "Lần trước bị từ chối vì"; hết `max_counted_failures` ⇒ `blocked`.
- Ticket tạo mới chỉ dùng executor mà adapter của nó dispatch được: `executor: "claude"`, kind + `command_adapter` là một cặp trong `decision → decision-v1`, `fix → fix-v1`, `implement → implement-v1`, `review → review-clean-v1`, `review → review-local-v1`, `review → review-remote-v1`, `test → test-v1`, `test → testaudit-v1`, `testcase → testcase-v1`. CẤM `executor: "controller"` (vd `test-v1` không có executor controller), kind `deploy`/`revert`, adapter `deploy-v1`/`revert-v1` (v1 không có đường dispatch) và kind `survey`/`plan` (chỉ controller tạo): cả lô `proposed_changes` bị từ chối (`proposal_apply_rejected`, tính một lần thất bại, F-73; tạo survey/plan ⇒ dừng chờ người). Deploy đi qua release flow (G3), không phải ticket.
- `.avatar/PLAN.md` do controller sinh từ ticket JSON sau khi áp `proposed_changes` (mục lục DAG theo `slice_id`) — worker không ghi file này.

## Acceptance của ticket testcase / implement / test

- Mỗi ticket `testcase`/`implement`/`test` phải có `acceptance[]` ≥ 1 dòng theo hành vi (`{"text": "<hành vi>", "done": false}`, `text` không rỗng). Thiếu/rỗng ⇒ controller từ chối result (`feature_ticket_without_acceptance`), tốn thêm một attempt.
- Ticket testcase của lát đầu có ca hành vi chính: ví dụ đầu tiên trong BLUEPRINT `## Hành vi` (đầu vào điển hình ⇒ đầu ra cụ thể), không chỉ ca biên.
- Ticket chạm file nhạy cảm (config test: `conftest.py`, `pytest.ini`, `setup.cfg`, `pyproject.toml`, `tox.ini`, `package.json`, `vitest.config.*`, `jest.config.*`, `.npmrc`, `Makefile`; CI/hook: `.gitlab-ci.yml`, `.gitlab/`, `.github/`, `.husky/`, `.pre-commit-config.yaml`) phải nêu tên file (basename) trong một dòng `acceptance[].text` của chính ticket đó, nếu không verifier từ chối result (`sensitive_path_modified`), tốn thêm một attempt.

## Quyết định mở của BLUEPRINT

- Ticket chạm một mục trong `## Quyết định mở` ⇒ acceptance đúng dạng "gặp quyết định <X> ⇒ trả `needs_decision` (options + `recommended_option_id`)" — chỉ controller áp ủy nhiệm G0.
- CẤM ghi "tự quyết theo G0" / "theo `decision_policy`" vào acceptance (controller escalate plan đó); acceptance không nhắc G0, kể cả để phủ định.
- Mỗi mục mở là một quyết định riêng: một dòng acceptance cho mỗi mục, không gộp hai mục vào một dòng.
- `allowed_paths` phủ **mọi** phương án đang mở (liệt kê đủ file của từng phương án hoặc một glob hẹp) — không chốt một phương án qua `allowed_paths`.

## Ticket ngoài chuỗi TDD (F-48)

- Implement/fix không đi kèm testcase (docs, config, gỡ injection) ⇒ đặt **cùng lát** với cặp TDD và cho testcase đầu của lát `depends_on` nó: ticket chạy trên suite xanh trước khi testcase mở test RED. **Không** tách ra lát riêng (lát chỉ có implement ⇒ G2 cảnh báo thiếu testcase/test/integration).
- ≥ 2 cặp trong một lát ⇒ testcase B `depends_on` implement A (testcase A → implement A → testcase B → implement B).
- Implement luôn `depends_on` testcase của nó: scheduler chỉ giữ thứ tự RED→GREEN qua cạnh này; thiếu cạnh ⇒ ticket khác có thể chạy khi suite đang đỏ ⇒ verify từ chối (`verification_recipe_exit_nonzero`).
- Ticket `test` luôn `depends_on` implement (đứng sau implement), không nằm giữa testcase và implement: test chạy khi suite đang đỏ thì fail, scheduler không xếp nó vào cửa sổ RED ⇒ `run` dừng với `red_window_conflict`.
