# Review trang Tin tức — 01/11/2026

> **02/11/2026 — superseded về trạng thái chưa sửa:** NR-01–NR-07 đã có [bản sửa và kiểm chứng](2026-11-02-news-fixes.md). Nội dung dưới đây giữ lại bằng chứng tại thời điểm review.

**Status: verified — review, chưa sửa implementation.** User yêu cầu review `http://localhost:8000/dashboard-static/news`.

- [Báo cáo](../../qa/results/NEWS_REVIEW_2026_11_01.md) ghi 7 lỗi đã tái hiện/đối chiếu source: bỏ dấu khiến “đầu” khớp “dầu”; sắc thái chỉ có từ điển tiếng Anh (370/370 tin VN neutral trong snapshot); lọc importance sau cắt 80; Xem thêm chỉ mở mảng local; concept link bị bỏ qua; stale metadata không hiển thị; không tự refresh khi mở lâu.
- UX: highlights độc lập bộ lọc nhưng chưa nói rõ phạm vi; panel advanced không đóng khi có điều kiện; Dòng tin bắt đầu y1241 desktop/y1689 mobile.
- Chromium thực tế trên cổng8000; session QA, auth/analytics mock, API tin thật. Cổng bị sandbox chặn ban đầu, truy cập ngoài sandbox được HTTP200. Không phải lỗi server.
- Probe API dùng bản sao 710 news rows và 3 bảng hỗ trợ từ connection read-only sang DB tạm, refresh tắt; 28 existing backend tests đạt qua runner cô lập. Build riêng `/private/tmp/northstar-news-review-dist` đạt. Browser ca tổng hợp có timeout automation; các ca tách có bằng chứng riêng, không báo toàn bộ suite browser pass.
- Sources: `features/news/pages/NewsPage.jsx`, `NewsFilters.jsx`, `NewsArticleReader.jsx`; backend `news_intelligence/application/services.py`, `enrichment.py`, `domain/text.py`. Evidence trong `output/{qa,playwright}/news-review/` và report test `output/qa/isolated-tests/20261101T164116Z-f5fdc4a8/report.json`.
- Không sửa sản phẩm, không reset DB thật, không deploy/push. Các hướng sửa trong report là **proposed**; không coi review là đã khắc phục.
