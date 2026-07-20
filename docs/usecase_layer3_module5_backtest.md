# Lớp 3 - Module 5: Backtest & Thực Hành

## Biểu đồ Use Case (Use Case Diagram)

```mermaid
flowchart LR
    %% Actors
    Student["🧑‍🎓 Sinh viên (Student)"]
    System["⚙️ Hệ thống (System)"]

    %% Module 5: Backtest & Thực Hành
    subgraph M5["Module 5: Backtest & Thực Hành"]
        UC51(["UC-M5.1: Xây dựng chiến lược (Strategy Builder)"])
        UC52(["UC-M5.2: Tua nhanh thời gian / Kịch bản lịch sử"])
        UC53(["UC-M5.3: Xem thống kê hiệu quả"])
        UC54(["UC-M5.4: Mở khóa tài khoản bị phạt"])
    end

    %% Module 2: Learn Hub (Cross-module)
    subgraph M2["Module 2: Learn Hub"]
        Quiz(["Làm Quiz Quản trị Rủi ro"])
    end

    %% Relationships
    Student --> UC51
    Student --> UC52
    Student --> UC53
    Student --> UC54
    System -.->|"Tự động khóa/mở khóa"| UC54
    UC54 -.->|"≪include≫"| Quiz
```

---

## Chi tiết Use Case & Sequence Diagrams

### UC-M5.1: Xây dựng chiến lược (Strategy Builder)

**Mô tả:** Cho phép sinh viên thiết lập chiến lược giao dịch dựa trên các chỉ số Cơ bản và Kỹ thuật.
**Actors:** Sinh viên
**Điều kiện trước (Pre-conditions):** Sinh viên đã đăng nhập và hoàn thành các bài học cơ bản về chỉ số (Learn Hub).
**Luồng chính (Main Flow):**
1. Sinh viên truy cập tính năng Strategy Builder.
2. Sinh viên chọn các chỉ báo (MA, RSI, PE, PB).
3. Hệ thống lưu cấu hình và xác nhận thành công.
**Luồng thay thế (Alternative Flows):** Nếu chỉ báo chưa được học, hệ thống cảnh báo và gợi ý bài học.
**Điều kiện sau (Post-conditions):** Chiến lược được lưu và sẵn sàng để chạy Backtest.

> [!IMPORTANT]
> Quy tắc nghiệp vụ (Business Rules): Sinh viên chỉ được sử dụng các chỉ báo đã mở khóa trong Learn Hub.

```mermaid
sequenceDiagram
    actor Student
    participant SPA
    participant API
    participant StrategyBuilder
    participant DB
    
    Student->>SPA: Mở tính năng Strategy Builder
    SPA->>API: Yêu cầu danh sách chỉ báo khả dụng
    API->>StrategyBuilder: Lấy dữ liệu
    StrategyBuilder-->>API: Trả về MA, RSI, PE, PB
    API-->>SPA: Hiển thị danh sách
    Student->>SPA: Chọn và cấu hình chỉ báo
    SPA->>API: Lưu chiến lược
    API->>DB: Lưu cấu hình
    DB-->>API: OK
    API-->>SPA: Thông báo thành công
```

---

### UC-M5.2: Tua nhanh thời gian (Bar Replay) / Chạy kịch bản lịch sử

**Mô tả:** Sinh viên chạy thử chiến lược trên dữ liệu quá khứ hoặc tua nhanh thời gian trên biểu đồ.
**Actors:** Sinh viên
**Điều kiện trước:** Có ít nhất 1 chiến lược hợp lệ.
**Luồng chính:**
1. Sinh viên chọn chiến lược.
2. Sinh viên chọn kịch bản lịch sử (2008, 2020) hoặc Bar Replay.
3. Hệ thống chạy giả lập và hiển thị diễn biến theo thời gian.
**Luồng thay thế:** Thiếu dữ liệu của kịch bản, hệ thống thông báo lỗi.
**Điều kiện sau:** Hoàn tất giả lập, sinh viên có thể xem kết quả.

```mermaid
sequenceDiagram
    actor Student
    participant SPA
    participant API
    participant BacktestEngine
    participant HistoryDB as Historical Data Store
    
    Student->>SPA: Chọn kịch bản (2008 crisis, 2020 COVID)
    SPA->>API: Gửi yêu cầu Backtest
    API->>BacktestEngine: Khởi chạy engine
    BacktestEngine->>HistoryDB: Truy xuất dữ liệu quá khứ
    HistoryDB-->>BacktestEngine: Trả dữ liệu
    BacktestEngine-->>API: Stream diễn biến
    API-->>SPA: Hiển thị Tua nhanh/Bar replay liên tục
```

---

### UC-M5.3: Xem thống kê hiệu quả

**Mô tả:** Xem chi tiết các chỉ số thống kê hiệu suất của chiến lược vừa chạy.
**Actors:** Sinh viên
**Điều kiện trước:** Hoàn thành ít nhất một lần chạy giả lập (UC-M5.2).
**Luồng chính:**
1. Hệ thống tự động tính toán số liệu ngay sau khi giả lập kết thúc.
2. Sinh viên mở bảng thống kê để xem Win rate, Max Drawdown, Sharpe, PnL.
**Điều kiện sau:** Không có.

```mermaid
sequenceDiagram
    actor Student
    participant SPA
    participant API
    participant StatsCalc as Stats Calculator
    
    Student->>SPA: Yêu cầu xem báo cáo
    SPA->>API: Lấy báo cáo hiệu quả
    API->>StatsCalc: Tính toán Win rate, Max Drawdown, Sharpe, PnL
    StatsCalc-->>API: Trả kết quả tính toán
    API-->>SPA: Hiển thị biểu đồ & thống kê
```

---

### UC-M5.4: Mở khóa tài khoản bị phạt

**Mô tả:** Khi tài khoản bị phạt do giao dịch sai nguyên tắc, sinh viên phải hoàn thành bài Quiz Quản trị Rủi Ro (QTRR) tại Learn Hub để được mở khóa.
**Actors:** Sinh viên, Hệ thống (tự động khóa/mở khóa)
**Điều kiện trước:** Tài khoản đang bị khóa do PnL < -50% hoặc vi phạm cắt lỗ (stop-loss) 3 lần liên tiếp.
**Luồng chính:**
1. Sinh viên thấy thông báo 'Account Locked' và bấm 'Học để mở khóa'.
2. Hệ thống chuyển hướng sang Learn Hub.
3. Sinh viên làm bài Quiz Quản trị Rủi Ro.
4. Hệ thống chấm điểm:
   - Nếu >= 80%: Hệ thống mở khóa tài khoản, khôi phục vốn ảo, ghi log.
   - Nếu < 80%: Yêu cầu làm lại.
**Điều kiện sau:** Tài khoản được mở khóa hoặc sinh viên phải làm lại bài kiểm tra.

> [!CAUTION]
> Quy tắc nghiệp vụ (Business Rules): 
> - Điều kiện khóa: PnL < -50% HOẶC vi phạm stop-loss 3 lần liên tiếp.
> - Số lần mở khóa: Tối đa 3 lần/tháng. Lần thứ 4 yêu cầu liên hệ Admin/Instructor.

```mermaid
sequenceDiagram
    actor Student
    participant SPA
    participant System as System/DB
    participant LearnHub as Learn Hub
    participant QuizEngine
    
    Student->>SPA: Truy cập Dashboard (thấy 'Account Locked')
    Student->>SPA: Bấm 'Học để mở khóa'
    SPA->>System: Yêu cầu mở khóa
    System->>LearnHub: Chuyển hướng
    LearnHub->>QuizEngine: Mở bài Quiz Quản trị Rủi Ro (QTRR)
    Student->>QuizEngine: Hoàn thành bài Quiz
    QuizEngine->>System: Gửi điểm số
    alt score >= 80%
        System->>System: Unlock account, restore virtual capital
        System->>System: Log 'Account Unlocked via Education'
        System-->>SPA: Thông báo thành công, tiếp tục giao dịch
    else score < 80%
        System-->>SPA: Yêu cầu làm lại Quiz (score < 80%)
        SPA->>QuizEngine: Quay lại bài Quiz
    end
```
