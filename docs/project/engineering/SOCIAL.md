# Social — vận hành và phạm vi hiện hành

02/11/2026 · **verified trên workspace và QA**, chưa đưa lên dịch vụ đang chạy.

## Người dùng sử dụng

Mở **News → Social** (`/dashboard-static/news/social`), chọn **Cập nhật** để thu thập lần đầu. Bốn nguồn tìm kiếm mặc định chia đều Việt Nam/quốc tế; có thể tắt hoặc thêm chủ đề riêng trong **Nguồn theo dõi** (tối đa 12 nguồn/tài khoản). Sau lần thu thập được yêu cầu, nguồn tự chạy lại khoảng mỗi giờ khi worker hoạt động.

**Thêm liên kết** nhận video YouTube hoặc bài Reddit công khai, đưa vào hàng đợi và tự lưu bài đọc được vào **Đã lưu**. Bài đã lưu không bị giới hạn 7 ngày. Video có thể chỉ đọc được mô tả; phụ đề có trạng thái riêng. Dòng khám phá lọc theo ngày đăng thật hoặc thời điểm ghi nhận đầu tiên nếu nguồn không cung cấp ngày; trường hợp sau luôn ghi “Chưa rõ ngày đăng”.

Nguồn hiện dùng public search, tối đa 6 kết quả/lượt. Reddit có thể trả bài rất cũ dù đã thêm điều kiện ngày vào query; ứng dụng vẫn lọc ngày ở phía server. Phạm vi Việt Nam/quốc tế là nhãn của nguồn hoặc lựa chọn khi nhập, không phải kết luận về quốc tịch tác giả hay một bộ phân loại ngôn ngữ.

## Collector local

Agent-Reach v1.6.1 khóa commit `7a38047acf26a729cbb27851e3cb81639da86b29`, chạy trong Python environment riêng. File `requirements-social.txt` khóa dependency đã kiểm tra. Từ root, nếu cần tái tạo environment:

```sh
python3 -m venv .venv-social-tools
.venv-social-tools/bin/python -m pip install -r requirements-social.txt
```

Cần Git khi cài từ commit. Không cài package trùng tên từ PyPI, không chạy trình setup/import cookie tự động. Environment này đã được tạo và thử live trên máy local trong lượt triển khai.

API tự khởi động worker khi module News được bật, `ENABLE_SOCIAL_WORKER` không bằng `0` và Python collector tồn tại. GET chỉ đọc cache/DB; POST trả 202 và job ID. Có thể tắt worker trong API và chạy riêng:

```sh
ENABLE_SOCIAL_WORKER=0 .venv/bin/uvicorn risk_dashboard.api.main:app --app-dir src --port 8000
.venv/bin/python -m risk_dashboard.cli.social_worker
```

API và worker phải dùng **cùng DB** qua `RISK_DASHBOARD_DB_PATH`. `--once` xử lý tối đa một job. Worker và API có thể cùng tồn tại: lease DB bảo đảm một job đang thu thập ở một thời điểm. Các biến tùy chọn:

| Biến | Mặc định / ý nghĩa |
| --- | --- |
| `ENABLE_SOCIAL_WORKER` | `1`; đặt `0` khi dùng worker riêng |
| `SOCIAL_REACH_PYTHON` | `<project>/.venv-social-tools/bin/python` |
| `SOCIAL_REACH_RUNTIME` | `<project>/.local-dev/social-reach`; cache công cụ, không phải cookie trình duyệt |

Docker hiện giữ image ứng dụng cơ sở; environment Python macOS **không thể mount làm Python Linux**. Khi dùng Docker, chạy worker local đã cài ở trên với DB host tương ứng volume `./data:/app/data`, hoặc provision environment collector Linux riêng trong image vận hành và đặt `SOCIAL_REACH_PYTHON`. UI nhận heartbeat của worker riêng. Lượt này không rebuild/restart Docker hoặc dịch vụ localhost:8000.

Frontend build theo workflow hiện có (`npm run build` trong `frontend/` hoặc service watch). Lượt QA dùng `output/social-qa/dist` để không thay bản đang phục vụ.

## Hợp đồng và giới hạn

- Migration `021_social_intelligence` chỉ thêm bảng/index; không reset dữ liệu cũ. Tài khoản từ auth principal là owner cho nguồn, job, bài, phiên bản, bookmark và cursor.
- 20 job pending và 200 job/ngày/tài khoản; chống trùng cùng nguồn/phạm vi trong 120 giây. Timeout và lỗi upstream thử tối đa 3 lần với backoff; source lỗi chờ khoảng 2 giờ. Nguồn yêu cầu login/setup hoặc bị chặn không tự chạy tiếp cho đến khi người dùng yêu cầu lại. Tắt/bỏ nguồn hủy job còn chờ; kết quả job đang chạy bị bỏ nếu nguồn không còn được bật.
- URL chỉ nhận post/video của host cho phép. Adapter public-only; không browser, không login, không dùng cookie/config yt-dlp cá nhân. Process có timeout và kiểm tra kích thước/schema JSON. Text được sanitize, React escape nội dung.
- Tổng hợp là **trích đoạn có nguồn**, không phải mô hình AI kiểm chứng/dịch/diễn giải. Nhận diện mã dùng danh mục VN và một số alias quốc tế, có ngữ cảnh gần mã; độ bao phủ chưa đầy đủ. Gom chủ đề bằng từ khóa/độ giống tiêu đề trong 48 giờ, không hợp nhất ngữ nghĩa đa ngôn ngữ. Không cam kết precision nghiên cứu khi chưa có corpus gán nhãn.
- Các snapshot phân trang có owner/filter, TTL 15 phút, tối đa 10/tài khoản. Có bài mới khi đang đọc nhiều trang thì hiện thông báo cập nhật. Tên chủ đề lấy bài neo; ID không được cam kết bền qua thay đổi bộ lọc/hết cửa sổ thời gian.
- Search sample không dùng tính “độ nóng toàn thị trường”, bullish/bearish hay tín hiệu mua/bán. `attention.available=false`; stance `unknown`. Metrics thiếu là null.
- X, Facebook nhóm/ảnh, nguồn cần đăng nhập, dịch/LLM và thống kê định lượng còn ở các giai đoạn sau của đề xuất. Không có lịch sử/corpus đủ để bật các metric đó.
- Chưa có bộ theo dõi thu hồi/xóa bài tại nguồn hoặc retention tự động của bài/revision. Nội dung lưu là bản đã đọc tại thời điểm thu thập; mở link gốc để kiểm tra hiện trạng.

Xem [báo cáo QA](../qa/results/SOCIAL_IMPLEMENTATION_2026_11_02.md) và [đề xuất nghiên cứu ban đầu](specs/social-intelligence.md).
