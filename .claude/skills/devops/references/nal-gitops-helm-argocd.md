# NAL — GitLab CI → ECR → Helm values → ArgoCD (GitOps)

Mô hình triển khai chung mà các dự án NAL trên Kubernetes đang dùng. Đây là **khuôn**, không phải
cấu hình thật của dự án nào: luôn đọc `.gitlab-ci.yml`, chart Helm và repo values của chính dự án
trước khi đề xuất thay đổi.

## Dòng chảy

```
push / merge vào nhánh deploy (thường là main)
  → GitLab CI trên git.nal.vn: test → build image → scan → push ECR (tag = commit SHA)
  → job deploy sửa image tag trong repo Helm values (GitOps)
  → ArgoCD thấy repo values đổi → sync → Kubernetes rollout
```

Điểm quan trọng: **trạng thái mong muốn nằm trong git** (repo values), không nằm trong cụm.
Muốn đổi prod thì đổi git; đổi tay trong cụm sẽ bị ArgoCD sync đè lại.

## Đọc gì trước khi đụng vào

| Câu hỏi | Nơi trả lời |
|---|---|
| Nhánh nào deploy, job nào chạy khi nào | `.gitlab-ci.yml` của repo (khối `workflow:rules`, `rules:` từng job) |
| Image đẩy đi đâu, tag thế nào | job build trong `.gitlab-ci.yml` (registry ECR, biến tag) |
| Giá trị Helm thật của môi trường | repo/thư mục values mà job deploy sửa (tên repo nằm trong script job) |
| App nào ArgoCD quản | ArgoCD Application trỏ tới repo values đó |
| Biến/secret CI | Settings → CI/CD → Variables của project (chỉ xem tên, KHÔNG in giá trị) |

`k8s.yaml` hay manifest trong repo ứng dụng có thể chỉ là **tham chiếu**, CI không apply — kiểm job
deploy thật sự làm gì trước khi tin file đó.

## Rollback đúng cách với ArgoCD

- **Đúng:** revert commit đổi image tag trong repo values (hoặc đặt lại tag cũ), push, để ArgoCD sync.
  Kiểm: ArgoCD app `Synced` + `Healthy`, pod mới chạy tag cũ, health endpoint trả 200.
- **Sai:** `kubectl rollout undo` / sửa Deployment tay — ArgoCD (self-heal) sẽ sync đè về tag trong git,
  rollback "biến mất" sau vài phút.
- Migration DB đã chạy KHÔNG tự lùi theo image — rollback ứng dụng phải tương thích schema hiện tại,
  hoặc có migration lùi viết sẵn và đã thử.

## Rào an toàn khi làm việc với pipeline có auto-deploy

- Repo mà **push `main` = deploy prod** thì mọi merge vào `main` là một lần deploy: coi như cần duyệt
  deploy, không chỉ duyệt code.
- Không tự chạy job deploy thủ công, không sửa repo values prod, không đổi biến CI khi người dùng
  chưa xác nhận rõ ràng cho đúng lần đó.
- Không in, log hay chép giá trị biến CI/secret; chỉ nhắc tên biến.
- Mỗi đề xuất deploy kèm 3 thứ: lệnh/thao tác deploy, cách kiểm sau deploy, cách rollback.

## Kiểm nhanh trạng thái (chỉ đọc)

```bash
glab ci list --repo <group>/<project>              # pipeline gần nhất
glab ci get -p <pipeline-id> --repo <group>/<project>   # `glab ci view` là TUI tương tác, đừng dùng
glab ci status --repo <group>/<project>
kubectl -n <ns> get deploy,pods -l app=<app>        # nếu có quyền đọc cụm
argocd app get <app>                                # nếu có argocd CLI
curl -s -o /dev/null -w '%{http_code}' https://<host>/health
```

`git.nal.vn` chỉ mở cho dải mạng cho phép (văn phòng / VPN): lệnh treo ~150 s rồi
`Failed to connect … port 443` nghĩa là đang ở ngoài mạng, không phải lỗi repo.
