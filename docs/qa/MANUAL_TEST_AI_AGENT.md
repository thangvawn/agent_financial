# Kịch Bản Kiểm Thử Thủ Công (Manual Test Plan) - Agentic Quantum System

Tài liệu này hướng dẫn QA/Manual Tester cách khởi chạy dự án và các bước chi tiết để kiểm thử hệ thống AI Agent (Agentic Quantum) từ End-to-End.

---

## 1. Hướng Dẫn Khởi Chạy (Setup Instructions)

### Bước 1: Cấu hình API Key
Mở file `.env` tại thư mục gốc, đảm bảo bạn đã điền `GEMINI_API_KEY`:
```env
# === AI Runtime (Agentic Quantum) ===
AI_PROVIDER=google
AI_MODEL=gemini-3.5-flash
AI_FALLBACK_ENABLED=0
GEMINI_API_KEY=AIzaSy... (điền key thật vào đây)
```

### Bước 2: Khởi động Backend (FastAPI)
Mở Terminal 1 tại thư mục gốc của dự án:
```bash
source .venv/bin/activate
PYTHONPATH=src uvicorn risk_dashboard.api.main:app --reload --port 8000
```
*Backend sẽ chạy tại: `http://127.0.0.1:8000` (Swagger UI: `http://127.0.0.1:8000/docs`)*

### Bước 3: Khởi động Frontend (React/Vite)
Mở Terminal 2, di chuyển vào `frontend`:
```bash
cd frontend
npm install  # (Chỉ chạy lần đầu nếu chưa cài)
npm run dev
```
*Frontend sẽ chạy tại: `http://localhost:5173`*

---

## 2. Kịch Bản Kiểm Thử (Test Cases)

### Kịch Bản 1: API Agent Run - Happy Path (Swagger UI)
**Mục tiêu:** Kiểm tra Graph Orchestrator (Backend) có thể xử lý một request hợp lệ, gọi Gemini AI và trả về kết quả đúng định dạng.
* **Bước thực hiện:**
  1. Mở `http://127.0.0.1:8000/docs`
  2. Tìm endpoint `POST /api/v1/public/agentic/runs` -> Nhấn **Try it out**
  3. Nhập Payload JSON mẫu:
     ```json
     {
       "task_type": "analysis",
       "prompt": "Tóm tắt thị trường chứng khoán VN-Index.",
       "budget": {
         "max_steps": 5,
         "max_tool_calls": 3
       }
     }
     ```
  4. Nhấn **Execute**.
* **Kết quả mong đợi:** 
  - HTTP Code 200/202.
  - JSON Response trả về chứa `run_id` và `status` (e.g. `"running"` hoặc `"completed"`).
  - Copy `run_id`.

### Kịch Bản 2: API Agent Polling (Swagger UI)
**Mục tiêu:** Kiểm tra endpoint lấy trạng thái Run.
* **Bước thực hiện:**
  1. Vào endpoint `GET /api/v1/public/agentic/runs/{run_id}`.
  2. Dán `run_id` vừa copy từ Kịch bản 1 vào tham số.
  3. Nhấn **Execute**.
* **Kết quả mong đợi:** 
  - Trả về status `"completed"` (nếu đã xong) hoặc `"running"`. 
  - Nếu `completed`, response sẽ bao gồm thông tin `artifact` với các trường như `artifact_type`, `claims`, `source_refs`.

### Kịch Bản 3: Giao diện (UI) - Agent Run Panel & Polling
**Mục tiêu:** Kiểm tra Frontend Component `<AgentRunPanel />` hiển thị đúng các trạng thái (Loading, Completed).
* **Bước thực hiện:**
  1. Mở trình duyệt `http://localhost:5173` (hoặc view có nhúng Agent Run Panel).
  2. Trigger một tác vụ AI (ví dụ: nhấn nút "Phân tích số liệu").
  3. Quan sát Component `<AgentRunPanel />`.
* **Kết quả mong đợi:** 
  - Component hiển thị trạng thái chuyển từ `IDLE` -> `RUNNING` (hiệu ứng loading).
  - Không bị giật/lag (polling thực hiện ngầm qua TanStack Query).
  - Khi API trả về `completed`, panel đổi sang màu xanh, hiển thị Artifact Card.

### Kịch Bản 4: Giao diện (UI) - Đọc Artifact & Evidence Drawer
**Mục tiêu:** Kiểm tra Drawer chứa bằng chứng số liệu và citation.
* **Bước thực hiện:**
  1. Tiếp tục từ kết quả của Kịch bản 3.
  2. Click vào thẻ Artifact Card (VD: thẻ "Analysis Result").
* **Kết quả mong đợi:**
  - Drawer `<EvidenceDrawer />` trượt từ cạnh phải màn hình mượt mà.
  - Hiển thị đầy đủ danh sách Claims (Luận điểm) và Sources (Nguồn trích dẫn).
  - Nhấn phím `Esc` hoặc nút (X) để đóng Drawer chính xác.

### Kịch Bản 5: Giao diện (UI) - Hủy tác vụ (Cancel Run)
**Mục tiêu:** Đảm bảo người dùng có thể ngắt kết nối/hủy task đang chạy.
* **Bước thực hiện:**
  1. Trigger một tác vụ AI trên giao diện.
  2. Ngay khi `<AgentRunPanel />` đang ở trạng thái `RUNNING`, nhấn nút **"Cancel"**.
* **Kết quả mong đợi:**
  - Hệ thống ngưng polling API.
  - Trạng thái Panel chuyển sang `CANCELED` hoặc quay về màn hình chờ.
  - Endpoint Backend `POST /.../runs/{run_id}:cancel` được gọi thành công.

### Kịch Bản 6: Chặn thực thi Action rủi ro (Risk Gating)
**Mục tiêu:** Đảm bảo hệ thống bắt người dùng xác nhận các Action thay đổi dữ liệu (`ActionProposal`).
* **Bước thực hiện:**
  1. Gọi AI thực hiện một tác vụ sửa/xóa dữ liệu hệ thống (VD: "Xóa checkpoint cũ").
  2. Quan sát giao diện (nơi gắn Component `<ActionProposalReview />`).
* **Kết quả mong đợi:**
  - Giao diện hiển thị form Review với Badge mức độ rủi ro (VD: `MEDIUM RISK` / `HIGH RISK`).
  - Nút Confirm bị vô hiệu hóa khi đồng hồ đếm ngược hết thời hạn (Timeout).
  - Nhấn "Reject", form đóng và task kết thúc với status báo rejected.
  - Nhấn "Confirm Action", gửi request `POST /.../action-proposals/{id}:confirm`, hệ thống thực thi.
