# Git Flow — workspace đa repo (NAL)

> Hook cưỡng chế = tool `git-flow` (bật/tắt độc lập qua `avatar tools enable/disable
> git-flow`). Doc này vẫn là luật kể cả khi tool tắt — hook chỉ là lớp cưỡng chế, không
> phải nguồn sự thật.

Áp dụng cho mọi repo trong `src/<repo>` của workspace đa repo (4 repo hiện tại:
`avatar-cli`, `telemetry`, `avatar-supabase`, `team-ai-pack` — xem `.claude/repos.json`).

## TL;DR

| Hành vi | Được / Không |
|---|---|
| Commit thẳng vào `main`/`master` | ⛔ Không — tạo nhánh trước |
| Push nhánh feature lên remote | ✅ Được |
| Push (kể cả refspec `HEAD:main`) tới `main`/`master` | ⛔ Không — phải qua PR/MR |
| Tạo nhánh đúng prefix ở bảng §3 | ✅ Được |
| Tạo nhánh sai prefix, hoặc trùng tên `main`/`master` | ⛔ Không |
| `git merge`/`rebase`/`revert`/`cherry-pick` ở LOCAL | ✅ Được (không gate — xem §10) |

## 1. Mô hình lai: GitHub Flow làm nền

Nền là **GitHub Flow**: nhánh ngắn cắt từ `main`, commit, push, mở PR, review, merge,
xoá. KHÔNG có nhánh tích hợp dài hạn kiểu `develop` của Git Flow đầy đủ. Phần "lai"
chỉ nằm ở **profile repo** (§4): repo có bản phát hành rời rạc (`versioned`) được
thêm prefix `release/*`, repo deploy liên tục (`continuous`) thì không cần.

## 2. Nhánh protected

`main` và `master` đều là protected. Đo thật hôm nay: cả 4 repo đều dùng `main`,
**không repo nào dùng `master`** — luật vẫn phủ `master` để an toàn khi thêm repo mới.

Trên nhánh protected: KHÔNG commit thẳng, KHÔNG push thẳng (kể cả refspec ẩn như
`HEAD:main`, `:main`, `--all`, `--mirror`), KHÔNG tạo nhánh mới trùng tên.

## 3. Đặt tên nhánh

Định dạng: `<prefix>/<ticket-hoặc-slug>`.

| Prefix | Dùng khi | Profile | Ví dụ thật |
|---|---|---|---|
| `feat/` | Tính năng mới | cả 2 | `feat/plan-monitor-findings-content` |
| `fix/` | Sửa lỗi | cả 2 | `fix/116-dashboard-idor-membership-guard` |
| `chore/` | Việc lặt vặt, không đổi hành vi | cả 2 | `chore/sync-docs-pack-v1.1.29` |
| `docs/` | Chỉ đổi tài liệu | cả 2 | `docs/119-doc-drift-cleanup` |
| `test/` | Chỉ thêm/sửa test | cả 2 | — |
| `refactor/` | Tái cấu trúc, không đổi hành vi | cả 2 | — |
| `perf/` | Tối ưu hiệu năng | cả 2 | — |
| `ci/` | Đổi pipeline CI/CD | cả 2 | — |
| `hotfix/` | Vá khẩn — **DOC-ONLY**, xem §5 | cả 2 | — (chưa từng dùng thật) |
| `release/` | Cắt bản phát hành | chỉ `versioned` | `release/v1.1.27` |

**SemVer bắt buộc cho `release/` dưới profile `versioned`** (GF-D05, chốt
vòng 2 — CHỈ `release/`, KHÔNG `hotfix/`, xem §5): định dạng
`release/v?X.Y.Z(-suffix.N)?` — `v` TUỲ CHỌN (`release/v1.1.27` và
`release/1.1.27` đều hợp lệ), hậu tố bản thử `-beta.N` (vd
`release/v1.1.27-beta.3`, pack dùng thật). `release/next` hay `release/1.2`
(thiếu patch) bị DENY `branch-name-prefix` dưới `versioned`. Profile
`continuous` KHÔNG áp SemVer — giữ prefix-match lỏng như cũ. Lý do loại
`hotfix/` khỏi gate: hotfix thường CHƯA biết số bản lúc tạo nhánh (vá khẩn),
deny oan lần đầu dùng đúng kịch bản khiến dev tắt hẳn tool.

Prefix bot (allowlist riêng, **miễn kiểm hoàn toàn** — không cần khớp prefix người):
`dependabot/`, `renovate/`. Ví dụ thật:
`origin/dependabot/github_actions/github-actions-1b2f1b9c29`.

## 4. Profile repo: continuous vs versioned

| Repo | Profile | Vì sao |
|---|---|---|
| `telemetry` | `continuous` | Push `main` → GitLab CI tự động deploy prod — không có bản phát hành tách rời |
| `avatar-supabase` | `continuous` | `supabase functions deploy` thủ công, không gắn version artifact, không dùng `release/*` |
| `avatar-cli` | `versioned` | Publish npm có version (`chore(release): 3.19.1`) — có bản phát hành rời rạc |
| `team-ai-pack` | `versioned` | Build tarball + upload Supabase thủ công qua `release/*` |
| Repo lạ (chưa liệt kê) | `versioned` (mặc định) | Nới nhất — fail-open: thừa `release/*` vô hại, thiếu thì chặn oan |

Khác biệt duy nhất: `versioned` có thêm prefix `release/` trong allowlist §3
(cộng SemVer bắt buộc CHỈ cho `release/`, xem §3); `continuous` thì không.

### 4b. Per-repo override 2 luật DENY (quyết định #124)

`denyDirectCommitOnProtected`/`denyPushToProtected` — 2 khoá ĐỘC LẬP, mặc
định `true` cả hai (y hệt hành vi cũ). `telemetry` mở riêng
`denyPushToProtected: false` vì push `main` → GitLab CI **tự động deploy
prod** (§Deploy `avatar-workspace`) — không có bước PR/MR tách rời để chặn ở
đó; tai nạn đắt nhất với repo này là **commit sinh ra thẳng trên `main`**,
không phải cú push sau khi đã merge, nên `denyDirectCommitOnProtected` GIỮ
`true`. Cấu hình tại `.claude/state/git-flow-config.json`:

```json
{ "repoOverrides": { "telemetry": { "denyDirectCommitOnProtected": true, "denyPushToProtected": false } } }
```

## 5. `hotfix/*` (DOC-ONLY — hook không có luật riêng)

`hotfix/` nằm trong allowlist prefix chung ở §3 (cả 2 profile dùng được, KHÔNG
SemVer-gated ở profile nào — chốt vòng 2, xem §3) nhưng **[DOC-ONLY]**: hook
không có luật riêng nào phân biệt "vá khẩn cấp" với `fix/` thông thường
(không ép xuất phát từ tag, không rút ngắn review, không rule cưỡng chế nào
đọc Ý NGHĨA prefix này khác đi).

Lý do: đo thật trên cả 4 repo, **chưa nhánh nào từng dùng `hotfix/`**. Viết luật
cưỡng chế riêng cho một prefix chưa ai dùng vi phạm YAGNI — giữ prefix sẵn trong
allowlist để không chặn oan nếu sau này có người dùng, nhưng không code thêm rule.

## 6. Commit message

Định dạng conventional: `type(scope)?: mô tả ngắn` (scope tuỳ chọn). Type hợp lệ:
`feat fix chore docs test refactor perf build ci style revert`

WARN (không chặn) khi commit KHÔNG khớp định dạng trên, **TRỪ** các ca sau (miễn
hoàn toàn, không WARN):

- `Merge branch…`
- `Merge pull request…`
- `Merge remote-tracking…`
- `Revert "…`
- `fixup!…`
- `squash!…`
- Mọi commit có **≥2 parent** (merge commit nói chung)

Lý do đo được: `telemetry` lệch conventional **27/100** commit gần nhất, phần lớn là
`Merge branch 'x' into 'main'` do GitLab MR tự sinh. Không miễn thì WARN bắn liên
tục trên commit dev không tự sửa được → nhiễu → dev học phản xạ phớt lờ MỌI WARN,
kể cả WARN nhánh cũ ở §7.

WARN bắn ở `PostToolUse`, chỉ trong **cửa sổ tươi** kể từ lúc commit — mặc định
**120 giây**, chỉnh qua khoá `commitWarnFreshnessSeconds` trong
`.claude/state/git-flow-config.json` (xem §9). Ngoài cửa sổ này hook coi là "đã qua"
và không nhắc lại.

## 7. Vòng đời nhánh

1. **Tạo** nhánh mới từ `main`/`master` mới nhất, đặt tên theo §3:
   `git -C <repo> checkout -b <prefix>/<ticket>-<slug>`
2. **Commit** theo §6.
3. **Push** nhánh (KHÔNG push thẳng `main`/`master` — §2, §8).
4. **Mở PR/MR**, review, merge (squash hoặc merge commit tuỳ repo).
5. **Xoá** nhánh — cả local lẫn remote — ngay sau khi merge.

Nhánh **sống quá 14 ngày** kể từ commit cuối (loại nhánh đã merge) bị WARN ở
`SessionStart`, tối đa **5 dòng** mỗi phiên. Thông điệp luôn là **"merge hoặc xoá"**,
không chỉ "merge" — vì `--merged` KHÔNG nhận ra nhánh đã **squash-merge** (xem
known-gap §10): 2/3 nhánh lấy mẫu ở `team-ai-pack` đã có subject nằm trong
`git log main` nhưng vẫn bị `git branch --no-merged main` báo dương giả.

## 8. Bị hook chặn thì làm gì

DENY chặn ở `PreToolUse` (lệnh không chạy). WARN chỉ cảnh báo — ở `PostToolUse`
(sau khi lệnh đã chạy) và `SessionStart` (đầu phiên); WARN KHÔNG có kênh chặn ở
`PreToolUse`.

| Hook báo | Rule | Nguyên nhân | Sửa |
|---|---|---|---|
| `[git-flow] ⛔ commit thẳng vào nhánh protected` | `commit-on-protected` | Đang đứng trên `main`/`master` mà chạy `git commit` | `git -C <repo> checkout -b fix/<ticket>-<slug>` rồi commit lại |
| `[git-flow] ⛔ push vào nhánh protected` | `push-to-protected` | Refspec đích là `main`/`master` (kể cả `HEAD:main`, `:main`) | Push nhánh feature, mở PR/MR |
| `[git-flow] ⛔ tên nhánh trùng nhánh protected` | `branch-name-protected` | `git checkout -b main` / `git branch master` — tạo nhánh TRÙNG TÊN nhánh protected | Chọn tên khác theo bảng §3 — nhánh protected đã tồn tại, không tạo lại |
| `[git-flow] ⛔ tên nhánh sai prefix` | `branch-name-prefix` | Tên nhánh thiếu prefix hợp lệ ở §3 | Đổi tên theo bảng §3 |

⚠ Hai dòng cuối là hai lỗi **khác bản chất** (trùng tên nhánh protected vs
sai prefix) — không nhầm lẫn: gộp lại thì message không nói được user sai chỗ
nào. Lệnh gộp nhiều repo (#137): mỗi action git được gắn repo/branch RIÊNG
theo CWD hiệu lực + hint (`-C`/`GIT_DIR`) tại segment chứa nó — lệnh đa repo
KHÔNG còn bị chặn loạt, chỉ action chạm nhánh protected mới bị DENY.

## 9. Escape hatch + giới hạn

Hai đường thoát khi bị chặn oan:

**(a) `GIT_FLOW_OVERRIDE=1`** — export **TRƯỚC khi mở Claude Code**:

```
export GIT_FLOW_OVERRIDE=1
```

⚠ Giới hạn: hook chạy trong **tiến trình riêng**, đọc env của tiến trình đó — prefix
inline (`GIT_FLOW_OVERRIDE=1 git push`) **KHÔNG có tác dụng** (cùng cơ chế
`PRGATE_OVERRIDE` của `pull-request-checker`, xem
`tools/pull-request-checker/hooks/pretooluse-pr-review-gate-hook.py:25-27`).

**(b) `"enforce": false`** trong `.claude/state/git-flow-config.json` — hook đọc
config **mỗi lần chạy** nên hiệu lực **NGAY giữa phiên**, không cần restart. Đây là
trạng thái **TẠM THỜI**: bật lại gate bằng cách xoá khoá `enforce` hoặc đặt lại `true`.

Cả hai: mỗi lần bypass **trúng luật DENY** đều ghi vào
`.claude/state/git-flow-bypass.log`. WARN bị bypass **KHÔNG ghi log** (tránh rác).

**Trạng thái TẮT có tín hiệu đầu phiên** — khi bypass đang bật, `SessionStart` in
ĐÚNG 1 dòng (chỉ ở `startup`/`resume`, KHÔNG ở `clear`/`compact`/`fork`):

```
[git-flow] ⚠ gate đang TẮT (enforce:false | GIT_FLOW_OVERRIDE) — bật lại: xoá khoá enforce
```

`PostToolUse` (WARN conventional) vẫn im hoàn toàn khi gate tắt. Dòng trên là
**trạng thái**, không phải lỗi. Lý do cần dòng này: `enforce:false` nằm trong
`.claude/state/` nên sống qua **mọi `avatar sync`** — bật lúc bị chặn oan rồi quên
là mất cả DENY lẫn 2 kênh WARN vô thời hạn, không dấu hiệu nào báo lại.

**Khoá cấu hình khác**: `commitWarnFreshnessSeconds` (mặc định `120`) trong cùng
file `.claude/state/git-flow-config.json` — chỉnh cửa sổ "commit vừa xảy ra" của
WARN conventional (§6).

⚠ **Cảnh báo**: đặt `GIT_FLOW_OVERRIDE=1` trong khối `env` của `settings.json` = tắt
gate cho **MỌI phiên** trên máy đó, không phải một lần — đừng bật rồi quên. Không có
cách nào né hook ngoài 2 đường thoát chính thức ở trên.

## 10. Known-gap: hook KHÔNG bắt được gì

**Được biện minh (cố ý không gate)**: `git merge`, `git rebase`, `git revert`,
`git cherry-pick` sinh commit trên `main` **ở LOCAL**; `git branch -m <cũ> main`.
Lý do: **push là điểm thắt duy nhất** — DENY đã chặn MỌI push tới protected (kể cả
refspec `HEAD:main`, `:main`, `--all`/`--mirror`) nên commit local không bao giờ ra
được remote; merge buộc phải qua PR/MR. Thêm luật ở đây chỉ tăng bề mặt chặn oan mà
không ngăn được gì thêm.

**Kỹ thuật (không đóng được bằng phân tích văn bản)**: alias
(`alias gp='git push'; gp`), subshell (`$(echo git) push`), `eval`, script wrapper,
biến chưa expand (`git push $BR`), `git worktree add -b`, thao tác qua GUI/IDE
không đi qua Bash tool. Lý do: hook chỉ thấy **văn bản lệnh thô, chưa shell-expand**.

**Cảnh báo nhánh cũ (squash-merge)**: `--merged` KHÔNG nhận ra nhánh đã
**squash-merge** ⇒ danh sách WARN ở §7 có thể có dương giả (đo: 2/3 nhánh lấy mẫu ở
`team-ai-pack` đã có subject nằm trong `git log main` nhưng vẫn nằm trong
`git branch --no-merged main`) ⇒ thông điệp luôn là "merge **hoặc xoá**", không chỉ
"merge". Đây là giới hạn đã biết, không phải sót — liệt kê để người bảo trì biết
giới hạn thật của gate, không phải công thức để né hook.
