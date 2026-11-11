# Autopilot — Release profile và deploy

> Nguồn: spec §14. Dùng bởi `deploy-v1` (executor=controller) và bởi G3 review khi chuẩn bị release manifest. "G3 duyệt đúng candidate, đúng artifact và đúng môi trường."
>
> **V1 (từ bản CLI sau `3.33.0-beta.5`):** deploy **không** chạy như một ticket `deploy-v1` — ticket loại này bị từ chối ở lối vào (xem `command-adapters.md`). Bước deploy/verify chạy trong release flow của `avatar autopilot run`, theo `config.release` (`remote`, `target_branch`, `deploy_recipe`, `verify_recipe`) sau khi G3 được duyệt. Đọc "Trạng thái cuối của release flow" ở dưới trước khi viết plan/playbook nói về deploy.

## 14.1 Profile được chốt trong G1/Survey/Plan

| Nhóm trường | Nội dung |
|---|---|
| Target / authority | Environment (QA/staging/production theo scope), account/project/server IDs, repo và GitOps path nếu có, capability/secret names, quyền và ngân sách. |
| Source / trigger | Host/origin, base branch/SHA, reviewed head, merge method, merge candidate khi nền tảng cung cấp; trigger merge-main, tag, explicit job hoặc command. |
| Artifact / provenance | Immutable image digest/build artifact/edge bundle version, source mapping, CI pipeline ID, GitOps revision, release operation ID. CI build sau merge ⇒ G3 bind input + build recipe; output digest phải xác minh provenance trước rollout hoặc qua gate pipeline theo profile. |
| Migration / recovery | Manifest/hash, loại additive/destructive/data transform, thứ tự trước/sau app, compatibility window, backup ID, restore preconditions, rollback/forward-fix procedure. |
| Verification | Rollout timeout, expected artifact, readiness fields, smoke nghiệp vụ chính, failure thresholds và bước xác minh rollback. |

## 14.2 Review → release

1. Chốt code, blueprint/plan/ticket definitions và audit snapshot; regression pass. Supervisor freeze candidate SHA, **không** thêm runtime metadata commit.
2. Dispatch `review-local-v1` trên đúng candidate (tái dùng quy trình review local của `/review-pr`). Controller kiểm risk ≤ MEDIUM, security/quality evidence và secret scan, ghi receipt vào `review_state_root` riêng. Policy facade kiểm đúng mission/head/base/policy rồi controller mới push feature và mở/cập nhật MR — **v1 chỉ GitLab** (push option `merge_request.*` + GitLab REST; remote GitHub ⇒ `doctor` fail, `run` bị chặn trước dispatch/push). Không gọi nguyên slash command hay ghi gate vào source checkout.
3. Dispatch `review-remote-v1` để kiểm required CI/review trên remote candidate và base/merge result theo profile; controller thu evidence và cập nhật review receipt. Code/base thay đổi ⇒ invalidate bằng chứng tương ứng, kiểm lại rồi mới tạo request G3.
4. G3 bind release manifest/candidate và các operation sẽ tác động remote. Kiểm ngay trước side effect đầu tiên rằng approval, SHA/base, target và recipe còn khớp. V1: release manifest hash là sha256 canonical của candidate SHA, `remote`, `target_branch`, toàn bộ `deploy_recipe` và `verify_recipe` (recipe vắng thì ghi `null`), cộng `deploy_timeout_sec`/`verify_timeout_sec` nếu có khai (không khai thì không thêm khoá nào, nên hash cũ giữ nguyên). Đổi recipe, target, remote hoặc timeout sau khi đã duyệt, kể cả thêm recipe mới, đều ⇒ G3 mới trước mọi side effect. `cwd` của recipe release phải tương đối và nằm trong worktree (tuyệt đối hoặc có `..` ⇒ `config_invalid`). Worktree còn thay đổi chưa commit ngay trước deploy ⇒ `blocked:deploy`.
5. `deploy-v1` (executor=controller) chạy thứ tự đã duyệt: có thể migration additive trước merge, hoặc merge/job/tag trigger deploy, hoặc app tương thích trước migration destructive. Mỗi operation ghi intent/receipt và reconcile được; `decision-v1` chuẩn bị kế hoạch nếu cần — **không** cấp deploy authority cho model. V1: bước này là `deploy_recipe` của `config.release`, một recipe cục bộ do release flow chạy; receipt deploy ghi ngay khi recipe exit 0, trước smoke.
6. Đối chiếu artifact rollout, smoke ứng dụng và dữ liệu trong VERIFYING. Chỉ DONE khi đủ evidence; health liveness 200 và "đã push GitOps" **không thay thế** việc ứng dụng chạy đúng. V1: smoke là `verify_recipe`; **rollout chưa được quan sát** (chưa có probe bản đang chạy), nên `released` = deploy và smoke đều exit 0, không phải "đã đối chiếu bản đang chạy".

Điều kiện để G3 được xin (v1): bằng chứng remote phải thuộc đúng commit vừa push — head SHA và SHA pipeline mới nhất của MR đều là commit đó, base là base của mission. MR chưa có pipeline (`pipeline_sha: not_reported`) hoặc lệch SHA ⇒ không xin G3 (`blocked:release_flow`, lý do nêu SHA lệch). Có `deploy_recipe` mà thiếu `verify_recipe` ⇒ cũng chặn trước G3.

## Trạng thái cuối của release flow (v1)

Khi ticket loop đã `done` và có `config.release`, stdout của `run` ghi `outcome=done, release=<nhãn>`. Không có `config.release` ⇒ nhãn `done`, exit 0.

| Nhãn | Exit | Nghĩa |
|---|---|---|
| `waiting_gate:g3` | 1 | G3 đang chờ duyệt (người, hoặc Claude ủy nhiệm khi lái từ chat: `--targets` = nhánh `target_branch` + `--expires` ≤ 1 h). Nếu thiếu `deploy_recipe`, dòng G3 ghi "duyệt G3 KHÔNG deploy gì". |
| `blocked:release_flow` | 1 | Chưa có review report; `deploy_recipe` thiếu `verify_recipe`; hoặc bằng chứng remote lệch SHA / chưa có pipeline. |
| `done_without_deploy` | 0 | G3 đã duyệt nhưng `config.release` không có `deploy_recipe`: 0 lệnh chạy, 0 receipt; MR vẫn merge tay. Thêm recipe sau đó ⇒ G3 mới. |
| `released` | 0 | `deploy_recipe` và `verify_recipe` đều exit 0. Rollout `not_observed`. |
| `blocked:deploy` | 1 | Tái kiểm G3 trước side effect đầu hỏng, worktree mission còn thay đổi chưa commit, hoặc `deploy_recipe` fail. Chưa có receipt, chạy lại được. |
| `blocked:deploy_smoke_failed` | 1 | Deploy exit 0, smoke fail. Receipt deploy giữ lại; chạy lại chỉ chạy lại smoke, không deploy lần hai trên cùng candidate + recipe. |
| `blocked:release_g3_invalid` | 1 | Đã deploy nhưng G3 không còn hợp lệ (hết hạn, target đổi) trước khi smoke pass; smoke không chạy. Lối thoát: đổi `config.release` (xin G3 mới) hoặc kiểm tay môi trường rồi `archive`. |
| `blocked:release_unverified_legacy` | 1 | Có receipt `deployed_verified` do CLI trước H14 ghi (có thể sinh từ hai lệnh `true`). Không deploy lại, không tính released; kiểm tay môi trường rồi `archive`. |
| `blocked:deploy_outcome_unknown` | 1 | Không xác định được deploy trước đó ra sao: `run` chết lúc recipe deploy chạy, recipe quá `deploy_timeout_sec` (mặc định 60) hoặc bị signal giết, hoặc receipt deploy hỏng. Autopilot không bao giờ tự deploy lại. Người kiểm tay môi trường đích rồi chạy ĐÚNG MỘT lệnh: `avatar autopilot resolve-deploy --candidate <sha đầy đủ> --outcome deployed` (chỉ chạy smoke) hoặc `… --outcome not-deployed` (deploy lại sau khi tái kiểm G3); không đổi `config.release` trước khi trả lời `deployed` (lệch deploy hash ⇒ bị từ chối). Receipt hỏng ⇒ kiểm tay, xoá đúng file receipt được nêu rồi `run` lại. Bỏ mission ⇒ `archive`. Recipe exit ≠ 0 hoặc không khởi động được ⇒ `blocked:deploy`, `run` lại được — recipe phải chịu được chạy lại. |

`run` exit 0 chỉ khi mission xong thật (`done`, `released`, `done_without_deploy`); Ctrl-C ⇒ 130; còn lại ⇒ 1. Gợi ý `archive` chỉ in khi exit 0. Process chết sau khi recipe deploy exit 0 và kết quả đã vào journal nhưng trước khi ghi receipt ⇒ lần `run` sau ghi bù receipt, không deploy lại.

## Repo có merge tự deploy

Một số repo (vd telemetry: main → GitLab CI → image → GitOps → ArgoCD) tự động deploy khi merge. G3 phải ở **trước** merge/trigger này; controller theo dõi pipeline sẵn có thay vì mở thêm một phiên deploy tag riêng. Mission QA **không** được merge vào nhánh auto-production để "thử QA" — chọn đúng release branch/job/environment hoặc yêu cầu bổ sung quyền/profile trước khi tiếp tục.

Tag `mission/<id>/release-<n>` dùng làm nhãn audit khi remote/policy cho phép, **không phải** cơ chế deploy bắt buộc cho mọi repo. Khi squash merge: ghi mapping head-được-review → merge-SHA → artifact; không tìm commit ticket chỉ bằng message sau merge. V1 không deploy code chưa qua merge/review theo profile; preview local phục vụ test là tài nguyên phát triển riêng, không phải release.

## 14.3 Dữ liệu và credential

- Deploy executor của supervisor mới được lấy secret/capability **sau G3**; worker implement không nhận chúng.
- Backup trước migration ghi backup ID và kiểm khả năng phục hồi.
- Restore sau khi có ghi dữ liệu mới chỉ tự chạy nếu cửa sổ mất dữ liệu/maintenance và preconditions đã được duyệt; còn lại forward-fix hoặc escalation.
- Recipe migration dùng đúng runbook của repo, không thay bằng blanket `supabase db push` khi lịch sử môi trường không tương thích.
- Máy tắt thì mission dừng tiến độ (v1 chấp nhận). Journal bảo vệ khỏi crash tiến trình/ngắt nguồn trên filesystem đã kiểm, không bảo đảm cứu được máy mất đĩa. Backup control root theo vận hành, có bảo vệ secrets. Run lại trên cùng máy reconcile rồi tiếp tục; chuyển máy phải theo quy trình chuyển quyền/tài nguyên, không copy PID lock rồi chạy.

## Không làm

- Không mở thêm một phiên deploy tag khi repo đã có pipeline auto-deploy từ merge.
- Không coi "health liveness 200" là bằng chứng đủ cho DONE.
- Không đề xuất ticket `deploy`/`revert` trong plan: v1 từ chối chúng ở lối vào. Muốn deploy thì khai `deploy_recipe` + `verify_recipe` trong `config.release`; không khai thì G3 chỉ ghi nhận quyết định, không deploy.
- Không báo "đã deploy" hay "rollout đã xác minh" khi nhãn là `done_without_deploy` hoặc khi rollout còn `not_observed`.
- Không tự suy Supabase/cloud project từ config repo khi workspace có nhiều project khác vai — kiểm read-only năng lực tài nguyên G1 trước.
