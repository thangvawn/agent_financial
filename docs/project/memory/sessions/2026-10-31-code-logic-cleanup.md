# Review logic và dọn file

- Date: 2026-10-31.
- Status: **verified** cho cleanup/test/reproduction; sửa các lỗi mới là **proposed**, chưa triển khai.
- Request: review logic/dự án hiện tại và loại file không dùng. Dọn 43 file frontend (30 tracked, 13 untracked), có ZIP/manifest SHA-256. Source graph 322 → 279 file; 279 còn lại reachable từ app/test. Giữ các shim có caller và runtime data.
- Findings: notebook theo session; BCTC stale scenario; portfolio agent tính PnL khi thiếu quote; lưu notebook lỗi/dirty status; reload BCTC; VaR UnboundLocalError; cache root dưới src/data. Chi tiết, source line và reproduction trong [report](../../qa/results/CODE_LOGIC_CLEANUP_2026_10_31.md).
- Verified: 148 frontend unit, 86 backend regression, ESLint/CSS50/build; Chromium 6 route smoke với unavailable fixtures và 6 probe UI; 3 backend characterization probes. Probe pass nghĩa tái hiện được bug, không phải đã fix. Ruff phạm vi còn 6 diagnostics, gồm một runtime bug.
- Isolation: backend runner dùng DB tạm; QA server có DB/assets/uploads riêng, lifecycle off, build tại `/private/tmp/northstar-review-20261031-dist`, không thay frontend/dist đang mount live. Không dùng hash DB live để suy ra an toàn. Không khôi phục dữ liệu lịch sử.
- Preserved staging fingerprint: `38f8fe1906f7dcd23ef9f97d84a7bab92051ebf08cc60ac7bc90a6bcd21d41ec`; không stage/commit/push/deploy.
- Remaining: ưu tiên owner ổn định, chặn response lỗi thời và thống nhất missing-value contract giữa service/agent; sau đó storage/reload/VaR/cache. Chưa chạy mọi backend test, provider live hoặc mọi trình duyệt.
