# PlantUML Render Test File

This file contains the exact Use Case diagram using standard **PlantUML** syntax, preserving all standard notations, and links to the rendered image representation below.

---

## 1. UML 2.5 Use Case Diagram (PlantUML Render)

Here is the rendered diagram:

![Use Case Diagram](usecase_diagram.png)

Below is the exact raw PlantUML code:

```plantuml
@startuml
left to right direction
skinparam packageStyle rectangle
' BỎ dòng skinparam actorStyle awesome hoặc đổi thành stickman
skinparam actorStyle stickman

actor "Học sinh/sinh viên" as Trader
actor "Quản trị viên" as Admin
actor "Hệ thống tự động" as SystemAgent

rectangle "«subsystem»\nHệ thống Risk Dashboard" {
  usecase "Xem tổng quan\nrủi ro" as UC_ViewRisk
  usecase "Phân tích tin tức\nthị trường" as UC_AnalyzeNews
  usecase "Tính điểm ưu tiên\ntin tức" as UC_CalcImportance
  usecase "Tạo báo cáo EOD\ntự động" as UC_EODReport
  usecase "Chạy mô hình\ndự báo XGBoost" as UC_RunXGBoost
  usecase "Quản lý danh mục\ntheo dõi" as UC_Watchlist
  usecase "Tương tác trợ lý AI" as UC_AIChat
  usecase "Chạy kịch bản\nStress-test" as UC_StressTest
}

actor "VNStock API" as VNStockAPI
actor "LLM Provider" as LLMProvider

' Associations - Đường liền KHÔNG mũi tên
Trader -- UC_ViewRisk
Trader -- UC_AnalyzeNews
Trader -- UC_Watchlist
Trader -- UC_AIChat

Admin -- UC_ViewRisk
Admin -- UC_EODReport
Admin -- UC_RunXGBoost

SystemAgent -- UC_EODReport

' Secondary Actor Associations
UC_AnalyzeNews -- VNStockAPI
UC_EODReport -- LLMProvider
UC_AIChat -- LLMProvider

' Include Relationships
UC_AnalyzeNews ..> UC_CalcImportance : <<include>>
UC_EODReport ..> UC_RunXGBoost : <<include>>

' Extend Relationships
UC_StressTest .> UC_ViewRisk : <<extend>>

@enduml
```

---

## 2. System Architecture (C4 Container Diagram)

```mermaid
C4Container
    title Sơ đồ Kiến trúc Hệ thống Risk Dashboard (C4 Container Diagram)

    %% Users / Clients
    Person(investor, "Học sinh/sinh viên", "Truy cập dashboard để xem chỉ số rủi ro vĩ mô, đọc tin tức được gán nhãn và quản lý danh mục đầu tư.")
    Person(admin, "Quản trị viên", "Quản trị nội dung CMS, sinh bản thảo bằng AI, duyệt tin tức và giám sát trạng thái hệ thống.")

    %% External APIs
    System_Ext(openai, "LLM API Provider", "OpenAI API (GPT-4o-mini completions & embeddings)")
    System_Ext(vnstock, "VNStock API", "VNStock service (Cung cấp giá chứng khoán VN)")
    System_Ext(macro, "yfinance & WorldBank", "Market & Macro APIs (Cung cấp chỉ số vĩ mô thế giới)")

    %% VPC Cloud
    System_Boundary(private_cloud, "Risk Dashboard Cloud Infrastructure") {
        
        %% DMZ Proxy
        Container(nginx, "Nginx Reverse Proxy", "Nginx", "Định tuyến luồng HTTP, phục vụ tệp tin frontend tĩnh, cấu hình SSL Termination")
        
        %% Application Subnet
        System_Boundary(app_subnet, "Application Subnet") {
            Container(fastapi, "FastAPI App & Registry", "Python, uvicorn", "Điều phối API, đăng ký router động cho các modules nghiệp vụ")
            Container(modules, "Business Modules", "Python Modules", "Thực thi nghiệp vụ: system_surface, quant_risk, news_intelligence, ai_assistant, financial_health, admin_cms")
            Container(engines, "Quant Computation Engines", "Python Library", "Tính toán phân tích định lượng: XGBoost, GARCH, VaR, HMM, Scenario overrides")
            Container(orchestrator, "Agent Orchestration Graph", "LangGraph", "Điều phối hoạt động multi-agent, phân loại ý định (intent routing), duyệt các narrative")
        }

        %% Storage Subnet
        System_Boundary(storage_subnet, "Data & Storage Subnet") {
            ContainerDb(db, "Application Database", "SQLite Store", "Lưu trữ cấu hình ứng dụng, trạng thái, tin tức và snapshots")
            ContainerDb(cache, "Data Cache", "SQLite cache.db", "Lưu trữ ma trận bảng điều khiển thị trường chéo vĩ mô (cross-asset panel)")
        }
    }

    %% Connections
    Rel(investor, nginx, "Tương tác xem dữ liệu & chat", "HTTPS/TCP 443")
    Rel(admin, nginx, "Truy cập trang quản trị", "HTTPS/TCP 443")
    Rel(nginx, fastapi, "Chuyển tiếp API requests", "HTTP/TCP 8000")
    
    Rel(fastapi, modules, "Gọi các router modules", "Internal Call")
    Rel(modules, engines, "Kích hoạt tính toán lượng hóa", "Internal Library Call")
    Rel(modules, orchestrator, "Chạy luồng trợ lý AI", "Internal Call")
    
    Rel(modules, db, "Đọc/Ghi dữ liệu ứng dụng", "SQLite/file")
    Rel(modules, cache, "Đọc/Ghi ma trận chỉ số", "SQLite/file")
    Rel(engines, cache, "Truy vấn dữ liệu phục vụ huấn luyện", "SQLite/file")
    
    Rel(modules, vnstock, "Crawl giá chứng khoán & vĩ mô", "HTTPS/TCP 443")
    Rel(modules, macro, "Crawl dữ liệu yfinance & WB", "HTTPS/TCP 443")
    Rel(orchestrator, openai, "Gửi prompts và nhận kết quả LLM", "HTTPS/TCP 443")

    UpdateLayoutConfig($c4ShapeInRow="3", $c4BoundaryInRow="1")
```
