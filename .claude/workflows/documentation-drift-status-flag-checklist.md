# Checklist: soi cụm trạng thái khi copy hàng changelog / mục memory

> File **lazy** — không nằm trong 5 `@`-import, chỉ đọc khi sắp thêm/sửa hàng changelog hoặc sửa `plans/*/plan.md`.
> Luật ngắn (auto-load) ở `workflows/documentation-management.md` §Cụm trạng thái khi copy hàng changelog / mục memory.

## Vì sao có file này — 3 ca ĐÃ XẢY RA

| # | Chuyện gì | Sống bao lâu |
|---|---|---|
| 1 | Hàng changelog `v1.1.40` trong `README.md` bê nguyên cụm cờ từ hàng trước khi dời số version. Cờ đúng **lúc viết** (v1.1.40 khi đó là hàng mới nhất), chết ở lần promote kế tiếp mà không ai gỡ. Vá ở `4ef9c5a` (PR #52) | 2026-08-10 → PR #52 |
| 2 | Một cờ chặn debate nằm lại **5 vị trí** trong bó plan epic `token-budget`, trong khi `HANDOFF.md` cùng bó đã ghi là đã gỡ ⇒ người `grep` chuỗi đó tưởng việc còn treo. (Cờ đó thuộc họ verdict `ESCALATE` của `/avatar:debate`) | 2026-08-10 → 2026-08-16 |
| 3 | Một dòng khai sai host đang chạy (`avatar.nal.vn`) sống sót trong file memory **dù chính file đó** có khối đính chính phủ định nó ở 7 dòng dưới | tới 2026-08-16 |

**Điểm chung:** cả 3 đều **đúng lúc viết**. Không ai viết sai — cái sai là **không soi lại khi copy sang chỗ mới / version mới**.

## Quy trình — 4 bước, làm mỗi lần copy

1. **Dò** mọi cụm trạng thái trong đoạn vừa copy (tập literal ở §Tập literal dưới).
2. **Hỏi từng cụm: "còn đúng LÚC NÀY không?"** — không phải "có đúng lúc viết không". Không trả lời được ⇒ đi kiểm, đừng copy tiếp.
3. **Diễn đạt lại phần lịch sử** bằng thì quá khứ ("đã promote", "đã bị `vX` thay"), **không** giữ thể chờ ("chưa…", "đang chờ…").
4. Nếu đoạn vừa sửa nằm trong `plans/*/plan.md` ⇒ **re-attest cùng lượt** (xem §Ràng buộc re-attest).

## ⚠️ Bẫy: gỡ cờ bằng trang trí là KHÔNG gỡ

Giữ **nguyên văn** cụm cờ rồi bọc nó lại thì cụm vẫn còn trong file:

- `~~gạch ngang~~` — mắt người thấy đã huỷ, `grep` vẫn hit.
- `> blockquote` trích lại nguyên văn — y hệt.
- `<!-- HTML comment -->` — vô hình khi render, `grep` vẫn hit.

⇒ Người sau `grep` chuỗi đó vẫn tưởng việc còn treo. **Diễn đạt lại, đừng trích nguyên văn cụm cờ.**

## Tập literal

Khối dưới là **nguồn được ship**; ca test `tests/test-changelog-status-flag-staleness-gate.py` đọc chính khối này và so với tập hằng của nó — lệch là đỏ. Sửa ở đây thì sửa cả hai nơi cùng lượt.

```literals
TODO :: case-sensitive
CÒN TREO :: case-sensitive
CHƯA phát hành :: case-sensitive
⏳ :: case-insensitive
chờ chốt :: case-insensitive
```

**Vì sao chữ hoa phải so case-SENSITIVE:** dạng chữ thường của chúng là từ vựng văn xuôi bình thường. Đo 2026-08-17 trên `README.md`: `TODO` so case-insensitive khớp **4 hàng changelog cũ** (đều là chữ "Todo" trong "lane Todo", "Todo/") ⇒ gate sẽ đỏ trên cây sạch. Case-insensitive **chỉ** dành cho literal đã tiền kiểm **0 hit ở cả hai phép**.

**Literal đã bị LOẠI vì false positive:** `chờ` (văn xuôi "5xx → chờ") và `ĐANG` (văn xuôi "worktree **ĐANG PUSH**", còn nằm trong `**bold**` nên luật "bold + từ pending" cũng không cứu được).

## Ràng buộc re-attest khi sửa `plans/*/plan.md` hoặc `phase-*.md`

Sửa `plan.md` hoặc `phase-*.md` **phải** re-attest `plan_content_sha256` và `plan_bundle_sha256` trong `.claude/state/plan-attestations/<plan>.json` **cùng lượt**. Không làm thì `hooks/plan_stage_common.py` dán nhãn `DRIFTED — re-debate/re-approve` cho bó plan đó ⇒ **đẻ ra đúng một cờ chết MỚI thuộc chính loài file này đang chống**.

## Gate — phủ tới đâu, hở chỗ nào

- **Phủ:** hàng changelog trong `README.md` của pack, và chỉ `rows[1:]` (mọi hàng **trừ hàng mới nhất**). Hàng mới nhất được phép mang cờ vì cờ ở đó có thể còn đúng.
- **Không phủ — khai thẳng, đừng tưởng đã kín:**
  - Mục memory (`~/.claude/projects/*/memory/`) — **ngoài repo**, không cơ chế nào gác. Ca 3 ở trên thuộc nhóm này.
  - Plan ở workspace root (`plans/…` của workspace, không phải của repo) — cũng ngoài repo. Ca 2 thuộc nhóm này.
  - Biến thể literal chưa từng gây sự cố (vd "chưa promote") — tập trên là **tripwire cho thủ phạm đã biết**, không phải chứng minh.
- ⚠️ **Gate không quét file này** (nó chỉ đọc `README.md`) — nếu sau này ai mở rộng gate sang cả `workflows/`, file này sẽ thành false positive vì nó **cố ý** chứa nguyên văn cụm cờ để làm ví dụ.
