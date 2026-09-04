# Changelog — Module 8: Market & Paper Portfolio Agent

Tất cả các thay đổi kiến trúc và mã nguồn của Module 8: Market & Paper Portfolio Agent được theo dõi và ghi nhận tại đây theo chuẩn Semantic Versioning và tuân thủ các Work Packages (MP0 – MP7).

---

## [1.0.0-mp7] - 2026-09-04 — Work Package MP7: Production Rollout & Operations Runbook

### Added
- **Cohort Percentage Gating**: Thuật toán phân bổ người dùng tất định bằng hàm băm SHA-256 trên `account_id`, hỗ trợ các tỷ lệ mở rộng dần `0% → 5% → 25% → 100%` qua cờ `RISK_FLAG__MODULE__MARKET_PORTFOLIO__AGENT__COHORT_PERCENTAGE`.
- **Internal Allowlist Bypass**: Hỗ trợ danh sách tài khoản nội bộ thử nghiệm `COHORT_ALLOWLIST` qua biến môi trường `RISK_FLAG__MODULE__MARKET_PORTFOLIO__AGENT__COHORT_ALLOWLIST`.
- **Ops Telemetry Endpoint**: Thêm route `GET /api/v1/market-portfolio/agent/ops/rollout-status` cung cấp thông tin trạng thái triển khai, các ngưỡng SLA §9, chính sách TTL và trạng thái phụ thuộc.
- **Rollout Schemas**: Định nghĩa `RolloutStatusV1` và `SlaThresholdsV1` với `StrictModel(extra="forbid")` trong `schemas/rollout.py`.
- **Rollout Runbook**: Biên soạn tài liệu vận hành chi tiết `docs/project/agentic-quantum/08_MP7_ROLLOUT_RUNBOOK.md` bao gồm 4 checklist phê duyệt, quy trình kill-switch $\le 30$ giây và ma trận giám sát.
- **Automated Rollout Test Suite**: Thêm `tests/test_market_portfolio_rollout.py` kiểm chứng toàn bộ hành vi bật/tắt cờ, phân nhóm cohort, bypass allowlist và tính độc lập của API REST legacy.

---

## [1.0.0-mp6] - 2026-09-03 — Work Package MP6: Security Audit, Local Review & Verification

### Fixed & Hardened (Phản hồi Review Vòng 1 & Vòng 2)
- **F1 (Zero Fabricated Data)**: Xóa bỏ hoàn toàn chỉ số thị trường fallback giả lập; feed rỗng lập tức trả về lỗi rõ ràng thay vì suy diễn.
- **F2 (Fail-closed Scope)**: Chuyển guard kiểm tra scope sang fail-closed (`account:market_portfolio:read`); tự động gán mặc định cho session đăng nhập thực tế.
- **F3 (Reviewer 1-Turn Repair Loop)**: Thiết lập quy trình sửa đổi 1 vòng khi reviewer trả về "repair", chỉ cho phép phát hành khi cả hai reviewer đánh giá "pass", nếu không sẽ block narrative.
- **F4 (Dynamic Freshness)**: Tính toán tuổi dữ liệu động (`age_seconds`), tự động phát hiện trạng thái `stale` khi quá TTL; suy luận phiên giao dịch HOSE thời gian thực theo giờ ICT.
- **F5 (Pure Decimal Arithmetic)**: Chuẩn hóa toàn bộ số học tiền tệ và định giá danh mục sang `Decimal` với `ROUND_HALF_UP` ngay tại ranh giới dữ liệu.
- **F6 & F7 (Reviewer Thresholds)**: Siết chặt ngưỡng sai lệch số lượng về `0`; yêu cầu chỉ báo danh mục mô phỏng rõ ràng ("paper", "mô phỏng", "giả lập", "học tập").
- **F8 & F9 (IDOR & Strict Models)**: Loại bỏ alias `"default"`; chuyển đổi `ToolContext` sang `StrictModel(extra="forbid")`.
- **F10 & F11 (Code Quality & Exception Handling)**: Thay thế toàn bộ `assert` bằng exception rõ ràng; không bắt `SystemExit` hay exception rộng.
- **F12 & F13 (DI & Mutation Spies)**: Dependency injection cho agent service; bảo đảm tính bất biến bằng hàm băm SHA-256 toàn bộ các bảng `mp_*`.
- **F14 & F15 (Zero Dead Code)**: Loại bỏ skill không sử dụng và các import thừa.

---

## [1.0.0-mp5] - 2026-09-03 — Work Package MP5: REST Endpoints & Service Wiring

### Added
- Endpoint bắt đầu đánh giá: `POST /api/v1/market-portfolio/agent/reviews`
- Endpoint truy vấn artifact: `GET /api/v1/market-portfolio/agent/reviews/{artifact_id}`
- Tích hợp bảo vệ cờ tính năng `module.market_portfolio.agent.enabled` (mặc định tắt an toàn).
- Đảm bảo 100% tương thích ngược với các endpoint `/portfolio` và `/watchlist` cũ.

---

## [1.0.0-mp4] - 2026-09-03 — Work Package MP4: Artifact Repository & Retention

### Added
- Bảng cơ sở dữ liệu `mp_agent_artifacts` lưu trữ artifact đánh giá.
- Cơ chế idempotency đảm bảo cùng một yêu cầu không bị tạo trùng lặp.
- Chính sách lưu trữ tạm thời phi bền vững (TTL 24 giờ) và phương thức `purge_expired()`.

---

## [1.0.0-mp3] - 2026-09-03 — Work Package MP3: Skills, Reviewers & LLM Provider Integration

### Added
- Bốn kỹ năng giải thích: `market.context_explainer.v1`, `portfolio.exposure_review.v1`, `portfolio.scenario_walkthrough.v1`, `portfolio.paper_fill_explainer.v1`.
- Ba reviewer độc lập: `NumericReviewer`, `EvidenceReviewer`, `SafetyReviewer`.
- Tích hợp chuẩn hóa qua `LLMProvider` với fallback an toàn khi mất kết nối mạng.

---

## [1.0.0-mp2] - 2026-09-03 — Work Package MP2: Read-Only Tools & Deterministic Math

### Added
- Năm công cụ đọc dữ liệu: `market.get_snapshot.v1`, `portfolio.get_snapshot.v1`, `portfolio.get_exposure.v1`, `portfolio.run_scenario.v1`, `portfolio.explain_fill.v1`.
- Tính toán độ tập trung danh mục HHI và tỷ trọng vị thế xác định.
- Mô hình sốc giá tất định không qua LLM.
- Danh mục cấm triệt để mọi hành vi mutation (`place_order`, `cancel_order`, `reset_portfolio`, v.v.).

---

## [1.0.0-mp1] - 2026-09-03 — Work Package MP1: Identity, Authority & Zero-IDOR Policy

### Added
- Kiểm tra quyền sở hữu danh mục và lệnh giao dịch gắn chặt với `AuthPrincipal`.
- Mã lỗi 404 non-disclosing khi cố gắng truy cập dữ liệu của tài khoản khác.

---

## [1.0.0-mp0] - 2026-09-03 — Work Package MP0: Strict Contracts & Schemas

### Added
- Đóng gói toàn bộ schema vào package `schemas/` với `SCHEMA_VERSION = "1.0.0"`.
- Toàn bộ model thừa kế `StrictModel(extra="forbid")`.
- Tương thích ngược với các import cũ từ module cha.

