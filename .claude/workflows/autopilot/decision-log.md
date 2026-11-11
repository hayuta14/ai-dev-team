# Autopilot — Sổ quyết định (decision-log) và revision

> Nguồn: spec §11 + spec V2 §4.0/§4.1. Có **hai** nơi ghi quyết định, tách theo thời điểm:
> - **Trước G0** — mục `## Sổ quyết định` cuối `BLUEPRINT.md`: "default được ủy nhiệm" startbuild ghi (theo `startbuild-interview.md`) và quyết định người ghi khi tạo revision BLUEPRINT mới. Viết theo format dưới.
> - **Lúc mission chạy** — sổ **journal-backed ở control root** (không phải file trong repo), xem bằng `avatar autopilot status --decisions`. Controller **không** ghi vào BLUEPRINT.

## Sổ lúc mission chạy (journal, control root)

| Mục trên `status --decisions` | Nguồn journal | Thẩm quyền |
|---|---|---|
| Quyết định tự áp | `decision_auto_applied` (option id + nhãn, `claims`, `authority_ref`, `blueprint_hash`, `decided_at`) | `delegated:<G0 id>` — chỉ khi BLUEPRINT đã duyệt G0 khai `decision_policy: auto` và đủ luật auto (spec V2 §4.1) |
| Người trả lời | `decision_answered` (`question_id`, option id/giá trị, `directive_id`) | `user:<actor>` qua `@avatar answer` / `avatar autopilot answer` |
| Claude ủy nhiệm trả lời | `decision_answered` + `rationale` (phiên chat lái mission, `answer --delegated`) | `chat_delegated:<actor>` — hiển thị "Claude thay chủ mission (qua chat)", không bao giờ là người |
| Worker ghi nhận | `result.decisions[]` của worker ⇒ field `worker_decisions` trên `attempt_finished` cùng attempt | **không có** — chỉ là lời worker tự kể, không phải quyết định auto/người |
| Câu đang chờ | câu `required` chưa trả lời trong `interview.json` | — |

- Vì sao không ghi vào repo: recover (`reset --hard` + `clean -fd`) không xoá được journal; không sinh metadata commit sau candidate freeze; không đổi bytes BLUEPRINT ⇒ G0 không tự huỷ.
- Mất `interview.json` ⇒ sổ vẫn dựng lại từ journal. Mission chạy bằng CLI chỉ có V2-0 (3.34.4: có `decision_answered`, chưa có event câu hỏi) ⇒ text câu hỏi lấy từ `interview.json` nếu còn; mất thì chỉ hiện `question_id` + giá trị.
- Quyết định tự áp đảo được bằng `@avatar redirect: …`. Release (G3): mô tả MR dẫn danh sách QĐ khi sổ ≥ 1 mục (qua redactor, không vào hash G3).

## Worker ghi quyết định thế nào

1. Trả `decisions[]` trong result (§5.3) — mỗi mục ghi Bối cảnh, Các phương án, Chọn, Lý do, Đánh đổi, Nguồn/Ticket, viết theo hành vi sản phẩm. `decisions[]` của worker **không** mang trường thẩm quyền/ủy nhiệm — thẩm quyền do controller/người gán. Trích quyết định đã chốt ⇒ chép **nguyên** chuỗi sau `nguồn:` mà prompt in (vd `delegated:<id>`) hoặc `question_id`, không thêm chữ. Controller chỉ **ghi nhận** (journal, hiện như "worker ghi nhận"); không áp vào BLUEPRINT/PLAN.
2. Muốn đổi ticket ⇒ `proposed_changes[]` (CHỈ mutation TICKET); plan đổi ⇒ G2 xin lại. **Không tự sửa** ticket/BLUEPRINT trực tiếp.
3. Cần người chọn ⇒ `outcome: needs_decision` theo `escalation.md` (options có `id`, `recommended_option_id`, `boundary_claims`).

## Format một mục QĐ (mục `## Sổ quyết định` của BLUEPRINT, trước G0)

Format này chỉ dùng cho sổ BLUEPRINT (người/startbuild ghi) — không phải shape của `decisions[]` worker trả.

```
### QĐ-04 · 2026-09-08 · Cách lưu phiên đăng nhập
Bối cảnh: điều cần giải quyết, nói theo hành vi sản phẩm.
Các phương án: A ... / B ...
Chọn: B.
Vì sao tốt cho người dùng và business: ...
Đánh đổi chấp nhận: ...
Nguồn: URL hoặc artifact hash · Ticket: T-0009 · Run: ...
Thẩm quyền: default được ủy nhiệm (startbuild) / người (revision BLUEPRINT mới).
Thay thế quyết định: QĐ-02 (nếu có); không xóa mục lịch sử.
```

Trường bắt buộc: mã QĐ tăng dần (`QĐ-NN`), ngày, tiêu đề ngắn theo hành vi sản phẩm (không theo tên hàm/class), Bối cảnh, Các phương án, Chọn, Lý do (người dùng/business trước, kỹ thuật sau), Đánh đổi, Nguồn (nếu có), Ticket/Run (nếu có), Thẩm quyền, Thay thế quyết định (nếu có).

**Hệ quả với G0 (B3):** G0 gắn với sha256 bytes của `BLUEPRINT.md`. Người sửa sổ (hay bất kỳ byte nào) sau G0 ⇒ trước lần dispatch feature kế tiếp G0 tự huỷ và được request lại với hash mới ⇒ duyệt lại bằng `@avatar approve g0 <id mới>`. Gom nhiều quyết định vào một revision để chỉ duyệt lại một lần.

## Thay đổi scope

- Đổi scope làm code đã "done" không còn đáp ứng AC ⇒ mark `superseded` hoặc tạo ticket sửa/retest; **không giữ nhãn done** cho revision mới chưa được kiểm lại.
- Thu hẹp scope có thể huỷ ticket chưa làm, rồi đi TESTING → REVIEWING → G3 với phần đã hoàn chỉnh.
- Mọi ticket gắn blueprint/plan input cụ thể theo revision; sửa định nghĩa nguồn tăng revision **và** đánh giá lại các ticket đang done/dependencies liên quan — không âm thầm để ticket cũ trỏ vào định nghĩa đã lỗi thời.

## Không làm

- Không tạo metadata commit sau candidate freeze chỉ để lưu trạng thái duyệt/deploy/quyết định — các receipt đó nằm trong journal, không phải commit runtime.
- Không xoá mục lịch sử khi một quyết định bị thay thế; dùng "Thay thế quyết định" trỏ tới mã QĐ cũ.
- Plan và verification recipes có revision **độc lập** với blueprint — đừng gộp chung một số revision cho cả ba.
