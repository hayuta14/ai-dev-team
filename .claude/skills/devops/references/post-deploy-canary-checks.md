# Kiểm sau deploy (canary) — có mốc so sánh

Một lần `curl` health trả 200 chưa chứng minh bản mới chạy đúng: có thể pod cũ còn phục vụ, asset build mới
404, hoặc lỗi chỉ hiện sau vài phút. Cách làm: **đo mốc trước deploy** (lúc `MODE: prepare`), **đo lại cùng
bộ probe sau deploy** (lúc `MODE: execute`), so từng dòng. Tất cả probe dưới đây chỉ ĐỌC.

Ý tưởng bộ probe và ngưỡng lấy từ skill `canary-watch` của affaan-m/ECC (MIT), viết lại cho hạ tầng NAL.

## Bộ probe

Thay `<URL>` bằng host thật của môi trường (đọc từ ingress/values, không đoán). Mỗi lệnh `--max-time 10`.

| # | Kiểm | Lệnh | Ghi lại |
|---|---|---|---|
| 1 | Mã trạng thái **hop đầu** của trang chính và route API chính | `curl -sS -o /dev/null -w '%{http_code} %{time_total}\n' --max-time 10 <URL><path>` (KHÔNG `-L`) | mã + thời gian |
| 2 | Health | `curl -sS --max-time 10 <URL>/api/health` (hoặc endpoint health của dự án) | JSON nguyên văn |
| 3 | Bản mới đã thật sự lên | trường khởi động trong health (vd `startedAt`/`uptimeSec` của telemetry) phải ĐỔI so với mốc; có trường version/commit thì so với SHA deploy | giá trị trước/sau |
| 4 | Asset tĩnh của bản build mới | `A=$(curl -sS --max-time 10 <URL><page> \| rg -o '/_next/static/[^"]+\.(js\|css)' \| head -1)` rồi `curl -sS -o /dev/null -w '%{http_code} %{content_type}\n' --max-time 10 "<URL>$A"` | mã + content-type |
| 5 | Pod / ArgoCD (nếu máy có quyền) | `kubectl --context <ctx> get pods -n <ns> -l <selector>` (Ready, RESTARTS) · `argocd app get <app>` (Synced/Healthy) | trạng thái, số restart |
| 6 | Lỗi trong log (nếu có quyền) | `kubectl --context <ctx> logs -n <ns> deploy/<name> --since=10m \| rg -c -i 'error\|exception'` | số dòng |
| 7 | SSE (chỉ khi dự án có endpoint event-stream) | `curl -sS -N --max-time 15 -H 'Accept: text/event-stream' <URL><sse-path> \| head -c 300` | có nhận event/heartbeat đầu không |
| 8 | Lỗi console trình duyệt (khi thay đổi chạm UI) | skill `chrome-devtools` (script console/performance) trên trang chính | số lỗi console mới |

Probe 5–6 chỉ chạy với `--context <ctx>` và `-n <ns>` lấy từ values/chart của **chính dự án** hoặc từ brief; KHÔNG dùng context hiện hành của máy (`kubectl config current-context` có thể là một cụm production khác — spawn-test 20/10 đã kiểm nhầm `nal-prod-eks` vì thế). Không xác định được context ⇒ bỏ probe 5–6, ghi lý do.

Không có quyền hoặc thiếu công cụ cho dòng nào ⇒ ghi "không kiểm được (lý do)", không đoán.

## Đọc kết quả

Kỷ luật mã trạng thái: **401** = route sống nhưng thiếu auth · **404** = không có route · **30x** ở hop đầu là bình
thường với trang có redirect (vd `/vi/` → login) — so với mốc, đừng ép mọi thứ phải 200.

**Nghiêm trọng** (đề xuất rollback, dừng `BLOCKED: waiting for approval`):
- Mã hop đầu khác mốc theo hướng xấu (2xx/3xx → 4xx/5xx), hoặc route API chính trả 5xx.
- Health không còn báo DB kết nối (`db` khác mốc), hoặc health không trả lời.
- Trường khởi động KHÔNG đổi sau khi pipeline báo xong ⇒ bản mới chưa lên (pod cũ còn chạy hoặc rollout kẹt).
- Asset JS/CSS của trang trả 4xx/5xx hoặc content-type đổi (vd thành `text/html`).
- Pod không Ready, hoặc RESTARTS tăng sau deploy; ArgoCD không Healthy.
- SSE không kết nối được hoặc không nhận event đầu tiên.

**Cảnh báo** (ghi trong report, không tự rollback):
- Thời gian phản hồi > 2× mốc ở probe 1 (đo lại 1 lần trước khi kết luận).
- Số dòng lỗi log > 2× mốc và ≥ 5.
- Lỗi console mới so với mốc.

## Theo dõi kéo dài

Mặc định đo một lượt ngay sau khi pipeline/ArgoCD báo xong. Đề xuất có rủi ro (migration, đổi hợp đồng API,
service mới) ⇒ ghi trong `Kiểm sau deploy` thêm 2 lượt ở mốc +5 và +15 phút; mỗi lượt ghi bảng kết quả với giờ đo.

## Mẫu ghi trong report

```markdown
| Probe | Mốc (giờ) | Sau deploy (giờ) | Kết luận |
|---|---|---|---|
| 1 GET /vi/login hop đầu | 200 · 0,36s | 200 · 0,41s | ok |
| 3 startedAt | 2026-10-19T15:10:59Z | 2026-10-20T02:31:12Z | bản mới đã lên |
| 4 asset css | 200 text/css | 200 text/css | ok |
```
