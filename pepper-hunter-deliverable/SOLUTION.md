<!-- Ban thao do Gemini lam qua Pepper Hunter Doer - CHUA NOP, can duyet truoc khi gui. -->

Dưới đây là file `SOLUTION.md` được phân tích và tổng hợp dựa trên nội dung issue được cung cấp.

---

# SOLUTION.md

## 1. Tóm tắt yêu cầu + Tiêu chí nghiệm thu (Acceptance Criteria)

### Tóm tắt yêu cầu
Hiện tại snapshot dữ liệu đánh dấu `_jobbi.claims_open: true` cho một số công việc có điểm nộp bài (submission destination) không còn hoạt động hoặc không thể truy cập:
1. **BountyBook**: 118 bản ghi liên kết tới `api.bountybook.ai` bị lỗi DNS (`NXDOMAIN`).
2. **Algora / GitHub**: 7 bản ghi liên kết tới `rohitdash08/FinMind` đã bị `archived` (read-only), trong đó issue #144 đã bị khóa (`locked: true`) và hết hạn nộp bài.

Cần cập nhật logic xử lý để:
- Phân tách rõ giữa trạng thái "mở trên bảng công việc" (board-reported open) và "đường dẫn nộp bài thực sự khả dụng" (`claims_open`).
- Không đánh dấu `claims_open: true` nếu repository bị archive, issue bị lock, hoặc đã quá deadline.
- Đối với lỗi DNS (như BountyBook), ghi nhận thời gian và lý do thất bại, hỗ trợ tự khôi phục (recoverable) ở lần đọc khỏe mạnh tiếp theo thay vì đóng vĩnh viễn.
- Giữ nguyên dữ liệu lịch sử và thông tin phần thưởng (payout label/escrowed status).
- Giữ nguồn dữ liệu lành mạnh làm nhóm đối chứng tích cực (positive control).

### Tiêu chí nghiệm thu
- [ ] Các gig thuộc repo bị archive (`archived: true`), issue bị lock (`locked: true`), hoặc đã qua deadline phải trả về `_jobbi.claims_open: false`.
- [ ] Khi gặp lỗi DNS resolution (`NXDOMAIN`), hệ thống phải ghi lại timestamp và lý do lỗi; `claims_open` không được mang giá trị `true`.
- [ ] Cơ chế xử lý DNS failure phải có tính khả hồi: nếu domain hoạt động trở lại ở lần crawl tiếp theo, trạng thái `claims_open` có thể khôi phục bình thường.
- [ ] Dữ liệu lịch sử và thông tin phần thưởng (`payment_state`, payout label) không bị xóa hoặc làm hỏng.
- [ ] Nguồn dữ liệu hợp lệ (như `jobbi.org`) vẫn hoạt động bình thường và giữ trạng thái `claims_open: true` chuẩn xác.

---

## 2. Cách tiếp cận kỹ thuật từng bước

1. **Cập nhật Logic kiểm tra GitHub Source (Algora / GitHub Integrations)**
   - Đọc thêm metadata từ API GitHub: kiểm tra thuộc tính `archived` của repository và thuộc tính `locked`, deadline của issue.
   - Nếu `archived == true` hoặc `locked == true` hoặc `now > deadline`, thiết lập `_jobbi.claims_open = false`.

2. **Cập nhật Logic kiểm tra Health check / DNS cho Endpoint nộp bài (BountyBook & External APIs)**
   - Bổ sung bước kiểm tra phân giải tên miền (DNS lookup / health check) trước khi xác nhận trạng thái khả dụng của destination host.
   - Khi phát hiện lỗi DNS (như `NXDOMAIN` từ Google/Cloudflare resolvers):
     - Ghi nhận `last_failed_at` (thời điểm lỗi) và `fail_reason` (ví dụ: `NXDOMAIN`).
     - Tạm thời đặt `_jobbi.claims_open = false`.
     - Không xóa hoặc đổi trạng thái nguồn gốc thành "closed permanently" trong cơ sở dữ liệu để cho phép tự động phục hồi khi DNS hoạt động lại.

3. **Bảo toàn dữ liệu Lịch sử & Phần thưởng**
   - Đảm bảo các trường thông tin phần thưởng như `payment_state: "escrowed"` và thông tin lịch sử của gig được giữ nguyên vẹn trong payload JSON, chỉ có trường `_jobbi.claims_open` phản ánh đúng khả năng nộp bài hiện tại.

4. **Kiểm tra tương thích với Nguồn lành mạnh**
   - Đảm bảo các nguồn không bị ảnh hưởng (ví dụ: `jobbi.org`) tiếp tục pass các điều kiện kiểm tra và giữ `_jobbi.claims_open: true`.

---

## 3. File / Đường dẫn dự kiến sửa

*Lưu ý: Do issue chưa cung cấp sơ đồ cây thư mục chi tiết của repo, dưới đây là các đường dẫn dự kiến theo cấu trúc module thông thường:*

- `Dự kiến`: `src/crawlers/github.ts` (hoặc `.py`) - Thêm logic kiểm tra `archived`, `locked`, và `deadline` từ GitHub API.
- `Dự kiến`: `src/crawlers/bountybook.ts` (hoặc `.py`) - Thêm logic xử lý DNS lookup failure và ghi nhận lý do/thời gian lỗi.
- `Dự kiến`: `src/processors/claims.ts` (hoặc `.py`) - Hàm tính toán trạng thái `_jobbi.claims_open` dựa trên kết quả health check và metadata của gig.
- `Dự kiến`: `src/types/jobbi.ts` (hoặc `.py`) - Cập nhật type/schema lưu vết thông tin lỗi DNS (timestamp, reason) nếu có.

---

## 4. Kế hoạch tự test

### Test Case 1: Kiểm tra GitHub Repo bị Archive & Issue bị Lock
- **Thao tác**: Chạy crawler/processor với repo `rohitdash08/FinMind` và issue `#144`.
- **Kỳ vọng**:
  - `archived` trả về `true`, `locked` trả về `true`.
  - Kết quả JSON đầu ra có `_jobbi.claims_open: false`.
  - Các trường `payment_state` và lịch sử vẫn được giữ nguyên.

### Test Case 2: Kiểm tra Lỗi DNS (BountyBook NXDOMAIN)
- **Thao tác**:
  1. Giả lập/thực hiện kiểm tra DNS cho host `api.bountybook.ai` (khiến DNS trả về `NXDOMAIN`).
  2. Giả lập lần đọc tiếp theo khi DNS đã phục hồi (Domain khả dụng).
- **Kỳ vọng**:
  1. Lần 1: `_jobbi.claims_open` là `false`, hệ thống ghi nhận thời gian và lý do lỗi DNS.
  2. Lần 2: Hệ thống khôi phục `_jobbi.claims_open: true` khi domain hoạt động lại.

### Test Case 3: Positive Control (Nguồn hoạt động bình thường)
- **Thao tác**: Chạy fetch/check đối với nguồn hợp lệ (`jobbi.org`).
- **Kỳ vọng**: `_jobbi.claims_open` vẫn trả về `true`.

### Test Case 4: Kiểm tra lại bằng lệnh Reproduction Script
- **Thao tác**: Chạy lệnh curl & jq được cung cấp trong issue:
  ```sh
  curl -fsS 'https://jobbi.org/gigs.json?lane=agent&limit=1000' |
  jq '{generated:._jobbi.generated,total:(.items|length),
      bountybook:([.items[]|select(._jobbi.source=="bountybook" and ._jobbi.claims_open)]|length),
      finmind:([.items[]|select(._jobbi.extra.repo=="rohitdash08/FinMind" and ._jobbi.claims_open)]|length)}'
  ```
- **Kỳ vọng**: Kết quả `bountybook` và `finmind` đếm số bản ghi có `claims_open: true` phải bằng `0`.
