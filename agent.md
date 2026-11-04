---
name: financial-agent-lifecycle
description: Quy trình toàn diện (End-to-End Lifecycle) từ tiếp nhận mong muốn người dùng, phân tích nghiệp vụ tài chính, tuyển chọn Subagent & Tool, sinh code, review, tối ưu, test tự động, vòng lặp feedback sửa lỗi đến báo cáo hoàn thiện.
origin: Financial Engineering Architecture
version: 2.0.0
---

# Quy Trình Phát Triển Ứng Dụng Tài Chính Bằng Mạng Lưới Subagent (`agent.md`)

Tài liệu chuẩn mực hướng dẫn **Full Stack AI Engineer** và **Hệ thống Multi-Agent** vận hành một chu trình phát triển phần mềm tài chính tự trị khép kín, từ khâu tiếp nhận ý tưởng sơ khai đến khi xuất xưởng báo cáo nghiệm thu hoàn chỉnh.

---

## 1. Bản Đồ Tổng Quan Chu Trình 9 Giai Đoạn (End-to-End Lifecycle)

```
┌──────────────────────────────────────────────────────────────────────────────┐
│                    GIAI ĐOẠN 1: HIỂU MONG MUỐN NGƯỜI DÙNG                     │
│                (User Intent Discovery & Ambiguity Clarification)             │
└──────────────────────────────────────┬───────────────────────────────────────┘
                                       │
                                       ▼
┌──────────────────────────────────────────────────────────────────────────────┐
│                    GIAI ĐOẠN 2: PHÂN TÍCH NGHIỆP VỤ TÀI CHÍNH                │
│                 (Domain Logic, Data Contracts & Risk Bounds)                 │
└──────────────────────────────────────┬───────────────────────────────────────┘
                                       │
                                       ▼
┌──────────────────────────────────────────────────────────────────────────────┐
│                 GIAI ĐOẠN 3: TUYỂN CHỌN SUBAGENT & PHÂN QUYỀN TOOL           │
│                 (Subagent Matching, Tool Grants & Graph Routing)             │
└──────────────────────────────────────┬───────────────────────────────────────┘
                                       │
                                       ▼
┌──────────────────────────────────────────────────────────────────────────────┐
│                   GIAI ĐOẠN 4: THỰC THI MÃ NGUỒN (IMPLEMENTATION)            │
│                (Tracer Bullet, Strict Typing, Modular <200 lines)            │
└──────────────────────────────────────┬───────────────────────────────────────┘
                                       │
                                       ▼
┌──────────────────────────────────────────────────────────────────────────────┐
│                     GIAI ĐOẠN 5: RÀ SOÁT MÃ NGUỒN (CODE REVIEW)              │
│                (Architecture, Security, Hallucination & Clean Code)          │
└──────────────────────────────────────┬───────────────────────────────────────┘
                                       │
                                       ▼
┌──────────────────────────────────────────────────────────────────────────────┐
│                      GIAI ĐOẠN 6: TỐI ƯU HÓA (OPTIMIZATION)                  │
│                (Latency, Token Budget, Caching, DB Query, Profiling)         │
└──────────────────────────────────────┬───────────────────────────────────────┘
                                       │
                                       ▼
┌──────────────────────────────────────────────────────────────────────────────┐
│                    GIAI ĐOẠN 7: KIỂM THỬ ĐỘC LẬP (TESTING & QA)              │
│              (Unit Math, Mock Data, Regression, Proof of Work)               │
└──────────────────────────────────────┬───────────────────────────────────────┘
                                       │
               ┌───────────────────────┴───────────────────────┐
           [Test FAIL]                                     [Test PASS]
               │                                               │
               ▼                                               │
┌─────────────────────────────────────────┐                    │
│ GIAI ĐOẠN 8: FEEDBACK & AUTO-REMEDIATION│                    │
│   (Root Cause Analysis & Self-Healing)  │                    │
└──────────────────────┬──────────────────┘                    │
                       │ (Max 3 rounds)                        │
                       └───────────────► Quay lại Bước 4       │
                                                               ▼
┌──────────────────────────────────────────────────────────────────────────────┐
│                 GIAI ĐOẠN 9: BÁO CÁO NGHIỆM THU & BÀN GIAO                   │
│               (Executive Summary, Test Evidence, Runbook)                    │
└──────────────────────────────────────────────────────────────────────────────┘
```

---

## Giai Đoạn 1: Hiểu Mong Muốn Người Dùng (User Intent Discovery)

### 1.1. Mục tiêu
Biến các yêu cầu tự nhiên, trừu tượng hoặc chưa đầy đủ của người dùng (ví dụ: *"tôi muốn xem cổ phiếu nào tốt để mua"*, *"hãy tính toán rủi ro danh mục"*...) thành **Đặc tả Mục tiêu Chính xác (Precise Goal Specification)**.

### 1.2. Bộ lọc 4 câu hỏi định hình (4-Axis Filter)
Trước khi phân tích code hay giải pháp, AI bắt buộc phải trả lời rõ 4 câu hỏi:
1. **Đối tượng thụ hưởng (Persona & Context)**: Ai sử dụng tính năng này? Nhà đầu tư cá nhân, chuyên viên phân tích, hay hệ thống tự động?
2. **Đầu vào (Input Signals)**: Dữ liệu người dùng cung cấp là gì? (Mã ticker, file BCTC, danh mục hiện tại, khung thời gian 1D/1W/1M).
3. **Đầu ra kỳ vọng (Expected Output)**: Người dùng muốn nhận bảng số liệu, biểu đồ đồ thị, khuyến nghị Socratic hay một hành động giao dịch thực tế?
4. **Ranh giới & Ràng buộc (Constraints & Non-Goals)**: Giới hạn ngân sách token? Thời gian phản hồi tối đa? Những điều gì hệ thống **KHÔNG** được phép làm?

### 1.3. Cơ chế Phỏng vấn Chủ động (Interactive Inquiring)
- Nếu yêu cầu bị thiếu dữ liệu quan trọng, sử dụng câu hỏi trắc nghiệm hoặc gợi ý phương án thay vì bắt người dùng gõ lại từ đầu.
- **Tiêu chuẩn hoàn thành (Exit Gate)**: Xuất ra bản tóm tắt mục tiêu ngắn gọn và nhận được sự xác nhận của người dùng.

---

## Giai Đoạn 2: Phân Tích Nghiệp Vụ Tài Chính (Domain Analysis)

### 2.1. Mục tiêu
Bóc tách bài toán sang lăng kính tài chính định lượng, logic kế toán và quản trị rủi ro.

### 2.2. Các trụ cột phân tích nghiệp vụ
1. **Quy tắc Tính Toán Tất Định (Deterministic Math)**:
   - Liệt kê chính xác công thức toán: Ví dụ DuPont 3 bước:
     $$\text{ROE} = \text{Net Margin} \times \text{Asset Turnover} \times \text{Equity Multiplier}$$
   - Giá trị rủi ro danh mục: $\text{VaR}_{95\%}$ bằng Historical Simulation hay Parametric? Khung thời gian lấy mẫu là bao nhiêu phiên (e.g., 252 phiên giao dịch)?
2. **Khảo sát Nguồn Dữ Liệu (Data Feeds & Lineage)**:
   - BCTC: Bảng CĐKT, KQKD, LCTT lấy từ nguồn nào (Data Hub nội bộ, Vnstock, CafeF)? Cần kiểm tra kiểm toán (`audited = True`) hay chấp nhận báo cáo tự lập?
   - Dữ liệu giá/khối lượng: Khung thời gian (Daily, Intraday, Real-time ticks)?
3. **Ma trận Rủi ro & Tuân thủ Pháp lý (Risk & Compliance Matrix)**:
   - Các cảnh báo bắt buộc: Cổ phiếu diện kiểm soát, hạn chế giao dịch, tỷ lệ ký quỹ margin tối đa của UBCKNN.
4. **Tiêu chuẩn Chấp nhận (Acceptance Criteria - AC)**:
   - Viết dưới dạng `Given - When - Then` có số liệu kiểm chứng cụ thể.

---

## Giai Đoạn 3: Tuyển Chọn Subagent & Thiết Kế Tool Grants (Architecture)

### 3.1. Ma trận Tuyển chọn Subagent (Subagent Selection Matrix)
Dựa vào phân tích nghiệp vụ ở Giai đoạn 2, Orchestrator lựa chọn tập hợp tối thiểu các Subagent cần tham gia:

| Bài toán Nghiệp vụ | Subagent Đảm nhiệm | Vai trò & Trách nhiệm |
|---|---|---|
| Lấy giá, sổ lệnh, biến động phiên | `market_feed_specialist` | Fetch giá, cache dữ liệu SQLite WAL, chuẩn hóa ticker. |
| Bóc tách chỉ số tài chính, BCTC | `bctc_analyst_specialist` | Truy vấn các dòng chỉ tiêu BCTC, tính toán tỷ số cơ bản. |
| Tín hiệu kỹ thuật, MA, RSI, MACD | `quant_signal_specialist` | Tính toán chuỗi thời gian, phát hiện mô hình nến, phân kỳ. |
| Đo lường độ biến động, VaR, MaxDD | `risk_monitor_specialist` | Đo lường độ rủi ro, cảnh báo vi phạm giới hạn phân bổ. |
| Tái cân bằng danh mục, tối ưu hóa | `portfolio_allocator_specialist` | Chạy thuật toán Markowitz/Risk Parity, sinh lệnh mô phỏng. |
| Đọc tin tức, vĩ mô, lãi suất | `macro_sentiment_specialist` | Quét tin tức, trích xuất sự kiện vĩ mô và chấm điểm cảm xúc. |
| Tương tác hỏi đáp, giải thích thuật ngữ | `socratic_companion_specialist` | Dẫn dắt người dùng tự hiểu bản chất, không rò rỉ đáp án. |

### 3.2. Nguyên Tắc Phân Quyền Tool (Least-Privilege Tool Grants)
* **Tier 1 - READ_ONLY**: Truy vấn dữ liệu lịch sử, đọc BCTC, xem giá. Subagent tự do sử dụng.
* **Tier 2 - COMPUTATIONAL**: Chạy hàm toán học, mô phỏng Monte Carlo. Yêu cầu giới hạn RAM và thời gian chạy.
* **Tier 3 - STATE_MUTATION / ACTION_RISK**: Đặt lệnh giao dịch, rebalance danh mục, lưu thay đổi vào DB production. **BẮT BUỘC** có chốt chặn Kill Switch và Human-in-the-Loop.

### 3.3. Định Tuyến Luồng Thực Thi (Routing Topology)
Lựa chọn mô hình kết nối:
- **Sequential Pipeline**: Phân tích tuần tự (Lấy dữ liệu ➔ Tính toán ➔ Kiểm tra rủi ro ➔ Kết luận).
- **Fan-out / Fan-in (Song song)**: Chạy đồng thời `bctc_analyst` và `quant_signal`, sau đó gộp kết quả tại `risk_monitor`.

---

## Giai Đoạn 4: Thực Thi Mã Nguồn (Implementation)

### 4.1. Nguyên tắc Tracer Bullet
Không code dàn trải toàn bộ hệ thống cùng lúc. Xây dựng một lát cắt mỏng (thin end-to-end slice) chạy thông suốt từ:
$$\text{Input Schema} \longrightarrow \text{Subagent Service} \longrightarrow \text{Deterministic Tool} \longrightarrow \text{Output Schema}$$

### 4.2. Bộ Quy chuẩn Kỹ thuật Bắt buộc
1. **Giới hạn 200 dòng (Hard Limit)**: Mọi file code tạo mới hoặc sửa đổi PHẢI dưới 200 dòng. Vượt quá phải chủ động phân tách thành service/helper nhỏ hơn.
2. **100% Strict Typing**:
   - Python: Pydantic v2 schemas, type hinting đầy đủ (`typing.Optional`, `typing.Literal`, `typing.List`).
   - TypeScript/React: Type-safe props, clean interfaces, tuyệt đối không dùng `any` bừa bãi.
3. **Cách ly Code Tính toán (Pure Functions)**:
   - Toàn bộ công thức tài chính nằm trong các hàm thuần túy (pure functions) nhận số, trả số, không chứa side-effects hay phụ thuộc LLM.
4. **An toàn Bảo mật (Secret Safety)**:
   - Không commit API key, token, mật khẩu vào code. Dùng biến môi trường `os.getenv()`.

---

## Giai Đoạn 5: Rà Soát Mã Nguồn (Code Review)

### 5.1. Vai trò Subagent Reviewer
Subagent Reviewer hoạt động như một thanh tra độc lập với vai trò phản biện khắt khe, không được nhân nhượng.

### 5.2. Checklist 5 Trọng Điểm Rà Soát (Review Checklist)
| Trọng điểm | Tiêu chí Kiểm tra | Trạng thái Đạt |
|---|---|---|
| **Toán học & Hallucination** | LLM có tự bịa số liệu tài chính không? Mọi số liệu có trích dẫn từ Tool hoặc Evidence Ledger không? | `PASS` / `REJECT` |
| **Kiến trúc & Giới hạn** | Có file nào vượt quá 200 dòng không? Logic có vi phạm phân tầng (Clean Architecture) không? | `PASS` / `REJECT` |
| **Bảo mật (OWASP)** | Có nguy cơ SQL Injection không? Input người dùng đã được sanitize chưa? Có rò rỉ credential không? | `PASS` / `REJECT` |
| **Xử lý Ngoại lệ** | Có bắt lỗi chia cho 0 (ZeroDivisionError) khi tính P/E âm hoặc vốn chủ sở hữu = 0 không? | `PASS` / `REJECT` |
| **Hiệu năng I/O** | Có xuất hiện vòng lặp gọi API n+1 hoặc blocking I/O trên event loop không? | `PASS` / `REJECT` |

Nếu phát hiện bất kỳ điểm nào chưa đạt, Reviewer xuất ra danh sách các điểm vi phạm cụ thể (kèm `file:line` và cách sửa) và yêu cầu quay lại Giai đoạn 4.

---

## Giai Đoạn 6: Tối Ưu Hóa (Optimization)

### 6.1. Mục tiêu
Đảm bảo giải pháp đạt độ phản hồi nhanh, tiêu thụ ít tài nguyên và tiết kiệm chi phí token LLM.

### 6.2. Các Kỹ thuật Tối ưu Hóa Cốt Lõi
1. **Tối ưu Dữ liệu & Caching**:
   - Dữ liệu BCTC quá khứ là bất biến (immutable) ➔ Lưu cache tại DuckDB / SQLite WAL local, không fetch lại qua mạng.
   - Dữ liệu giá realtime ➔ Áp dụng debounce (300ms - 500ms) để chống spam request.
2. **Tối ưu Token Budget & Context Window**:
   - Sử dụng Structured Output (JSON Schema) để tránh sinh các văn bản thừa.
   - Chỉ truyền vào prompt ngữ cảnh những dòng BCTC liên quan, không dump toàn bộ file PDF vào prompt.
3. **Tối ưu Frontend UI**:
   - Sử dụng React virtualization cho bảng dữ liệu hàng ngàn giao dịch/cổ phiếu.
   - Tách biệt UI state và Data fetching thông qua TanStack Query để tránh re-render layout.

---

## Giai Đoạn 7: Kiểm Thử Độc Lập (Testing & Proof of Work)

### 7.1. Triết lý "Test As Proof of Work"
Một tính năng chỉ được xem là hoàn thành khi có automated test chạy **PASS** thực tế trên terminal. Không chấp nhận giả định *"chắc chắn code sẽ chạy được"*.

### 7.2. Các Tầng Kiểm Thử Bắt Buộc
1. **Unit Test Thuật Toán Toán Học**:
   - So sánh kết quả tính toán của tool với bảng tính mẫu đã được kiểm toán (sai số cho phép $< 10^{-4}$).
2. **Edge-case Test (Trường hợp biên)**:
   - Cổ phiếu mới niêm yết (thiếu dữ liệu lịch sử).
   - Lợi nhuận âm, vốn chủ sở hữu âm (ROE/PE âm).
   - Thị trường ngừng giao dịch, mất kết nối mạng.
3. **Integration & Contract Test**:
   - Kiểm tra chuỗi gọi qua LangGraph StateGraph đảm bảo state truyền giữa các node không bị mất dữ liệu.
4. **Guardrail & Security Test**:
   - Thử nghiệm các prompt tấn công (jailbreak) nhằm ép hệ thống đưa ra khuyến nghị mua bán trái quy định pháp luật.

---

## Giai Đoạn 8: Feedback, Debug & Tự Sửa Lỗi (Auto-Remediation Loop)

### 8.1. Cơ chế Vòng lặp Khép Kín (Closed-Loop Self-Healing)
Khi có lỗi phát sinh từ **Giai đoạn 5 (Review)** hoặc **Giai đoạn 7 (Test)**:

```
[Phát hiện Lỗi / Test Fail]
           │
           ▼
[Debugger Subagent: Root Cause Analysis (RCA)]
  - Đọc Stack Trace & Log
  - Xác định file:line gây lỗi
  - Phân loại lỗi: Logic, Type, Data hay Timeout
           │
           ▼
[Tạo Kế hoạch Sửa Lỗi (Fix Plan)]
           │
           ▼
[Thực thi Sửa Code (Giai đoạn 4)]
           │
           ▼
[Chạy lại Test Độc lập (Giai đoạn 7)]
           │
     ┌─────┴─────────────────┐
 [Vẫn Lỗi]                [PASS]
     │                       │
     ▼                       ▼
(Lặp lại tối đa 3 lần)    (Chuyển sang Giai đoạn 9)
```

### 8.2. Chốt Chặn Giới Hạn (Escalation Circuit Breaker)
* Nếu sau **3 vòng lặp** sửa lỗi tự động mà test vẫn không PASS:
  - Hệ thống BẮT BUỘC dừng lại, không tự sửa mò tiếp để tránh làm hỏng cấu trúc mã nguồn.
  - Xuất hiện thông báo Escalation nêu rõ nguyên nhân gốc rễ và xin chỉ định từ người dùng.

---

## Giai Đoạn 9: Báo Cáo Nghiệm Thu & Bàn Giao (Final Reporting)

### 9.1. Mục tiêu
Tổng hợp kết quả minh bạch, chứng minh code chạy đúng và cung cấp hướng dẫn vận hành cho người dùng.

### 9.2. Cấu trúc Báo Cáo Chuẩn Mực
Báo cáo nghiệm thu cuối cùng phải bao gồm đầy đủ 5 phần:

1. **Executive Summary (Tóm lược điều hành)**:
   - Mục tiêu ban đầu và giải pháp đã hoàn thành.
   - Các Subagent và Công cụ đã được kích hoạt.
2. **Bảng Bằng Chứng Kiểm Thử (Proof of Work Table)**:
   - Tên test suite, số lượng test case, thời gian thực thi và kết quả (`PASSED`).
3. **Thay Đổi Mã Nguồn (Codebase Impact Ledger)**:
   - Danh sách file tạo mới, file sửa đổi (mỗi file kèm đường link và xác nhận kích thước < 200 dòng).
4. **Chỉ Số Hiệu Năng & Rủi Ro (Performance & Safety Metrics)**:
   - Thời gian phản hồi trung bình, số token tiêu thụ, phân lớp rủi ro của tác vụ.
5. **Hướng Dẫn Sử Dụng & Vận Hành (Runbook)**:
   - Lệnh khởi chạy, cách tương tác trên giao diện, và cách kiểm tra lại bằng lệnh test.

---

## 2. Bảng Kiểm Tra Sẵn Sàng Vận Hành (Operation Readiness Checklist)

Trước khi xác nhận bàn giao một tính năng tài chính:

- [ ] Đã xác nhận rõ mong muốn người dùng và phạm vi không làm (Non-Goals).
- [ ] Mọi phép toán tài chính đã được đóng gói thành Tool tất định, không để LLM đoán mò.
- [ ] Đã chọn đúng Subagent chuyên biệt theo ma trận nghiệp vụ.
- [ ] 100% các file code có độ dài **dưới 200 dòng** và có Type hinting đầy đủ.
- [ ] Không có API key hay secret nào bị hardcode.
- [ ] Reviewer đã kiểm tra và phê duyệt kiến trúc cùng bảo mật.
- [ ] Toàn bộ unit tests và integration tests chạy **PASS 100%**.
- [ ] Đã xuất báo cáo nghiệm thu rõ ràng kèm bằng chứng thực thi.
