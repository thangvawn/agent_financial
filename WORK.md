# Risk Dashboard / Agent Tài Chính

## 1. Tổng quan dự án

`Risk Dashboard` là một nền tảng phân tích rủi ro cho thị trường chứng khoán Việt Nam, kết hợp giữa dữ liệu thị trường, mô hình định lượng và hệ thống AI agent để hỗ trợ người dùng đọc trạng thái thị trường, mô phỏng kịch bản và phân tích doanh nghiệp trên một giao diện thống nhất.

Thay vì chỉ hiển thị chart hoặc chỉ trả lời bằng chatbot, dự án đi theo hướng "data -> quant -> AI -> dashboard":

- Tầng dữ liệu thu thập và chuẩn hóa dữ liệu thị trường, vĩ mô và báo cáo tài chính.
- Tầng định lượng tính toán xác suất rủi ro, chế độ thị trường, biến động và các chỉ số giải thích mô hình.
- Tầng AI agent diễn giải kết quả, trả lời câu hỏi và điều phối theo từng chuyên môn.
- Tầng API và dashboard giúp người dùng cuối sử dụng toàn bộ hệ thống qua web.

Nói ngắn gọn, đây là một hệ thống hỗ trợ phân tích đầu tư và quản trị rủi ro có tính "neural-symbolic": mô hình máy học tạo tín hiệu, còn AI agent giúp biến tín hiệu thành thông tin dễ hiểu và có ngữ cảnh.

## 2. Bài toán dự án đang giải quyết

Nhà đầu tư và nhóm phân tích thường gặp 3 vấn đề:

- Dữ liệu nằm rời rạc ở nhiều nguồn: giá, tỷ giá, lãi suất, CPI, báo cáo tài chính.
- Chỉ số định lượng khó đọc với người dùng không chuyên sâu về mô hình.
- Dashboard thông thường thiếu khả năng tương tác thông minh, còn chatbot thông thường lại thiếu dữ liệu nội bộ và logic định lượng.

Dự án này giải quyết bằng cách gom dữ liệu, lượng hóa thành risk score, rồi cho AI agent giải thích trên cùng một hệ thống.

## 3. Giá trị cốt lõi

- Biến dữ liệu thị trường Việt Nam thành một pipeline phân tích thống nhất.
- Tạo risk score ngắn hạn cho VN-Index theo nhiều horizon: 1 tuần, 2 tuần, 1 tháng.
- Cho phép mô phỏng "what-if" với biến vĩ mô như tỷ giá USD/VND và lãi suất điều hành.
- Kết hợp phân tích báo cáo tài chính, so sánh peer và radar sức khỏe doanh nghiệp.
- Cung cấp chat AI theo nhiều vai trò chuyên môn thay vì chỉ một chatbot chung chung.
- Có dashboard web để demo trực tiếp, đồng thời có API và CLI để vận hành tự động.

## 4. Kiến trúc hệ thống

Luồng tổng thể của dự án:

`Data Ingestion -> Feature Engineering -> Quant Engine -> Multi-Agent / Narrative -> FastAPI -> React Dashboard`

### 4.1. Tầng dữ liệu

Tầng dữ liệu nằm trong `src/risk_dashboard/data/` và hiện có các nhóm chức năng chính:

- Kết nối dữ liệu thị trường từ CSV hoặc `vnstock`.
- Kết nối dữ liệu vĩ mô từ CSV, dữ liệu tự động hoặc nguồn chính thức.
- Đồng bộ dữ liệu giá cho watchlist qua `yfinance`.
- Đồng bộ dữ liệu cross-asset như vàng, bạc, BTC, ETH để đọc risk-on / risk-off.
- Thu thập và cache báo cáo tài chính doanh nghiệp về thư mục `data/financials/cache/`.
- ETL và materialize training panel để phục vụ huấn luyện và chạy EOD.

Điểm quan trọng là dự án không chỉ đọc dữ liệu một lần, mà có cơ chế cache cục bộ để phục vụ demo, nghiên cứu và tái sử dụng.

### 4.2. Tầng định lượng

Tầng quant nằm trong `src/risk_dashboard/quant/` và là lõi chuyên môn của hệ thống.

Các thành phần chính:

- `eod_pipeline.py`: chạy phân tích EOD tổng hợp.
- `xgb_engine.py`: xây feature và huấn luyện mô hình phân loại rủi ro theo nhiều horizon.
- `advanced_engine.py`: bổ sung HMM nhận diện regime, GARCH dự báo biến động và gợi ý allocation stock/cash.
- `scenario.py`: chạy lại mô hình khi override biến vĩ mô.
- `shap_explain.py`: giải thích feature nào đang chi phối risk score.
- `var_engine.py`: phân tích quan hệ VAR giữa VN-Index, tỷ giá và lãi suất.
- `model_benchmark.py`: benchmark mô hình và benchmark bộ feature.
- `backtest.py`: backtest buy-and-hold cho danh mục cổ phiếu Việt Nam.
- `financial_analysis.py`: phân tích chất lượng tài chính doanh nghiệp.
- `peer_compare.py`: so sánh một mã với nhóm peer.

Về mặt kỹ thuật, engine hiện dùng `HistGradientBoostingClassifier` của scikit-learn cho phần core risk model, dù tên module lịch sử vẫn là `xgb_engine.py`.

### 4.3. Tầng AI agent

Tầng agent nằm trong `src/risk_dashboard/agents/` và có 2 lớp ứng dụng khác nhau:

- Luồng public chat: chỉ phân tích, giải thích, không đưa khuyến nghị mua/bán.
- Trading Lab admin: môi trường sandbox để thảo luận chiến lược paper trading ở mức nghiên cứu.

Hệ thống agent hiện có các vai trò:

- `macro_agent`
- `fundamental_agent`
- `quant_risk_agent`
- `portfolio_agent`
- `sector_agent`
- `strategist_agent`

Ngoài ra còn có luồng `narrative + reviewer` để tạo bản tường thuật EOD và kiểm tra mức độ nhất quán với output định lượng.

Điểm hay của phần này là agent không trả lời mơ hồ, mà có tool gọi vào dữ liệu và quant engine trước khi diễn giải.

### 4.4. Tầng API và backend

Backend dùng `FastAPI`, nằm trong `src/risk_dashboard/api/main.py`.

Các nhóm API chính:

- System: health check, trạng thái panel.
- Dashboard: history, live feed, cross-asset, money flow.
- Quant: chạy EOD, rerun scenario, model report.
- Chat: multi-agent chat.
- Financials: trạng thái provider, phân tích ticker, peer compare, import dữ liệu.
- Backtest: chạy backtest danh mục.
- Watchlist: sync giá và trả dữ liệu OHLCV.
- Trading Lab admin: kiểm tra trạng thái, chat, thiết kế chiến lược.

Backend cũng có middleware cho:

- API key tùy chọn.
- Logging request.
- Kiểm soát riêng cho Trading Lab admin key.

### 4.5. Tầng frontend

Frontend nằm trong `frontend/`, dùng `React + Vite`.

Dashboard hiện đã có nhiều khu vực chức năng:

- Tổng quan rủi ro thị trường.
- Giải thích mô hình bằng SHAP.
- Mô phỏng kịch bản vĩ mô.
- Phân tích ngành và cổ phiếu.
- Phân tích báo cáo tài chính.
- Watchlist cá nhân với journal và checklist.
- Trading Lab sandbox.
- Backtest danh mục.

Frontend có thể chạy dev riêng trên Vite hoặc build để backend serve trực tiếp tại `/dashboard`.

## 5. Những chức năng nổi bật đang có

### 5.1. Phân tích rủi ro thị trường theo ngày

Hệ thống có thể chạy EOD cho một ngày cụ thể và trả về:

- Decision score.
- Risk regime.
- Xác suất giảm trong 1 tuần, 2 tuần, 1 tháng.
- Expected drawdown.
- SHAP top drivers.
- Tóm tắt VAR và backtest metrics.

### 5.2. Mô phỏng kịch bản vĩ mô

Người dùng có thể thay đổi:

- Tỷ giá USD/VND.
- Lãi suất điều hành.

Sau đó hệ thống chạy lại mô hình để xem risk score thay đổi như thế nào.

### 5.3. Giải thích mô hình

Hệ thống không chỉ đưa ra score mà còn cho biết feature nào đang là driver chính, ví dụ:

- Tỷ giá.
- Lãi suất.
- Biến động ngắn hạn.
- Độ rộng thị trường.
- Volume pressure.

### 5.4. Phân tích báo cáo tài chính doanh nghiệp

Dự án hiện hỗ trợ:

- Chuẩn hóa dữ liệu báo cáo tài chính từ provider hoặc JSON import.
- Tính nhiều chỉ số chất lượng tài chính.
- Phân tích DuPont.
- Altman Z-score.
- Piotroski F-score.
- Radar sức khỏe doanh nghiệp.
- So sánh peer theo nhóm mã.

### 5.5. Multi-agent chat

Người dùng có thể đặt câu hỏi dạng:

- "VN-Index hôm nay rủi ro thế nào?"
- "Nếu tỷ giá lên 25.500 thì sao?"
- "Rủi ro của FPT là gì?"
- "Danh mục này đang tập trung ở đâu?"

Agent sẽ route câu hỏi đúng chuyên môn và trả lời bằng tiếng Việt theo format phân tích.

### 5.6. Trading Lab cho admin

Trading Lab là phần mở rộng đáng chú ý của workspace hiện tại:

- Cho phép thảo luận thesis chiến lược trong sandbox.
- Có nhiều role như analyst, risk manager, stop-loss, portfolio designer.
- Có endpoint thiết kế blueprint chiến lược để đổ vào backtest.
- Không kết nối broker và không gửi lệnh thật.

### 5.7. Backtest danh mục

Hệ thống có thể backtest danh mục cổ phiếu Việt Nam theo kiểu buy-and-hold:

- Dùng dữ liệu giá điều chỉnh từ `yfinance`.
- Cho phép equal weight hoặc custom weights.
- Có thể so sánh với VN-Index.
- Trả equity curve, drawdown, rolling volatility, monthly returns.

### 5.8. Watchlist và cross-asset context

Workspace hiện tại đã có thêm:

- Cache OHLCV cho watchlist cá nhân.
- Đồng bộ dữ liệu theo ticker khi người dùng mở tab watchlist.
- Theo dõi vàng, bạc, BTC, ETH để đọc tín hiệu risk-on / risk-off ngoài thị trường Việt Nam.

Đây là phần giúp dashboard bớt "nội bộ VN-Index" và có góc nhìn rộng hơn về tâm lý thị trường.

## 6. Công nghệ sử dụng

### Backend

- Python 3.10+
- FastAPI
- Pydantic
- Pandas / NumPy
- scikit-learn
- SHAP
- statsmodels
- arch
- hmmlearn
- LangChain / LangGraph
- SQLite

### Frontend

- React
- Vite
- lightweight-charts

### Dữ liệu và vận hành

- vnstock
- yfinance
- Parquet
- Docker / Docker Compose
- Makefile

## 7. Hiện trạng dự án trong workspace này

Đây là tình trạng mình ghi nhận trực tiếp từ repo hiện tại, không chỉ dựa trên README:

- Backend package có khoảng `116` file trong `src/risk_dashboard/`.
- Frontend source có `8` file trong `frontend/src/`.
- Thư mục test hiện có `23` module test.
- Test suite collect được khoảng `44` test case.
- Có `33` artifact trong `data/models/`.
- Có `82` file cache báo cáo tài chính trong `data/financials/cache/`.
- Có `15` file cache dữ liệu trong `data/cache/`.
- Có SQLite registry tại `data/risk_dashboard.db`.
- Có Dockerfile đa stage để build frontend và backend cùng nhau.

Điều này cho thấy dự án đã vượt qua mức prototype rất sớm và đang ở giai đoạn một nền tảng nghiên cứu - demo - vận hành nội bộ khá đầy đủ.

## 8. Mức độ hoàn thiện hiện tại

Dự án đã có:

- Cấu trúc module rõ ràng.
- CLI để ingest, fetch, train, benchmark.
- API để tích hợp ngoài dashboard.
- Dashboard React có nhiều tab nghiệp vụ.
- Bộ test backend tương đối rộng.
- Dữ liệu mẫu, dữ liệu cache và model artifact thực tế.

Tuy nhiên, để giới thiệu trung thực, cần nói rõ một số điểm:

- Test suite hiện chạy ra `2` lỗi trong `tests/test_eod_pipeline.py`, tức là workspace hiện tại vẫn còn regression ở nhánh EOD/scenario.
- Một số API mang tính demo hoặc mock, ví dụ money flow hiện dùng dữ liệu mô phỏng hợp lý cho UI.
- Backtest hiện là paper backtest kiểu buy-and-hold, chưa mô phỏng phí giao dịch, trượt giá hay execution thực tế.
- Trading Lab là sandbox nghiên cứu, không có broker integration.
- Các luồng live và auto-fetch phụ thuộc vào nguồn bên ngoài như DNSE, yfinance, vnstock.

Nếu đi giới thiệu dự án, nên gọi đây là:

`Nền tảng phân tích rủi ro và trợ lý đầu tư cho thị trường Việt Nam, đang ở giai đoạn sản phẩm MVP+ / research platform có dashboard vận hành được.`

## 9. Điểm khác biệt của dự án

- Không chỉ là dashboard dữ liệu, mà có quant engine thật phía sau.
- Không chỉ là chatbot, mà AI agent được gắn với dữ liệu và tool chuyên môn.
- Có cả chiều rộng thị trường, vĩ mô, doanh nghiệp, danh mục và cross-asset trong một hệ thống.
- Thiết kế phù hợp cho cả demo sản phẩm, nghiên cứu định lượng và phát triển thành hệ thống nội bộ cho team phân tích.
- Có khả năng mở rộng từ use case "giải thích thị trường" sang "thiết kế chiến lược paper trading".

## 10. Nhóm người dùng phù hợp

- Nhà đầu tư cá nhân muốn đọc thị trường có hệ thống hơn.
- Nhóm research / investment office cần dashboard nội bộ.
- Đội ngũ phân tích rủi ro muốn thử nghiệm pipeline định lượng + AI.
- Tổ chức giáo dục / demo công nghệ tài chính.
- Startup fintech muốn phát triển nền tảng advisory hoặc insight engine cho thị trường Việt Nam.

## 11. Cách giới thiệu ngắn gọn dự án

### Phiên bản 30 giây

`Đây là một nền tảng phân tích rủi ro cho chứng khoán Việt Nam, kết hợp dữ liệu thị trường, mô hình định lượng và AI agent. Hệ thống có thể chấm risk score cho VN-Index, mô phỏng kịch bản tỷ giá/lãi suất, phân tích báo cáo tài chính doanh nghiệp, chat giải thích số liệu và hiển thị toàn bộ trên dashboard web.`

### Phiên bản 1-2 phút

`Dự án được xây theo pipeline hoàn chỉnh từ dữ liệu đến dashboard. Ở tầng dưới, hệ thống thu thập dữ liệu thị trường, vĩ mô, báo cáo tài chính và tạo training panel. Ở tầng giữa, quant engine chạy mô hình rủi ro nhiều horizon, HMM, GARCH, SHAP, VAR và backtest. Ở tầng trên, multi-agent AI diễn giải kết quả theo vai trò như macro, quant risk, fundamental hay portfolio. Toàn bộ được expose qua FastAPI và dashboard React. Workspace hiện tại còn có thêm watchlist cá nhân, cross-asset dashboard, backtest danh mục và Trading Lab sandbox cho admin.`

## 12. Hướng phát triển tiếp theo

Các bước hợp lý để nâng dự án lên production hơn:

- Sửa regression còn tồn tại ở EOD/scenario.
- Thay thế các phần mock bằng nguồn dữ liệu production ổn định.
- Bổ sung auth, phân quyền và audit log đầy đủ hơn.
- Tối ưu pipeline training, model registry và versioning.
- Bổ sung execution assumptions thực tế hơn cho backtest.
- Thêm cơ chế monitoring dữ liệu live và độ tin cậy nguồn dữ liệu.
- Chuẩn hóa phần frontend để hỗ trợ nhiều persona người dùng hơn.

## 13. Kết luận

`Risk Dashboard` hiện là một dự án fintech AI có nền tảng kỹ thuật khá đầy đủ: có dữ liệu, có quant engine, có multi-agent, có API, có dashboard và có các tính năng mở rộng như financial analysis, backtest, watchlist và Trading Lab.

Nếu giới thiệu ra bên ngoài, điểm mạnh nhất của dự án là khả năng kết nối giữa mô hình định lượng và trải nghiệm người dùng bằng AI. Đây không chỉ là một dashboard tài chính, mà là một hệ thống "ra tín hiệu + giải thích + tương tác" dành cho thị trường chứng khoán Việt Nam.

## 14. Feature Spec Kỹ Thuật: Data / Analytics / Monitoring

### 14.1. Mục tiêu module

Module `Data / Analytics / Monitoring` là lớp đo lường xuyên suốt cho toàn bộ sản phẩm public, pro và admin.

Mục tiêu:

- biến mọi hành vi chính trong sản phẩm thành event đo được;
- biết người dùng có đi từ `onboarding -> hiểu -> hành động -> quay lại` hay không;
- biết data, quant engine, AI layer và API có còn hoạt động ổn định hay không;
- tạo dashboard riêng cho `product`, `ops`, `trust/safety`;
- có alert/incident tier rõ ràng thay vì đợi lỗi runtime mới phản ứng.

Nguyên tắc:

- event schema dùng chung, có versioning;
- tách rõ `product analytics`, `ops monitoring`, `trust/safety telemetry`;
- KPI tính từ rollup snapshots, không query thẳng raw events cho mọi dashboard;
- event server-side là chuẩn chính, frontend event chỉ bổ sung khi cần UI interaction detail;
- mọi số liệu nhạy cảm phải đi qua layer privacy-safe, không log PII thô.

### 14.2. Boundaries và module structure

Backend module đề xuất:

`src/risk_dashboard/modules/analytics_monitoring/`

- `api/public.py`
- `api/admin.py`
- `application/event_ingest_service.py`
- `application/kpi_rollup_service.py`
- `application/ops_health_service.py`
- `application/alert_service.py`
- `application/dashboard_service.py`
- `domain/events.py`
- `domain/kpi_definitions.py`
- `domain/alert_rules.py`
- `infrastructure/repositories/sqlite.py`
- `schemas/requests.py`
- `schemas/responses.py`

Module này đọc từ:

- `home_onboarding`
- `financial_health`
- `goals`
- `learning`
- `guided_investing`
- `insights`
- `community`
- `pro_lab`
- `trust_safety`
- `admin_cms`

### 14.3. Event envelope chuẩn

Mọi event nên dùng envelope chung:

- `event_id`
- `event_name`
- `event_category`
- `schema_version`
- `timestamp`
- `module`
- `surface`
- `user_id`
- `session_id`
- `persona_segment`
- `route`
- `locale`
- `device_type`
- `source_surface`
- `target_surface`
- `properties_json`

Phân nhóm `event_category`:

- `product`
- `ops`
- `trust_safety`
- `admin`

Naming convention:

- dạng `snake_case`
- pattern: `<module>_<object>_<action>`

Ví dụ:

- `onboarding_completed`
- `financial_health_score_viewed`
- `goal_created`
- `learning_lesson_completed`
- `guided_market_context_viewed`
- `insight_card_opened`
- `community_post_blocked`
- `pro_lab_experiment_run`

### 14.4. Event taxonomy chi tiết

#### Onboarding

- `onboarding_started`
- `onboarding_step_viewed`
- `onboarding_step_answered`
- `onboarding_back_clicked`
- `onboarding_completed`
- `persona_assigned`
- `primary_route_assigned`
- `home_loaded_after_onboarding`

`properties_json` tối thiểu:

- `step_key`
- `answer_value`
- `persona`
- `route`
- `knowledge_level`
- `completion_time_sec`

#### Financial Health

- `financial_health_started`
- `financial_health_input_completed`
- `financial_health_score_viewed`
- `financial_health_subscore_expanded`
- `financial_health_flag_viewed`
- `financial_health_next_action_clicked`
- `financial_health_goal_cta_clicked`
- `financial_health_coach_opened`
- `financial_health_coach_reply_viewed`

Properties:

- `health_score`
- `score_band`
- `flag_codes`
- `next_action_code`
- `investment_readiness`

#### Goals

- `goal_created`
- `goal_viewed`
- `goal_recomputed`
- `goal_checkin_completed`
- `goal_planner_opened`
- `goal_planner_reply_viewed`
- `goal_next_action_clicked`
- `goal_offtrack_viewed`
- `goal_reminder_read`
- `goal_reminder_dismissed`

Properties:

- `goal_id`
- `goal_type`
- `currency`
- `feasibility_band`
- `months_remaining`
- `monthly_contribution_needed`

#### Learning

- `learning_home_viewed`
- `learning_path_started`
- `learning_lesson_opened`
- `learning_lesson_completed`
- `learning_quiz_started`
- `learning_quiz_submitted`
- `learning_quiz_passed`
- `learning_glossary_opened`
- `learning_contextual_explainer_viewed`
- `learning_tutor_opened`
- `learning_tutor_reply_viewed`
- `learning_coach_nudge_clicked`

Properties:

- `path_id`
- `lesson_id`
- `quiz_score`
- `difficulty_level`
- `content_type`
- `trigger_surface`

#### Guided Investing

- `guided_investing_home_viewed`
- `guided_investing_eligibility_checked`
- `guided_market_context_viewed`
- `guided_watchlist_item_added`
- `guided_watchlist_review_viewed`
- `guided_company_health_viewed`
- `guided_portfolio_saved`
- `guided_portfolio_review_submitted`
- `guided_journal_created`
- `guided_safe_chat_opened`
- `guided_safe_chat_blocked`
- `guided_contextual_lesson_clicked`

Properties:

- `eligible`
- `ticker`
- `watchlist_count`
- `scenario_label`
- `portfolio_concentration_band`
- `blocked_reason`

#### Insights

- `insights_home_viewed`
- `insight_card_opened`
- `insight_driver_expanded`
- `insight_scenario_opened`
- `insight_company_viewed`
- `insight_learn_clicked`
- `insight_guided_clicked`
- `insight_risk_banner_viewed`

Properties:

- `insight_id`
- `insight_type`
- `level`
- `freshness_status`
- `quality_state`
- `confidence_label`
- `action_category`

#### Community

- `community_home_viewed`
- `community_space_joined`
- `community_post_created`
- `community_comment_created`
- `community_reply_created`
- `community_post_blocked`
- `community_post_held_for_review`
- `community_notification_read`
- `community_notification_dismissed`
- `community_challenge_progress_viewed`

Properties:

- `space_id`
- `space_type`
- `moderation_status`
- `risk_labels`
- `challenge_id`
- `notification_type`

#### Pro / Lab

- `pro_lab_workspace_viewed`
- `pro_lab_blueprint_created`
- `pro_lab_blueprint_updated`
- `pro_lab_blueprint_archived`
- `pro_lab_blueprint_compared`
- `pro_lab_experiment_run`
- `pro_lab_report_exported`
- `pro_lab_session_revoked`
- `pro_lab_admin_review_completed`

Properties:

- `blueprint_id`
- `experiment_id`
- `scenario_type`
- `benchmark_id`
- `review_status`
- `token_scope`

### 14.5. Operational metrics taxonomy

Ngoài product event, cần có ops snapshots định kỳ:

- `ops_data_freshness_snapshot`
- `ops_api_health_snapshot`
- `ops_model_latency_snapshot`
- `ops_moderation_queue_snapshot`
- `ops_alert_triggered`
- `ops_alert_resolved`

Metrics cốt lõi:

- `minutes_since_last_refresh`
- `freshness_status`
- `success_rate`
- `error_rate`
- `p50_latency_ms`
- `p95_latency_ms`
- `timeout_rate`
- `fallback_rate`
- `stale_rate`
- `pending_queue_count`
- `oldest_pending_minutes`

### 14.6. DB schema đề xuất

#### `analytics_events`

- `event_id TEXT PRIMARY KEY`
- `event_name TEXT NOT NULL`
- `event_category TEXT NOT NULL`
- `schema_version INTEGER NOT NULL`
- `timestamp TEXT NOT NULL`
- `module TEXT NOT NULL`
- `surface TEXT NOT NULL`
- `user_id TEXT NULL`
- `session_id TEXT NULL`
- `persona_segment TEXT NULL`
- `route TEXT NULL`
- `locale TEXT NULL`
- `device_type TEXT NULL`
- `source_surface TEXT NULL`
- `target_surface TEXT NULL`
- `properties_json TEXT NOT NULL`

Indexes:

- `(event_name, timestamp)`
- `(module, timestamp)`
- `(surface, timestamp)`
- `(user_id, timestamp)`
- `(session_id, timestamp)`

#### `ops_metric_snapshots`

- `snapshot_id TEXT PRIMARY KEY`
- `metric_name TEXT NOT NULL`
- `metric_group TEXT NOT NULL`
- `surface TEXT NULL`
- `status TEXT NOT NULL`
- `value REAL NOT NULL`
- `unit TEXT NOT NULL`
- `captured_at TEXT NOT NULL`
- `meta_json TEXT NULL`

Indexes:

- `(metric_name, captured_at)`
- `(metric_group, captured_at)`
- `(surface, captured_at)`

#### `analytics_kpi_snapshots`

- `snapshot_id TEXT PRIMARY KEY`
- `kpi_name TEXT NOT NULL`
- `window_grain TEXT NOT NULL`
- `window_start TEXT NOT NULL`
- `window_end TEXT NOT NULL`
- `value REAL NOT NULL`
- `segment_key TEXT NULL`
- `segment_value TEXT NULL`
- `meta_json TEXT NULL`
- `created_at TEXT NOT NULL`

Indexes:

- `(kpi_name, window_grain, window_end)`
- `(segment_key, segment_value, window_end)`

#### `ops_alert_events`

- `alert_id TEXT PRIMARY KEY`
- `rule_name TEXT NOT NULL`
- `severity_tier TEXT NOT NULL`
- `surface TEXT NULL`
- `status TEXT NOT NULL`
- `summary TEXT NOT NULL`
- `details_json TEXT NULL`
- `triggered_at TEXT NOT NULL`
- `resolved_at TEXT NULL`

Indexes:

- `(status, triggered_at)`
- `(severity_tier, triggered_at)`
- `(surface, triggered_at)`

### 14.7. API contracts

#### Public ingest

`POST /api/v1/public/analytics/events`

Request:

```json
{
  "events": [
    {
      "event_name": "learning_lesson_opened",
      "event_category": "product",
      "schema_version": 1,
      "timestamp": "2026-04-19T08:30:00Z",
      "module": "learning",
      "surface": "learning",
      "session_id": "sess_123",
      "persona_segment": "starter",
      "properties": {
        "lesson_id": "risk-basics-01",
        "path_id": "starter-finance-path"
      }
    }
  ]
}
```

Response:

```json
{
  "accepted": 1,
  "rejected": 0
}
```

#### Admin metrics

- `GET /admin/analytics/status`
- `GET /admin/analytics/kpis?window=day`
- `GET /admin/analytics/kpis/{kpi_name}`
- `GET /admin/analytics/ops/freshness`
- `GET /admin/analytics/ops/api-health`
- `GET /admin/analytics/ops/moderation`
- `GET /admin/analytics/alerts`

#### Internal jobs

- `POST /admin/analytics/jobs/run-kpi-rollup`
- `POST /admin/analytics/jobs/run-ops-snapshot`
- `POST /admin/analytics/jobs/evaluate-alerts`

### 14.8. KPI tree

#### Acquisition

- landing -> onboarding start rate
- onboarding start volume
- home reached rate

#### Activation

- onboarding completion rate
- financial health completion rate
- first lesson completion rate
- first goal creation rate
- first guided action rate
- `time_to_first_meaningful_action`

#### Retention

- D1 / D7 / D30 retention
- weekly active users
- home revisit rate
- learning revisit rate
- community challenge return rate

#### Learning completion

- lesson completion rate
- path completion rate
- quiz pass rate
- tutor helpfulness rate
- learning-to-action conversion

#### Insight usage

- insight open rate
- repeat insight visits
- driver expand rate
- insight -> learn CTR
- insight -> guided CTR

#### Trust / Safety

- unsafe prompt rate
- safe redirect success rate
- stale insight exposure rate
- missing disclaimer rate
- moderation SLA
- harmful content incident count

#### Conversion

- public -> activated
- activated -> retained weekly
- guided eligible -> guided user
- pro eligible -> pro token created
- pro workspace view -> experiment run

### 14.9. KPI rollup jobs

Nên có 3 loại job:

#### Hourly rollup

- event counts theo module/surface
- error rate theo endpoint
- stale insight rate
- moderation queue volume

#### Daily rollup

- funnel conversion
- retention cohorts
- learning completion
- trust/safety summary

#### Weekly rollup

- WAU
- weekly guided active users
- weekly active learners
- challenge participation
- premium/pro conversion

### 14.10. Operational monitoring spec

#### Data freshness

Theo source:

- market panel
- macro source
- cross-asset source
- financial dataset
- insights runtime snapshot
- scenario cache

Core metric:

- `minutes_since_last_refresh`
- `freshness_status`
- `stale_surface_count`

#### API uptime

Theo endpoint group:

- public
- pro
- admin

Core metric:

- `request_count`
- `success_rate`
- `p50_latency_ms`
- `p95_latency_ms`
- `error_rate`
- `timeout_rate`

#### Model / AI latency

- tutor latency
- coach latency
- analyst latency
- pro assistant latency
- quant rerun latency
- report export latency

#### Moderation / trust ops

- held-for-review volume
- open incidents by severity
- frozen surfaces count
- degraded surfaces count
- default disclaimer injection spike

### 14.11. Dashboard spec

#### Product dashboard

Sections:

- acquisition funnel
- activation funnel
- module engagement
- learning completion
- insights usage
- guided investing usage
- conversion summary
- trust overlay

Primary charts:

- funnel chart
- D1/D7 retention
- WAU by module
- lesson completion trend
- insight CTR trend

#### Ops dashboard

Sections:

- API health
- data freshness
- model latency
- fallback/stale rates
- moderation queue
- alert timeline

Primary charts:

- p95 latency by endpoint group
- stale rate by surface
- freshness heatmap by source
- queue backlog trend

#### Trust / Safety dashboard

Sections:

- blocked unsafe prompts
- community harmful content
- missing disclaimer incidents
- surfaces in freeze/degrade
- incident aging

Primary charts:

- incidents by severity
- blocked content trend
- safe redirect rate
- open incidents SLA buckets

### 14.12. Alert rules và severity tiers

#### Severity tiers

- `SEV1`: outage hoặc trust incident nghiêm trọng có ảnh hưởng public rộng
- `SEV2`: degradation lớn, stale/fallback tăng mạnh, queue critical
- `SEV3`: degradation cục bộ hoặc latency tăng kéo dài
- `SEV4`: issue nhỏ, cần theo dõi

#### Rule examples

- `public_api_error_rate > 5% trong 5 phút` -> `SEV1`
- `insight_stale_rate > 20% trong 15 phút` -> `SEV2`
- `guided_market_context_unavailable > 10% trong 10 phút` -> `SEV2`
- `p95_ai_assistant_latency > 4000ms trong 10 phút` -> `SEV3`
- `moderation_queue_pending > 100` -> `SEV2`
- `critical_trust_incidents_open > 0` -> `SEV1`
- `default_disclaimer_injections > baseline x3` -> `SEV3`

### 14.13. Privacy và logging rules

- không log raw OTP, số tài khoản, CCCD, phone number nếu phát hiện trong text input;
- properties nhạy cảm chỉ lưu dạng band hoặc code, không lưu text tự do nếu không cần;
- community text khi cần analytics nên log moderation labels, không cần giữ nguyên nội dung dài;
- report export/pro actions phải log actor, scope, experiment id, nhưng không log secrets/token;
- mọi event schema thay đổi phải tăng `schema_version`.

### 14.14. MVP stack đề xuất

Để ship nhanh:

- storage: SQLite app-state hiện tại;
- ingest: backend endpoint ghi vào `analytics_events`;
- rollups: cron hoặc admin-triggered jobs trong backend;
- dashboards: admin API + frontend admin page;
- alerts: threshold-based records trong `ops_alert_events`, chưa cần Slack/email ngay;
- export/query nâng cao có thể thêm sau khi chuyển sang Postgres/warehouse.

### 14.15. Thứ tự triển khai khuyến nghị

#### Phase 1

- event ingest API
- `analytics_events`
- core product events cho onboarding, health, goals, learning
- daily KPI rollup

#### Phase 2

- guided/insights/community/pro events
- ops snapshots
- trust/safety metrics
- admin dashboards

#### Phase 3

- alert rules
- incident dashboard linkages
- warehouse/export support
- experiment analysis và cohort slicing sâu hơn

### 14.16. Quyết định chốt

Nếu build đúng, module này sẽ trả lời được 4 câu hỏi quan trọng:

- user có bắt đầu và đi đúng hành trình không;
- user có học xong và chuyển thành hành động không;
- user có quay lại đều không;
- data, API, AI và moderation có còn đủ ổn định để public-safe không.

Đây là module bắt buộc nếu muốn biến sản phẩm từ một app có nhiều tính năng thành một hệ thống có thể vận hành, đo lường và tối ưu được.
