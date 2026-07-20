# Lớp 4: Sơ đồ Luồng Nghiệp vụ Chéo (Cross-Module Integration)

## 1. Hành trình Từ Tin tức đến Thực hành

```mermaid
graph TD
    A[Student reads News M4 about Retail sector] --> B[Clicks Ticker Tag 'MWG']
    B --> C[Redirects to BCTC Analysis M3]
    C --> D{Sees confusing debt ratio}
    D -- Clicks AI Assistant --> E[AI explains and suggests: 'Learn Balance Sheet reading at Learn Hub']
    E --> F[Student goes to Learn Hub M2]
    F --> G[Completes lesson & takes Quiz]
    G --> H{Scores 8/10?}
    H -- Yes --> I[System unlocks feature]
    H -- No --> G
    I --> J[Student enters Backtest Lab M5]
    J --> K[Selects 'Retail Crisis' scenario with MWG]
```

---

## 2. Luồng Phạt Giáo Dục (Education Penalty Flow)

```mermaid
graph TD
    A[Trading violation: PnL < -50% or 3 stop-loss violations] --> B[Account locked]
    B --> C[Learn Hub Quiz: Quản trị rủi ro]
    C --> D{Pass Quiz >= 80%?}
    D -- Yes --> E[Unlock Account & Restore Capital]
    D -- No --> C
    E --> F[Resume trading in Backtest Lab]
```

---

## 3. Bản đồ Hành trình Người dùng (User Journey Map) - Vai trò trung tâm của Learn Hub

```mermaid
journey
    title Hành trình Sinh viên: Learn Hub là gốc
    section Khám phá & Tin tức (M4)
      Đọc tin tức: 5: Student
      Nhấn Ticker tag: 4: Student
    section Phân tích BCTC (M3)
      Xem biểu đồ nợ: 3: Student
      Nhờ AI giải thích: 4: Student, AI Assistant
      Chuyển hướng học: 5: System
    section Học tập cốt lõi (M2 - Learn Hub)
      Học bài mới: 4: Student
      Làm Quiz: 3: Student
      Mở khóa tính năng: 5: System
    section Thực hành & Giả lập (M5)
      Tạo chiến lược: 4: Student
      Chạy kịch bản 2008: 5: Student
      Vi phạm cắt lỗ & Bị khóa: 2: System
    section Phục hồi & Học lại (M2 - Learn Hub)
      Làm Quiz QTRR: 3: Student
      Mở khóa tài khoản: 5: System
```
