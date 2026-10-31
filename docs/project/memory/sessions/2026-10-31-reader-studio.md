# 2026-10-31 · Reader studio với Three.js

**Status: verified trên workspace.** Theo yêu cầu mới, thiết kế lại đúng màn đọc PDF + ghi chú trong ảnh; không redesign toàn bộ Learn Hub.

- `ReaderChrome`, `BookReaderWorkspace`, `reader-studio.css`: nền graphite/sage, khung PDF và giấy nổi, toolbar thống nhất, Sách / Song song / Ghi chú. Desktop mặc định split; mobile từng khung, giữ state khi đổi chế độ.
- `ReaderDeskScene` tải `readerDeskEngine` khi bật 3D. Hai sách dựng bằng Three.js/RoundedBoxGeometry, ánh sáng/bóng và pointer easing; không loop vô hạn, DPR cap 1,5, reduced motion, fallback khi không WebGL/context loss và cleanup GPU. Dùng dependency Three.js có sẵn.
- `ReaderSplitPane`: 28–72%, mặc định 56%; hỗ trợ keyboard/ARIA, localStorage an toàn. `PdfBookPane`: FitH và navpanes=0; trang đọc vẫn lưu thủ công qua kệ sách.
- Verified: 134 frontend unit, ESLint, 51 CSS files, Vite build, 9 browser reader + 12 browser personal-library; không page error. Đã xem ảnh desktop/mobile. [Báo cáo, lệnh và giới hạn](../../qa/results/READER_STUDIO_2026_10_31.md).
- QA dùng DB/files tạm. Không reset/khôi phục DB mặc định; sự cố cũ vẫn unresolved. Không push/deploy. Staged hash 116 mục sẵn có được giữ nguyên.
- `BookDocumentPane.jsx` đã dirty và `PdfBookPane.jsx` đã untracked trước task; thay đổi wrapper heading/fragment PDF của lượt này còn trong workspace cùng nền cũ. Checkpoint UI không gom các file nền đó; không coi checkpoint riêng là snapshot deploy được.
