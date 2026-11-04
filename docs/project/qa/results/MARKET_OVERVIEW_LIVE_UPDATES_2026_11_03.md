# Tổng quan thị trường: thu gọn UI và cập nhật từng ô

Ngày: 03/11/2026. Trạng thái: **đã sửa và kiểm chứng**.

## Phạm vi và tiêu chí

Theo yêu cầu người dùng: bỏ phần tiêu đề/trạng thái lớn trong ảnh; làm gọn và đồng nhất trang Tổng quan; giá/% chỉ cập nhật ô tương ứng; đổi diện tích có chuyển động tại vùng liên quan; giữ một bản đồ, tỷ trọng GTGD thật, zoom/kéo và sáng/tối. Không thay nguồn báo giá hoặc công thức nghiệp vụ backend.

## Thay đổi

- Bỏ hero `Tổng quan thị trường`, mô tả lặp và cụm trạng thái riêng. Gộp tiêu đề bản đồ, bộ lọc, tìm kiếm và thao tác vào thanh công cụ; ở 1600px, phần điều khiển trước bản đồ cao 98px.
- Chuyển chú giải xuống dưới bản đồ, đưa hướng dẫn/nguồn/thời gian/thiếu dữ liệu vào `Dữ liệu & cách xem`; vẫn hiển thị cảnh báo stale/gián đoạn và lỗi cần xử lý.
- Worker tồn tại theo phạm vi lọc; khóa tính bố cục không chứa giá/% hay thứ hạng do feed trả về. Dữ liệu giá mới cập nhật qua các cell React memo với khóa mã cố định.
- Dùng các cây `treemapResquarify` riêng cho ngành và mã trong ngành. Tái sử dụng thứ tự/hàng khi trọng số đổi; mã mới chỉ dựng lại hàng trong ngành của nó. Resize khung được phép tính lại tỷ lệ để tránh ô quá dài trên mobile.
- Không trả `layout=null` khi đang cập nhật. Lỗi mạng/worker giữ bản đồ đã có; retry khôi phục. Phản hồi worker cũ không được ghi đè yêu cầu mới.
- Giữ cặp bố cục/báo giá của khung đang vẽ đến khi worker hoàn tất khi thêm/bớt mã. Ca chậm 600ms đã tái hiện lỗi tooltip biến mất trước khi thay bố cục (`membership-before.log`), sau đó được sửa.
- Màu chuyển 180ms, hình học 220ms; kéo/zoom trực tiếp không chịu animation diện tích. Camera giữ tọa độ qua tick thông thường; chỉ khôi phục góc nhìn khi mã ghim mất khỏi bản đồ hoặc không còn đọc được.
- Tổng giá trị ở bản đồ chỉ cộng mã thực sự được vẽ; dạng bảng dùng tổng các hàng đủ dữ liệu diện tích, kể cả hàng thiếu %.

## Tham khảo giao diện

Đã mở trực tiếp [FireAnt Dashboard](https://fireant.vn/b/dashboard), xem thanh chỉ số, tiêu đề bản đồ gọn, chọn GTGD/vốn hóa và chú giải. Ở lần quan sát khoảng 09:12, bản đồ FireAnt trống; không tuyên bố đã kiểm chứng thuật toán hoặc animation nội bộ của FireAnt. Thiết kế/logic triển khai dựa trên source và phép đo của Northstar.

## Kết quả kiểm chứng cuối

- Frontend suite: **188/188 đạt**; riêng heatmap **16/16 đạt**, gồm kiểm tra tỷ trọng, không chồng ô, biến động liên tục 20 tick, thêm/bớt mã và ổn định ngành khác. Suite đầy đủ chạy trước chỉnh cuối về giữ quote khi chuyển bố cục; thay đổi React cuối được kiểm chứng trực tiếp bằng browser ở dưới.
- Chromium: **12 nhóm live update + 9 nhóm hồi quy đạt**, không có `pageerror`. Ca lỗi mới giữ tooltip khi mã bị loại và worker chậm 600ms đã đạt sau sửa.
- Dữ liệu giống hệt:0 cell mutations/0 layout requests; đổi giá riêng VCB: chỉ VCB đổi,0 cell bị tháo; tự polling cũng chỉ cập nhậtVCB.
- Cập nhật trọng số bị trì hoãn:0 khung trắng trong 60 frame được lấy mẫu, giữ nguyên SVG/DOM của các ô còn trong viewport và tọa độ camera, có chuyển động `width/x/transform/font-size`.
- ESLint:0 errors/1 warning Social cũ; CSS 57 files/0 failed; QA build và local build đạt. Localhost:8000 phục vụ cùng entry `index-BO_WkaU7.js` với bản QA (giá trị chính xác trong `live-assets.json`).
- Git staging giữ nguyên SHA256 `8c028f64e8ee1bec3998b905eaad1ae93998acc51418e46bd8fcb03300f1dd1e`; `git diff --check` đạt. Không push/publish/deploy hoặc khởi động lại server 8000.

## Bằng chứng

Thư mục: `output/market-overview-live/`.

- `checks.json`, `browser.log`: tình huống cập nhật độc lập, độ ổn định DOM, lỗi mạng/worker, zoom, lọc, bảng, responsive và polling.
- `browser-regressions.json`, `previous-regressions.log`: hồi quy đơn vị nhỏ, mã đang ghim, pointer capture, bàn phím và retry.
- `membership-before.log`: ca lỗi bổ sung được tái hiện trước khi sửa.
- `unit.log`, `heatmap-tests.log`, `lint.log`, `css.log`, `build.log`, `local-build.log`: kiểm tra source/build.
- `desktop-dark.png`, `map-desktop-dark.png`, `desktop-light.png`, `width-768.png`, `width-390.png`, `width-320.png`, `current-session.png`: ảnh Chromium đã kiểm tra.
- `live-assets.json`: đối chiếu entry localhost:8000 với build đã QA.

QA cổng 5193 đã dừng; credential QA và thư mục DB tạm được đối chiếu session trước khi xóa.

## Ranh giới kiểm chứng

Browser chạy build thật, worker thật và auth/DB tạm trên cổng 5193. Dữ liệu heatmap lấy từ snapshot công khai đã lưu (874 mã đủ điều kiện trong 1.521 mã) và snapshot đọc từ localhost lúc09:13 ngày 03/11 (176/1.521); kiểm thử tạo các cập nhật có kiểm soát trên bản sao. Không thay báo giá/DB người dùng. Các chỉ số/lịch sử ngoài heatmap được stub trong QA, nên ảnh QA không chứng minh giá/chỉ số toàn thị trường hiện tại.

Diện tích phản ánh tỷ trọng thực: tăng GTGD một mã làm thay tổng, nên các đường biên dùng chung có thể dịch chuyển. Giữ thứ tự và co giãn liên tục, không cố định sai diện tích các ngành khác. Những thay đổi cấu trúc trong cùng một ngành có thể sắp xếp lại ngành đó. Khi đổi sàn/metric, resize khung hoặc mã ghim biến mất, có thể phải dựng lại phạm vi/góc nhìn.

Đã thử Chromium ở desktop và kích thước mobile; chưa chứng nhận Safari/iOS vật lý hoặc tải nhiều tab dài hạn. ESLint có một warning cũ ở Social `useSocialFeed.js`; không thêm lỗi lint trong phạm vi này.
