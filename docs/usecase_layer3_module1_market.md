# Lớp 3 - Module 1: Bảng Điện & Quản Lý Danh Mục

## Use Case Diagram

```mermaid
flowchart LR
    %% Actors
    HocVien["🧑‍🎓 Student/Trainee"]
    MarketData["📊 Market Data Provider"]

    %% Use Cases
    UC11("UC-M1.1: Xem dữ liệu thị trường (EOD/Trễ 15p) & Biểu đồ")
    UC12("UC-M1.2: Quản lý Watchlist (Thêm/Xóa/Phân loại)")
    UC13("UC-M1.3: Đặt lệnh ảo (MP/LO)")
    UC13_Inc("Kiểm tra số dư tiền mặt ảo")
    UC14("UC-M1.4: Xem Sổ lệnh (Order Book) & Trạng thái khớp lệnh")
    UC15("UC-M1.5: Xem Dashboard tài sản (Tổng tài sản, PnL, Giá vốn)")

    %% Relationships
    HocVien --> UC11
    HocVien --> UC12
    HocVien --> UC13
    HocVien --> UC14
    HocVien --> UC15
    MarketData --> UC11
    
    UC13 -. "<<include>>" .-> UC13_Inc
```

---

## UC-M1.1: Xem dữ liệu thị trường (EOD/Trễ 15p) & Biểu đồ

### 1. Mô tả
Cho phép Học viên xem dữ liệu thị trường chứng khoán (giá, khối lượng, các chỉ số) với độ trễ 15 phút hoặc dữ liệu cuối ngày (EOD), cùng với biểu đồ giá kỹ thuật để phân tích.

### 2. Actors
- **Primary:** 🧑‍🎓 Student/Trainee
- **Secondary:** 📊 Market Data Provider

### 3. Điều kiện trước (Pre-condition)
- Học viên đã đăng nhập thành công vào nền tảng.
- Hệ thống kết nối ổn định với Market Data Provider.

### 4. Luồng chính (Main Flow)
1. Học viên truy cập vào tính năng Bảng Điện / Thị trường.
2. Hệ thống React SPA gửi yêu cầu lấy dữ liệu thị trường đến FastAPI backend.
3. Backend lấy dữ liệu mới nhất (đã được cache hoặc fetch từ Market Data Provider qua DB).
4. Backend trả về dữ liệu và SPA hiển thị Bảng điện.
5. Học viên chọn một mã chứng khoán để xem biểu đồ chi tiết.
6. Backend trả về dữ liệu lịch sử và SPA render biểu đồ (ví dụ: TradingView chart).

### 5. Luồng thay thế (Alternative Flow)
- *Lỗi kết nối dữ liệu:* Nếu không kết nối được với Market Data Provider, hệ thống hiển thị dữ liệu lưu trữ gần nhất và thông báo cho người dùng "Dữ liệu đang bị trễ hoặc mất kết nối".

### 6. Điều kiện sau (Post-condition)
Học viên xem được dữ liệu thị trường và biểu đồ tương ứng.

### 7. Quy tắc nghiệp vụ (Business Rules)
> [!IMPORTANT]
> Dữ liệu thị trường cung cấp cho tài khoản học viên mặc định là dữ liệu trễ 15 phút hoặc dữ liệu EOD (End Of Day) tùy theo cấu hình cấp phép, không phải Real-time để tiết kiệm chi phí API.

### 8. Sequence Diagram

```mermaid
sequenceDiagram
    participant S as 🧑‍🎓 Student
    participant UI as React SPA
    participant API as FastAPI
    participant MDP as 📊 Market Data Provider
    participant DB as SQLite DB

    S->>UI: Truy cập Bảng điện
    activate UI
    UI->>API: GET /market/data
    activate API
    API->>MDP: Fetch delayed data (nếu cache hết hạn)
    activate MDP
    MDP-->>API: Market Data
    deactivate MDP
    API->>DB: Lưu/Cập nhật dữ liệu
    activate DB
    DB-->>API: Success
    deactivate DB
    API-->>UI: Dữ liệu thị trường
    deactivate API
    UI-->>S: Hiển thị Bảng điện

    S->>UI: Chọn mã cổ phiếu xem biểu đồ
    UI->>API: GET /market/chart/{symbol}
    activate API
    API->>DB: Lấy dữ liệu lịch sử giá
    activate DB
    DB-->>API: Historical Data
    deactivate DB
    API-->>UI: Chart Data
    deactivate API
    UI-->>S: Render biểu đồ kỹ thuật
    deactivate UI
```

---

## UC-M1.2: Quản lý Watchlist (Thêm/Xóa/Phân loại)

### 1. Mô tả
Học viên có thể tạo và quản lý nhiều danh sách theo dõi (Watchlist) để tiện theo dõi các mã cổ phiếu quan tâm theo các tiêu chí hoặc danh mục riêng.

### 2. Actors
- **Primary:** 🧑‍🎓 Student/Trainee

### 3. Điều kiện trước (Pre-condition)
- Học viên đã đăng nhập.

### 4. Luồng chính (Main Flow)
1. Học viên chọn "Tạo Watchlist mới" và nhập tên.
2. Học viên tìm kiếm mã cổ phiếu và chọn "Thêm vào Watchlist".
3. SPA gửi API request lên Backend.
4. Backend lưu thông tin vào CSDL.
5. SPA cập nhật và hiển thị danh sách mã cổ phiếu trong Watchlist vừa chọn.
6. Học viên có thể xóa mã khỏi Watchlist hoặc chuyển sang danh mục khác.

### 5. Luồng thay thế (Alternative Flow)
- *Mã cổ phiếu không tồn tại:* Hệ thống báo lỗi và không cho phép thêm.

### 6. Điều kiện sau (Post-condition)
Watchlist được cập nhật (thêm, xóa, hoặc tạo mới) và lưu vào hồ sơ Học viên.

### 7. Quy tắc nghiệp vụ (Business Rules)
> [!IMPORTANT]
> Mỗi Học viên được tạo tối đa 5 Watchlist, mỗi Watchlist tối đa 50 mã cổ phiếu.

### 8. Sequence Diagram

```mermaid
sequenceDiagram
    participant S as 🧑‍🎓 Student
    participant UI as React SPA
    participant API as FastAPI
    participant DB as SQLite DB

    S->>UI: Tạo Watchlist mới (Tên)
    activate UI
    UI->>API: POST /watchlist
    activate API
    API->>DB: Insert Watchlist
    DB-->>API: Success
    API-->>UI: Watchlist created
    deactivate API
    UI-->>S: Hiển thị Watchlist mới

    S->>UI: Tìm & Thêm mã CP vào Watchlist
    UI->>API: POST /watchlist/{id}/items (symbol)
    activate API
    API->>DB: Insert symbol to Watchlist
    DB-->>API: Success
    API-->>UI: Item added
    deactivate API
    UI-->>S: Cập nhật hiển thị Watchlist
    deactivate UI
```

---

## UC-M1.3: Đặt lệnh ảo (MP/LO)

### 1. Mô tả
Cho phép Học viên thực hành đặt lệnh mua/bán cổ phiếu bằng tiền ảo (Virtual Money). Hỗ trợ các loại lệnh cơ bản như Lệnh thị trường (MP) và Lệnh giới hạn (LO). Bao gồm tính năng kiểm tra số dư.

### 2. Actors
- **Primary:** 🧑‍🎓 Student/Trainee

### 3. Điều kiện trước (Pre-condition)
- Học viên đã đăng nhập.
- Học viên đã có tài khoản giao dịch ảo (Virtual Account) với số dư khởi tạo.

### 4. Luồng chính (Main Flow)
1. Học viên chọn mã cổ phiếu, chọn loại lệnh (Mua/Bán) và loại giá (MP/LO).
2. Học viên nhập khối lượng và giá (nếu là lệnh LO).
3. SPA gửi yêu cầu đặt lệnh lên API.
4. (Include) Backend gọi Balance Checker để kiểm tra số dư tiền mặt (đối với lệnh Mua) hoặc số dư cổ phiếu (đối với lệnh Bán).
5. Sau khi xác thực hợp lệ, Backend chuyển lệnh vào Order Engine.
6. Order Engine ghi nhận lệnh vào Database trạng thái "Pending" (Chờ khớp).
7. SPA thông báo đặt lệnh thành công.

### 5. Luồng thay thế (Alternative Flow)
- *Không đủ số dư:* Balance Checker trả về False. Backend từ chối lệnh và gửi thông báo lỗi "Không đủ số dư tiền/cổ phiếu".

### 6. Điều kiện sau (Post-condition)
Lệnh được ghi nhận vào sổ lệnh của hệ thống. Số tiền/cổ phiếu tương ứng có thể bị phong tỏa (hold).

### 7. Quy tắc nghiệp vụ (Business Rules)
> [!IMPORTANT]
> - Lệnh MP chỉ được đặt trong phiên khớp lệnh liên tục.
> - Số lượng đặt lệnh phải là bội số của 100 (theo quy định sàn HOSE hiện hành).

### 8. Sequence Diagram

```mermaid
sequenceDiagram
    participant S as 🧑‍🎓 Student
    participant UI as React SPA
    participant API as FastAPI
    participant BC as Balance Checker
    participant OE as Order Engine
    participant DB as SQLite DB

    S->>UI: Đặt lệnh Mua (Symbol, LO/MP, Vol, Price)
    activate UI
    UI->>API: POST /order
    activate API
    
    %% Include Balance Check
    API->>BC: Validate Balance & Portfolio
    activate BC
    BC->>DB: Get current Virtual Balance
    activate DB
    DB-->>BC: Balance Data
    deactivate DB
    alt Không đủ số dư
        BC-->>API: Invalid (Insufficient funds)
        API-->>UI: Error: Không đủ số dư
    else Đủ số dư
        BC-->>API: Valid
    end
    deactivate BC

    API->>OE: Process Order
    activate OE
    OE->>DB: Insert Order (Status: Pending)
    activate DB
    DB-->>OE: Order Created
    deactivate DB
    OE->>DB: Hold Funds/Shares
    OE-->>API: Order Accepted
    deactivate OE

    API-->>UI: Đặt lệnh thành công
    deactivate API
    UI-->>S: Hiển thị thông báo xác nhận
    deactivate UI
```

---

## UC-M1.4: Xem Sổ lệnh (Order Book) & Trạng thái khớp lệnh

### 1. Mô tả
Học viên xem danh sách các lệnh đã đặt trong ngày hoặc trong quá khứ, cùng với trạng thái hiện tại của lệnh (Chờ khớp, Đã khớp, Đã hủy).

### 2. Actors
- **Primary:** 🧑‍🎓 Student/Trainee

### 3. Điều kiện trước (Pre-condition)
- Học viên đã đăng nhập.

### 4. Luồng chính (Main Flow)
1. Học viên truy cập tab "Sổ lệnh".
2. SPA yêu cầu API lấy danh sách lệnh của tài khoản.
3. Backend truy vấn DB lấy thông tin lịch sử lệnh và trạng thái mới nhất.
4. SPA hiển thị danh sách lệnh.
5. Học viên có thể sử dụng bộ lọc để xem theo ngày, trạng thái hoặc mã chứng khoán.

### 5. Luồng thay thế (Alternative Flow)
- *Học viên yêu cầu hủy lệnh:* Nếu lệnh đang ở trạng thái "Pending", Học viên có thể chọn Hủy. Backend cập nhật trạng thái thành "Cancelled" và giải tỏa số dư.

### 6. Điều kiện sau (Post-condition)
Học viên nắm được tình trạng các lệnh giao dịch của mình.

### 7. Quy tắc nghiệp vụ (Business Rules)
> [!IMPORTANT]
> Chỉ được phép hủy các lệnh chưa khớp (Pending). Lệnh đã khớp (Matched) một phần hoặc toàn bộ không thể bị hủy.

### 8. Sequence Diagram

```mermaid
sequenceDiagram
    participant S as 🧑‍🎓 Student
    participant UI as React SPA
    participant API as FastAPI
    participant DB as SQLite DB

    S->>UI: Xem Sổ lệnh
    activate UI
    UI->>API: GET /orders?date=today
    activate API
    API->>DB: Query Orders by UserID
    activate DB
    DB-->>API: List of Orders (Pending, Matched, Cancelled)
    deactivate DB
    API-->>UI: Return Order Book
    deactivate API
    UI-->>S: Hiển thị Sổ lệnh
    
    opt Hủy lệnh
        S->>UI: Click "Hủy lệnh" (Order ID)
        UI->>API: DELETE /order/{id}
        activate API
        API->>DB: Check status == Pending?
        activate DB
        alt Status là Pending
            DB-->>API: Valid
            API->>DB: Update Status = Cancelled & Unhold Funds
            DB-->>API: Success
            API-->>UI: Hủy thành công
        else Đã khớp
            DB-->>API: Invalid
            API-->>UI: Lỗi: Lệnh đã khớp
        end
        deactivate DB
        deactivate API
        UI-->>S: Cập nhật giao diện Sổ lệnh
    end
    deactivate UI
```

---

## UC-M1.5: Xem Dashboard tài sản (Tổng tài sản, PnL, Giá vốn)

### 1. Mô tả
Cung cấp cái nhìn tổng quan về danh mục đầu tư hiện tại của Học viên. Hiển thị Tổng tài sản (NAV), Lợi nhuận/Thua lỗ (PnL - Lãi/lỗ dự kiến), Giá vốn trung bình của các mã cổ phiếu đang nắm giữ, và tỷ trọng tiền mặt/cổ phiếu.

### 2. Actors
- **Primary:** 🧑‍🎓 Student/Trainee

### 3. Điều kiện trước (Pre-condition)
- Học viên đã đăng nhập và đang có tài sản (tiền mặt ảo hoặc cổ phiếu).

### 4. Luồng chính (Main Flow)
1. Học viên truy cập "Quản lý tài sản" / "Dashboard".
2. SPA gọi API yêu cầu thông tin Portfolio.
3. Backend gọi Portfolio Calculator.
4. Portfolio Calculator truy vấn số lượng cổ phiếu đang nắm giữ, giá vốn từ DB và giá thị trường hiện tại.
5. Tính toán NAV, PnL (chưa thực hiện) và các chỉ số liên quan.
6. Backend trả về kết quả cho SPA.
7. SPA render các biểu đồ tròn (phân bổ tài sản) và bảng chi tiết danh mục.

### 5. Luồng thay thế (Alternative Flow)
- Không có

### 6. Điều kiện sau (Post-condition)
Học viên xem được hiệu quả đầu tư của mình.

### 7. Quy tắc nghiệp vụ (Business Rules)
> [!IMPORTANT]
> - Giá trị tài sản ròng (NAV) = Tiền mặt + (Tổng số lượng cổ phiếu * Giá thị trường hiện tại).
> - PnL (%) = (Giá thị trường - Giá vốn trung bình) / Giá vốn trung bình * 100.

### 8. Sequence Diagram

```mermaid
sequenceDiagram
    participant S as 🧑‍🎓 Student
    participant UI as React SPA
    participant API as FastAPI
    participant Calc as Portfolio Calculator
    participant DB as SQLite DB

    S->>UI: Mở Dashboard tài sản
    activate UI
    UI->>API: GET /portfolio/summary
    activate API
    API->>Calc: Calculate Portfolio Metrics
    activate Calc
    Calc->>DB: Get Holdings & Cash Balance
    activate DB
    DB-->>Calc: Holdings Data (Volume, Cost Price)
    deactivate DB
    Calc->>DB: Get Latest Market Price (EOD/Delayed)
    activate DB
    DB-->>Calc: Market Prices
    deactivate DB
    
    Note right of Calc: Tính toán NAV, PnL, Tỷ trọng
    Calc-->>API: Portfolio Summary (NAV, PnL, Metrics)
    deactivate Calc
    
    API-->>UI: Return Summary Data
    deactivate API
    UI-->>S: Hiển thị Biểu đồ và Bảng danh mục
    deactivate UI
```
