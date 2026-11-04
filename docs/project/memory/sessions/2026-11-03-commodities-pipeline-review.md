# 2026-11-03 · Review logic/pipeline Hàng hoá

**superseded: CP-01–09 đã được sửa và kiểm chứng trong [lượt sửa mã nguồn](2026-11-03-commodities-pipeline-fixes.md).** Nội dung bên dưới giữ bằng chứng tại thời điểm review trước sửa.

**verified review tại thời điểm ghi nhận.** Người dùng yêu cầu review logic và data pipeline sau chỉnh chart/UI. Phạm vi commodity frontend + shared global feed/history, storage/API/scheduler; không review toàn dự án.

Xác nhận 9 finding: CP-01 giá tham chiếu lệch ngày UTC/sàn; CP-02 yfinance1.2.0 shared state lẫn history concurrent; CP-03 partial snapshot làm mất mã; CP-04 crypto/global as_of và DB fallback làm giá cũ trông mới; CP-05 chart không polling cùng quotes; CP-06 manual refresh không bypass backend; CP-07 lỗi refresh xoá chart cũ; CP-08 high/low chỉ lấy nến5m cuối; CP-09 cacheRAM không scope theo directory. 4P1/4P2/1P3, **chưa sửa**.

[Report bằng chứng, vị trí code, hướng sửa và lệnh chạy lại](../../qa/results/COMMODITIES_PIPELINE_REVIEW_2026_11_03.md).

25 existing tests đạt (10frontend/15backend), build đạt; 11 backend observations và4 Chromium reproductions, 0pageerrors. Public provider trả3quotes và65dailybars/mã XAU/WTI/CORN. Lần raw timestamp probe có lỗi cache yfinance `database is locked` cho dailyCORN; intraday/history vẫn có, đã ghi giới hạn. Không đánh đồng test pass với các finding đã sửa hoặc nguồn realtime ổn định.

Thêm3script trong scripts/qa: review-commodities-pipeline.py, review-commodities-browser.mjs, probe-commodities-provider.py. Chỉ QA/docs đổi trong lượt này, app source giữ nguyên. DB/cache tạm, QA5191 dừng và session credential xoá; không resetDB live/restart8000/deploy. Staged SHA256 giữ nguyên theo report.
