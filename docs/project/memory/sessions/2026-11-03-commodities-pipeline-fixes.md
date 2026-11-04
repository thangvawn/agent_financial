# 2026-11-03 · Sửa logic/data pipeline Hàng hoá

**verified trên source/QA.** Người dùng yêu cầu sửa mã nguồn sau review. Đã xử lý CP-01–CP-09: daily reference theo timezone, khoá Yahoo download chung với backtest/single-flight, merge partial theo mã, timestamp/freshness riêng từng quote và SQLite fallback, polling main/mini, force refresh xuyên API có throttle, giữ chart khi lỗi, extrema theo exchange_day, cache RAM theo directory và namespace history v2.

[Report thay đổi, bằng chứng, lệnh kiểm chứng và giới hạn](../../qa/results/COMMODITIES_PIPELINE_FIXES_2026_11_03.md). [Review trước đó](2026-11-03-commodities-pipeline-review.md) là trạng thái lịch sử đã được xử lý.

40 backend/183 frontend/11 nhóm Chromium đạt; CSS57/build đạt, ESLint0 lỗi/1 warning Social cũ. Source thật XAU/WTI/CORN trả3quotes và65bars/mã, không còn cảnh báo cache lock trong lần probe. Browser kiểm chứng API/auth/DB thật trên môi trường cô lập với provider fixture; xem ảnh desktop/mobile. Bản sửa reference=null cũng được xử lý trong market pulse; fixture GTGD test_data_hub đổi sang raw VND đúng contract đang có.

Không coi daily close là official settlement; exchange_day không phải phiên futures chuẩn/rolling24h. Chưa có lịch nghỉ thị trường hoặc soak/load test đa worker. Khoá/rate limit trong process; cache v2 tải lại lần đầu. Chưa restart8000/deploy/push. Server QA5192 đã dừng, session/temp DB/cache đã xoá. Staging116files giữ nguyên theo report.
