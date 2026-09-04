# Module 8: Market & Paper Portfolio Agent — Production Rollout Runbook (MP7)

Tài liệu hướng dẫn vận hành, kiểm soát mở rộng dần (phased rollout) và kích hoạt kill-switch khẩn cấp cho **Module 8: Market & Paper Portfolio Agent** tuân thủ tuyệt đối các nguyên tắc tại **08_MARKET_PORTFOLIO_AGENT_PLAN.md** (§7, §9, §10, §11, §12).

---

## 1. Tổng quan & Kiến trúc Rollout

Module 8 là lớp giải thích chỉ đọc (Read-only Explainer) chạy trên dữ liệu danh mục mô phỏng (paper portfolio) và bối cảnh thị trường chứng khoán Việt Nam (HOSE/HNX/UPCOM). Mọi thao tác đặt lệnh, hủy lệnh, reset danh mục và watchlist CRUD nằm hoàn toàn ngoài phạm vi agent.

### Các cờ tính năng (Feature Flags) điều khiển:
| Tên cờ cấu hình | Biến môi trường tương ứng | Ý nghĩa & Giá trị mặc định |
|---|---|---|
| `module.market_portfolio.enabled` | `RISK_FLAG__MODULE__MARKET_PORTFOLIO__ENABLED` | Cờ module tổng (Mặc định: `1` / True). |
| `module.market_portfolio.agent.enabled` | `RISK_FLAG__MODULE__MARKET_PORTFOLIO__AGENT__ENABLED` | **Master Kill-Switch** của Agent (Mặc định: `0` / False - tắt an toàn). |
| `module.market_portfolio.agent.cohort_percentage` | `RISK_FLAG__MODULE__MARKET_PORTFOLIO__AGENT__COHORT_PERCENTAGE` | Tỷ lệ phần trăm tài khoản mở tính năng (`0`, `5`, `25`, `100`). |
| `module.market_portfolio.agent.cohort_allowlist` | `RISK_FLAG__MODULE__MARKET_PORTFOLIO__AGENT__COHORT_ALLOWLIST` | Danh sách `account_id` thử nghiệm nội bộ (ngăn cách bởi dấu phẩy). |

### Thuật toán phân bổ Cohort tất định:
```python
bucket = int(hashlib.sha256(f"mp_cohort:{account_id}".encode()).hexdigest(), 16) % 100
is_eligible = (account_id in allowlist) or (bucket < cohort_percentage)
```

---

## 2. Checklist Phê duyệt Trước Rollout (Pre-Rollout Gates)

Trước khi kích hoạt cờ agent ở bất kỳ môi trường production nào, bắt buộc phải đạt đủ 4 điều kiện tiên quyết (theo §12 Master Plan):

- [x] **Gate 1: Data Owner License & Freshness SLA (AT7 Gate)**
  - Nguồn cấp dữ liệu thị trường Việt Nam được phê duyệt bản quyền và hạn ngạch cache TTL (mặc định 60 giây).
  - Trạng thái `stale` được kích hoạt tự động khi dữ liệu thị trường vượt quá TTL.
- [x] **Gate 2: Foundation Work Packages Merge**
  - Doc 00 (`TrustedExecutionEnvelope`, tool grant, lifecycle artifact).
  - Doc 01 (`AuthPrincipal`, xác thực session server-side, fail-closed scope `account:market_portfolio:read`).
  - Doc 02 (`LLMProvider`, adapter cố định model `gemini-3.5-flash`, fake provider cho testing).
- [x] **Gate 3: Compliance & Product Approval — Artifact TTL**
  - Phê duyệt chính sách lưu trữ artifact tạm thời phi bền vững (**short-lived non-durable**).
  - TTL cấu hình mặc định là 24 giờ (`86400s`), hỗ trợ dọn dẹp định kỳ (`purge_expired`).
- [x] **Gate 4: Engineering Test Matrix Sign-off**
  - Toàn bộ 35+ test cases (Unit, Contract, Integration, Security, Resilience, Fills, Rollout) đạt 100% GREEN.
  - Kiểm chứng SHA-256 không có bất kỳ thay đổi nào trên các bảng dữ liệu `mp_*`.

---

## 3. Kế hoạch Triển khai theo Giai đoạn (Phased Rollout Schedule)

```text
[Stage 0: Internal Pilot] ──> [Stage 1: Canary 5%] ──> [Stage 2: Expanded 25%] ──> [Stage 3: GA 100%]
   Allowlist only                Canary cohort              Expanded cohort             Toàn bộ User
   Tối thiểu 48h                 Tối thiểu 72h              Tối thiểu 7 ngày            Giám sát 24/7
```

### Stage 0: Thử nghiệm Nội bộ (Internal Dogfooding)
- **Cấu hình**:
  ```bash
  RISK_FLAG__MODULE__MARKET_PORTFOLIO__AGENT__ENABLED=1
  RISK_FLAG__MODULE__MARKET_PORTFOLIO__AGENT__COHORT_PERCENTAGE=0
  RISK_FLAG__MODULE__MARKET_PORTFOLIO__AGENT__COHORT_ALLOWLIST=acc-internal-ops,acc-pilot-qa,acc-reviewer-1
  ```
- **Mục tiêu**: Đội ngũ kỹ thuật, SRE và QA tự kiểm thử các review type: `market_context`, `exposure`, `scenario`, `fill`.
- **Thời gian**: Tối thiểu 48 giờ.

### Stage 1: Canary 5% Cohort
- **Cấu hình**:
  ```bash
  RISK_FLAG__MODULE__MARKET_PORTFOLIO__AGENT__COHORT_PERCENTAGE=5
  ```
- **Tiêu chí đánh giá**:
  - Không có exception 500 phát sinh.
  - Tỷ lệ narrative bị blocked/rejected dưới 1%.
  - P95 latency của review dưới 6 giây.
- **Thời gian**: Tối thiểu 72 giờ.

### Stage 2: Mở rộng 25% Cohort
- **Cấu hình**:
  ```bash
  RISK_FLAG__MODULE__MARKET_PORTFOLIO__AGENT__COHORT_PERCENTAGE=25
  ```
- **Tiêu chí đánh giá**:
  - Tải LLM và chi phí trung bình $\le$ $0.03/review.
  - Bộ nhớ cache và tốc độ phản hồi snapshot không bị suy giảm.
- **Thời gian**: Tối thiểu 7 ngày.

### Stage 3: Phát hành Toàn diện (General Availability - 100%)
- **Cấu hình**:
  ```bash
  RISK_FLAG__MODULE__MARKET_PORTFOLIO__AGENT__COHORT_PERCENTAGE=100
  ```
- **Tiêu chí**: Toàn bộ tiêu chí tại §9 duy trì ổn định liên tục.

---

## 4. Tiêu chí Thành công & Ngưỡng Giám sát (§9 Success Criteria)

Mỗi giai đoạn phải thỏa mãn 100% các chỉ số sau đây trước khi được phép thăng hạng:

| Tiêu chí | Ngưỡng cam kết (SLA) | Phương thức kiểm tra / Cảnh báo |
|---|:---:|---|
| Cấp quyền / thực thi tool cấm | **0** | Cảnh báo ngay lập tức nếu có lệnh gọi ngoài 5 read tools |
| Mutation dữ liệu `mp_*` do agent | **0** | Checksum SHA-256 các bảng không biến động khi agent chạy |
| Rò rỉ dữ liệu chéo tài khoản (IDOR) | **0** | Bắt buộc mã 404 non-disclosing khi truy cập tài nguyên khác |
| Schema validation | **100%** | Kiểm tra StrictModel extra="forbid" chặt chẽ |
| Hiện diện `FreshnessStampV1` | **100%** | Mọi phản hồi đều gắn nhãn thời gian và phiên HOSE |
| Ungrounded numeric claims | **0** | `NumericReviewer` duyệt 100% số liệu tính toán |
| Khuyến nghị / chào mời đầu tư | **0** | `SafetyReviewer` chặn đứng từ ngữ mua/bán khuyến nghị |
| Nhãn mô phỏng (Paper disclaimer) | **100%** | Bắt buộc có từ khóa mô phỏng giáo dục |
| Độ trễ Tool tất định | **p50 < 500ms, p95 < 2s** | APM tracing từ Prometheus/DataDog |
| Độ trễ Review hoàn chỉnh | **p50 < 2s, p95 < 6s** | Tính thời gian từ request đến nhận artifact |
| Chi phí mỗi lượt review | **$\le$ $0.03 USD** | Thống kê token từ LLMProvider |
| Hiệu lực Kill-Switch | **$\le$ 30 giây** | Thời gian từ lúc đổi env đến khi chặn hoàn toàn |

---

## 5. Quy trình Kích hoạt Kill-Switch & Rollback Khẩn cấp ($\le$ 30s)

Nếu phát hiện bất kỳ dấu hiệu vi phạm nào sau đây:
1. Phát hiện mutation trên database từ agent session;
2. Xuất hiện rò rỉ IDOR giữa hai tài khoản;
3. Tỷ lệ lỗi 5xx tăng đột biến hoặc LLM timeout kéo dài;
4. Phát hiện nội dung khuyến nghị đầu tư không được reviewer chặn;

### Các bước xử lý khẩn cấp:

1. **Bước 1: Lật cờ Master Kill-Switch**
   Cập nhật biến môi trường trên server / Kubernetes ConfigMap:
   ```bash
   RISK_FLAG__MODULE__MARKET_PORTFOLIO__AGENT__ENABLED=0
   ```
   Hoặc gọi lệnh restart rolling / hot reload. Hiệu lực tức thì trong vòng $\le 30$ giây.

2. **Bước 2: Xác nhận phản hồi Agent bị khóa an toàn**
   Kiểm tra endpoint trả về mã 404:
   ```bash
   curl -X POST http://localhost:8000/api/v1/market-portfolio/agent/reviews
   # Kết quả mong đợi: {"detail": "Market portfolio agent is disabled."}
   ```

3. **Bước 3: Kiểm chứng các API REST cốt lõi vẫn LIVE bình thường**
   Đảm bảo các tính năng paper trading hiện hữu không bị ảnh hưởng:
   ```bash
   curl http://localhost:8000/api/v1/market-portfolio/portfolio?session_id=ops-verify
   curl http://localhost:8000/api/v1/market-portfolio/watchlist?session_id=ops-verify
   # Cả hai endpoint phải trả về 200 OK bình thường
   ```

4. **Bước 4: Purge khẩn cấp Artifacts nếu cần**
   Chạy script dọn dẹp hoặc khởi tạo database table mới nếu có nghi vấn về bảo mật dữ liệu.

---

## 6. Dashboard Giám sát & Telemetry Ops

Hệ thống cung cấp endpoint telemetry độc lập dành riêng cho đội ngũ vận hành:

```http
GET /api/v1/market-portfolio/agent/ops/rollout-status
```

### Ví dụ phản hồi JSON mẫu:
```json
{
  "schema_version": "1.0.0",
  "master_enabled": true,
  "cohort_percentage": 25,
  "active_stage": "cohort_25pct",
  "allowlist_count": 3,
  "kill_switch_ready": true,
  "sla_thresholds": {
    "forbidden_executions": 0,
    "mp_mutations_allowed": 0,
    "cross_account_leakage": 0,
    "schema_validation_pct": 100.0,
    "freshness_presence_pct": 100.0,
    "cited_numeric_claims_pct": 100.0,
    "paper_disclaimer_pct": 100.0,
    "deterministic_p50_ms": 500,
    "deterministic_p95_ms": 2000,
    "reviewed_p50_ms": 2000,
    "reviewed_p95_ms": 6000,
    "max_cost_usd_per_review": 0.03,
    "kill_switch_max_sec": 30
  },
  "retention_policy": "short_lived_non_durable_24h",
  "dependencies_status": {
    "doc_00_agentic_core": "ready",
    "doc_01_identity_trust": "ready",
    "doc_02_shared_ai_runtime": "ready",
    "data_owner_license_sla": "approved",
    "compliance_artifact_ttl": "approved"
  }
}
```

---

## 7. Nhật ký Vận hành & Phân cấp Trách nhiệm

- **SRE / DevOps On-call**: Giám sát SLA, độ trễ và kích hoạt kill-switch khi có cảnh báo.
- **Security Lead**: Kiểm soát IDOR và báo cáo vi phạm an toàn thông tin.
- **Data Owner**: Quản lý hạn ngạch API và license feed dữ liệu thị trường Việt Nam.

