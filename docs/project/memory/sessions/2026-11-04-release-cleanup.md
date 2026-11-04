# Dọn mã và đầu ra QA cho bản bàn giao

- Ngày: 04/11/2026. Trạng thái: **verified trong phạm vi dưới đây**.
- Yêu cầu: dọn code/test cũ, chức năng không dùng và file đầu ra; không thêm chức năng.
- Xoá 99 file: 35 frontend (gồm 3 test chỉ dành cho UI cũ), 20 backend/helper/shim,
  40 script QA/probe dùng một lần, 3 ảnh QA cũ và 1 snapshot tạm. Dọn thêm hàm/API/icon,
  import, CSS và component cũ; bỏ Emotion/Query Devtools (3 dependency trực tiếp,
  npm prune bỏ 39 package). Giữ các màn và API hiện hành.
- Frontend bỏ toàn bộ UI screener/preset và overview cũ vốn không còn được hiển thị;
  giữ API screener/CLI backend và Tổng quan/heatmap hiện tại. 12 ca test chỉ phục vụ
  UI/helper cũ được bỏ; không xoá test của chức năng còn dùng.
- Bỏ theo dõi Git 282 file dependency/cache/SQLite sidecar/snapshot/manifest backup;
  thư viện và cache runtime vẫn nằm trên máy (manifest backup cũ đã xoá). Git trước
  phiên sạch; không có staging người dùng bị thay. Chưa commit/push/deploy.
- Dọn 23.026 file đầu ra/cache/backup sinh tự động, tổng 1.370,19 MiB (~1,34 GiB).
  Không xoá DB người dùng, model, tài liệu thư viện hoặc frontend/dist đang có.
- `.gitignore` chặn node_modules mọi cấp, SQLite WAL/SHM, snapshot tạm và báo cáo test.
  `.dockerignore` loại QA/output/tooling/secret khỏi build context. `make test` dùng
  runner DB tạm; `make clean` dọn QA/cache, không quét vào virtualenv hoặc data.
- Giữ `risk_dashboard.quant.xgb_engine` và namespace cha: pickle model hiện có
  tham chiếu đường dẫn này. Thử bỏ gây 9 lỗi hồi quy; khôi phục đúng shim thì cả
  128 ca đạt. Các shim quant khác không còn caller đã bỏ; notebook dùng `engines.quant`.
- Đã chạy: 180 frontend unit (baseline 192, bỏ 12 ca obsolete); 128 backend trong
  `tests/modules/{legacy_gate,quant_research}` và 6 file AI tutor/runtime/registry/
  portfolio; 5 test CLI isolated runner. ESLint 0 lỗi/0 cảnh báo, CSS 54 file đạt,
  Vite production build và Python wheel đạt. Wheel có shim pickle, không có tests/
  scripts/output/node_modules. Graph JS/TS/CSS còn 293 file, không có file ngoài
  đường dẫn app/test đã phân tích; đây không phải chứng minh mọi symbol đều cần dùng.
- Chromium: đăng nhập API thật trên DB tạm; Market 1440×1000 và 390×844, 853 ô
  heatmap từ bản sao quote thật, zoom/reset, tab cổ phiếu/hàng hoá, sáng/tối;
  Learn/News/Social/BCTC/Simulation render được, không pageerror hoặc tràn ngang mobile.
  Provider ngoài dùng fixture/503; chưa kiểm chứng nguồn live, mọi API/backend test,
  Safari/iOS hoặc Docker image build. Không suy ra toàn dự án production-ready.
- Log/ảnh/script kiểm chứng mới đặt ngoài repo tại `/private/tmp/northstar-cleanup-20261104/`;
  `backend-final.log`, `frontend-final.log`, `lint.log`, `css.log`, `build.log`,
  `wheel.log`, `browser-report.json`, `market-desktop.png`, `market-mobile-light.png`.
  Output QA và script trong các hồ sơ lịch sử đã được xoá theo yêu cầu, có thể xem lại
  source qua Git; không coi liên kết output lịch sử là artifact còn trên máy.
- Notion không có tool trong phiên này; bản ghi được lưu trong repository, chưa lưu Notion.
