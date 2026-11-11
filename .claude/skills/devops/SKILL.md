---
name: devops
description: CI/CD, container and Kubernetes delivery for NAL projects — GitLab CI on git.nal.vn, Docker images pushed to AWS ECR, Helm values deployed by ArgoCD (GitOps), plus deployment strategies, rollback and incident response. Use when writing or fixing `.gitlab-ci.yml`, Dockerfiles, Helm charts/values, Kubernetes manifests, planning a release or rollback, or triaging a production incident. Every production-changing action requires explicit user approval first. Triggers (VI): "dựng CI/CD", "deploy", "rollback", "viết Dockerfile", "sự cố production".
license: MIT
version: 2.0.0
---

# DevOps (NAL)

Giao hàng phần mềm an toàn trên hạ tầng NAL: build → test → image → registry → GitOps → giám sát.
Quy trình và danh sách ràng buộc dựa trên skill MIT của jeffallan (xem `THIRD_PARTY_LICENSE.md`),
viết lại cho GitLab CI + ECR + Helm + ArgoCD.

## Khi nào dùng

- Viết / sửa `.gitlab-ci.yml` (stage, `rules`, `needs`, cache, environment, runner)
- Viết Dockerfile, tối ưu image (dùng `scripts/docker_optimize.py` để soát Dockerfile)
- Viết / sửa chart Helm, values theo môi trường, manifest Kubernetes
- Lên kế hoạch release, chọn chiến lược deploy (rolling, blue-green, canary), soạn rollback
- Điều tra sự cố production, viết runbook, postmortem

## Quy trình 7 bước

1. **Đánh giá** — đọc cấu hình THẬT của dự án trước: `.gitlab-ci.yml`, Dockerfile, chart/values,
   job deploy sửa gì. Xác định nhánh nào deploy và deploy tự động hay thủ công.
2. **Thiết kế** — cấu trúc pipeline, chiến lược deploy, điểm kiểm sức khoẻ.
3. **Triển khai cấu hình** — sửa file trong repo (IaC/GitOps), không sửa tay trên cụm.
4. **Kiểm** — lint YAML, `helm lint` / `helm template`, build image local, chạy test; xác nhận
   không có thay đổi phá huỷ trước khi đi tiếp.
5. **Soạn rollout** — môi trường đích, tóm tắt thay đổi, lệnh/thao tác deploy, cách kiểm sau deploy,
   **lệnh rollback** (GitOps: revert commit values — xem `references/nal-gitops-helm-argocd.md`).
6. **Duyệt rồi mới deploy** — đích là production hoặc chạm khách hàng ⇒ trình tóm tắt + rollback,
   **chờ người dùng xác nhận rõ ràng**; chưa xác nhận thì dừng với trạng thái `BLOCKED`.
   Sau deploy chạy lại bộ probe canary và so với mốc đo trước deploy (`references/post-deploy-canary-checks.md`).
7. **Giám sát** — health endpoint, log, cảnh báo; rollback sẵn sàng trước khi coi là xong.

## Tài liệu tham khảo

| Chủ đề | File | Đọc khi |
|---|---|---|
| GitOps NAL | `references/nal-gitops-helm-argocd.md` | Mọi việc deploy/rollback trên hạ tầng NAL — **đọc đầu tiên** |
| GitLab CI | `references/gitlab-ci.md` | Viết pipeline, `rules`, DAG `needs`, environments, runner |
| Docker | `references/docker-patterns.md`, `references/docker-compose.md` | Dockerfile multi-stage, image nhỏ, compose cho local |
| Kubernetes | `references/kubernetes.md` | Deployment, probe, resource, ingress |
| Chiến lược deploy | `references/deployment-strategies.md` | Rolling / blue-green / canary, rollback |
| Sự cố | `references/incident-response.md` | Production lỗi, runbook, postmortem |
| Kiểm sau deploy | `references/post-deploy-canary-checks.md` | Đo mốc trước deploy, so lại sau deploy, ngưỡng đề xuất rollback |

## Ràng buộc

### PHẢI
- Thay đổi hạ tầng đi qua git (pipeline, chart, values); ArgoCD là nguồn sự thật của cụm
- Image tag = commit SHA (hoặc version bất biến); có health check + readiness probe
- Đặt resource requests/limits cho container
- Quét image (vd trivy) và secret (vd gitleaks) trong CI
- Ghi rollback + cách kiểm vào MR hoặc ticket trước khi deploy

### KHÔNG ĐƯỢC
- Đổi production khi người dùng chưa xác nhận rõ cho đúng lần đó (merge vào nhánh auto-deploy cũng tính)
- Đưa secret vào code, file trong repo hay log; in giá trị biến CI ra màn hình
- Dùng tag `latest` cho production
- Rollback bằng `kubectl rollout undo` trên app do ArgoCD quản (sẽ bị sync đè) — revert values
- Bỏ qua bước kiểm ở staging/preview nếu dự án có môi trường đó

## Mẫu đầu ra

Một đề xuất deploy luôn có:

```markdown
**Môi trường:** <staging|production>   **Thay đổi:** <commit/MR>   **Image:** <registry>/<app>:<sha>
**Deploy:** <merge MR / chạy job / sửa values>
**Kiểm sau deploy:** <probe canary + ngưỡng, mốc đo trước deploy ở report>
**Rollback:** <revert commit values `<sha>` → ArgoCD sync> · kiểm lại bằng <…>
**Rủi ro:** <migration? breaking API? thời điểm?>
```

Mỗi dòng **Deploy** và **Rollback** là MỘT bước chạy được, chép nguyên văn được vào `APPROVED_STEP` (nhiều bước ⇒ nhiều dòng, đánh số).
