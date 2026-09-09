# ADR-002: Agentic Core Contracts Freeze & Invariants

- Status: Accepted
- Date: 2026-09-09

## Context

Module `agentic_core` đóng vai trò là product-level control plane cho toàn bộ conversational và embedded agent trong hệ thống Agentic Quantum (`00_AGENTIC_CORE_PLAN.md`). Để ngăn chặn hiện tượng trôi dạt lược đồ dữ liệu (schema drift), rủi ro IDOR và leo thang đặc quyền (privilege escalation), toàn bộ các hợp đồng trao đổi dữ liệu (root contracts) giữa các node trong graph, persistence layer và public API cần được đóng băng (freeze) và xác lập các bất biến bảo mật (security invariants).

## Decision

1. **Đóng băng 8 Root Contracts ở phiên bản `1.0.0`:**
   - `TrustedExecutionEnvelope` & `ExecutionBudget` (`schemas/envelope.py`)
   - `AgentRun`, `AgentStep`, `ToolCallRecord` (`schemas/runs.py`)
   - `AgentArtifact` (`schemas/artifact.py`)
   - `ActionProposal` (`schemas/artifact.py`)
   - `ActionReceipt` (`schemas/artifact.py`)
   - `MemoryProposal` (`schemas/memory.py`)
   - `Claim`, `ReviewedClaim`, `ClaimLedger`, `ReviewedArtifact` (`schemas/claim.py`)
   - `AgentRunRequestV1`, `AgentRunResponseV1` (`schemas/requests.py`)

2. **Ràng buộc Immutability và Strict Validation:**
   - Toàn bộ schema sử dụng Pydantic v2 với cấu hình bắt buộc: `ConfigDict(extra="forbid", frozen=True)`.
   - Mọi model đều mang trường nhận diện phiên bản bất biến: `schema_version: str = "1.0.0"`.

3. **Bất biến Thẩm quyền (Authority Invariant):**
   - Client tuyệt đối **không** được truyền `account_id`, `scopes`, memory namespace hoặc `allowed_capabilities` dưới dạng authority trong request payload.
   - Server runtime chịu trách nhiệm giải quyết danh tính duy nhất thông qua `AuthPrincipal` từ session xác thực hợp lệ (`modules/auth`), sau đó đóng gói thành `TrustedExecutionEnvelope` trước khi tiến vào graph execution.

4. **Chốt 3 Quyết định Kỹ thuật Mở (Open Decisions §12):**
   - **Xác nhận hành động (Action Confirmation):** Sử dụng cơ chế `idempotency-key` kết hợp `re-authentication` và kiểm tra quyền sở hữu trên resource target thay vì dùng one-time token.
   - **Làm mới Feature Flag:** Sử dụng cơ chế polling với chu kỳ làm mới `<= 30s` (đọc biến môi trường trực tiếp qua `FeatureFlagService.is_enabled()`).
   - **Chính sách Retention:** Tách riêng retention policy theo từng `memory_type` (`preference`, `goal`, `plan`, `mastery`, `misconception`).
   - **Giá trị TTL ngày cụ thể:** Ghi nhận trạng thái "Chờ Product và Compliance phê duyệt"; hệ thống hỗ trợ cấu hình động qua biến môi trường `RISK_AGENTIC__RETENTION__<TYPE>`, giá trị mặc định là `None` (lưu giữ an toàn không tự xóa trước khi có văn bản phê duyệt chính thức).

## Consequences

- Các node trong LangGraph và API endpoints bắt buộc phải tuân thủ nghiêm ngặt định dạng schema, mọi payload chứa trường lạ sẽ bị từ chối ngay tại biên (fail-closed).
- Kiểm thử tự động sẽ khóa chặt cấu trúc schema (`tests/test_agentic_core_schemas.py`). Mọi thay đổi schema sau thời điểm này đều phải tạo phiên bản kế thừa (additive versioning) chứ không được sửa đè v1.0.0.

## Rollback

Revert tài liệu này và khôi phục trạng thái schema linh hoạt nếu kiến trúc có thay đổi chiến lược lớn được phê duyệt bởi Tech Lead.
