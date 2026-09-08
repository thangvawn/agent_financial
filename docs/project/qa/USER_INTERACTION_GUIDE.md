# Hướng Dẫn Tương Tác Người Dùng & AI Agent (User Interaction Guide)
## Northstar Finance Lab — Hệ Thống Đa Tác Tử Định Lượng (Agentic Quantum)

> **Loại tài liệu:** Hướng dẫn Vận hành & Trải nghiệm Sản phẩm (Product UI/UX & Interaction Guide)  
> **Dự án:** Northstar Finance Lab — Agentic Quantum  
> **Định vị:** Phòng thí nghiệm Nghiên cứu & Giáo dục Tài chính Định lượng (AI Quant Finance Learning Lab)  
> **Trạng thái:** Bản chuẩn hóa (Canonical Reference)  
> **Mục tiêu độc giả:** Học viên, Nhà nghiên cứu định lượng, Giảng viên, Kỹ sư Sản phẩm & Kiểm thử viên (QA/QC)

---

## Tuyên Bố Định Vị & Giới Hạn Cốt Lõi (System Identity)

> [!IMPORTANT]
> **ĐỊNH VỊ SẢN PHẨM & TUYÊN BỐ KHƯỚC TỪ TRÁCH NHIỆM:**
> 1. **Mục đích duy nhất là Giáo dục & Nghiên cứu:** Northstar Finance Lab là môi trường học tập và mô phỏng thực nghiệm tài chính định lượng (Quantitative Finance). Nền tảng **KHÔNG** cung cấp dịch vụ tư vấn đầu tư, **KHÔNG** đưa ra khuyến nghị mua/bán chứng khoán, và **KHÔNG** ủy thác quản lý tài sản dưới bất kỳ hình thức nào.
> 2. **Ý nghĩa thuật ngữ "Quantum":** "Quantum" trong hệ thống đại diện cho **Tài chính định lượng (Quantitative Finance)**, kinh tế lượng (Econometrics) và mô hình hóa rủi ro toán học. Hệ thống **TUYỆT ĐỐI KHÔNG** sử dụng hay liên kết với phần cứng Máy tính lượng tử (Quantum Computing), vi mạch Qubit hay thuật toán lượng tử vật lý.
> 3. **Không giao dịch thực tế (Zero Live Execution):** Mọi chức năng mô phỏng, thử nghiệm chiến lược và quản lý danh mục đều vận hành trên môi trường giả lập (Paper Sandbox). Hệ thống không kết nối với bất kỳ cổng đặt lệnh (broker gateway) hay tài khoản giao dịch tiền thật nào.

---

## 1. Tổng Quan Kiến Trúc & Hai Chế Độ Tương Tác (Interaction Modes)

Hệ thống cung cấp một lớp trợ lý thông minh thống nhất (**Agentic Assistance Layer**) xuyên suốt toàn bộ vòng đời học tập và nghiên cứu. Để tối ưu hóa trải nghiệm người dùng, hệ thống phân tách rõ rệt giữa hai phương thức tương tác:

```text
+-----------------------------------------------------------------------------------+
|                        NORTHSTAR FINANCE LAB WORKSPACE                            |
+-----------------------------------------------------------------------------------+
       |                                                            |
       v                                                            v
+-----------------------------+              +--------------------------------------+
|     CONVERSATIONAL MODE     |              |        EMBEDDED WORKFLOW MODE        |
|      (AI Tutor Drawer)      |              |      (Contextual In-Screen Agent)    |
+-----------------------------+              +--------------------------------------+
| • Hỏi đáp khái niệm tự do   |              | • Nhúng trực tiếp tại màn hình       |
| • Phương pháp Socratic      |              | • Bắt trọn ngữ cảnh thực tế          |
| • Không mớm đáp án          |              | • Kích hoạt qua nút bấm nghiệp vụ    |
| • Gợi mở tư duy định lượng  |              | • Sinh Artifact & Action Proposal    |
+-----------------------------+              +--------------------------------------+
       \                                                            /
        \                                                          /
         v                                                        v
+-----------------------------------------------------------------------------------+
|                     AGENTIC CORE & TRUSTED EXECUTION ENVELOPE                     |
|  - Định danh xác thực (AuthPrincipal)        - Đóng gói bối cảnh an toàn          |
|  - Bộ công cụ xác định (Deterministic Tools)  - Kiểm định số liệu (Reviewers)      |
+-----------------------------------------------------------------------------------+
                                       |
                                       v
+-----------------------------------------------------------------------------------+
|                      THÀNH PHẦN GIAO DIỆN KIỂM CHỨNG (UI)                         |
|  [AgentRunPanel]           --->  [AgentArtifactCard]    --->  [EvidenceDrawer]    |
|  (Tiến trình & Trạng thái)       (Tóm tắt kết quả)            (Bằng chứng số liệu)|
|                                       |                                           |
|                                       +---------------->  [ActionProposalReview]  |
|                                                           (Xác nhận tác vụ ghi)   |
+-----------------------------------------------------------------------------------+
```

### 1.1. Chế Độ Hội Thoại (Conversational Mode — AI Tutor)
* **Bản chất:** Đóng vai trò như một người thầy hướng dẫn học thuật đồng hành (Academic Coach).
* **Phương pháp sư phạm:** Vận dụng triệt để phương pháp gợi mở **Socratic Method**. Khi người học gặp câu hỏi hóc búa hoặc bài tập mô phỏng, AI Tutor không cung cấp đáp án có sẵn mà đặt các câu hỏi định hướng, gợi ý từng bước (staged hints), chỉ ra các giả định ẩn và khuyến khích người học tự tìm ra lời giải.
* **Giao diện hiển thị:** Cửa sổ nổi (Floating Widget) hoặc Ngăn kéo hội thoại chuyên dụng (AI Tutor Drawer) có thể mở/đóng tại bất kỳ vị trí nào trên màn hình làm việc.
* **Bộ nhớ học tập (Learning Memory):** Ghi nhớ có kiểm soát tiến trình bài học, các lỗ hổng kiến thức thường gặp của học viên để điều chỉnh văn phong và mức độ nông sâu của bài giảng.

### 1.2. Chế Độ Quy Trình Nhúng (Embedded Workflow Mode)
* **Bản chất:** Đóng vai trò như một trợ lý chuyên môn định lượng (Quant Research Specialist) được tích hợp sẵn tại từng điểm nút tác vụ.
* **Đặc tính nhận thức ngữ cảnh (Context-Aware):** Agent tự động trích xuất trạng thái hoạt động trên màn hình người dùng: mã cổ phiếu đang xem, kỳ báo cáo tài chính được chọn, dòng chỉ tiêu đang kiểm tra, hoặc các tham số backtest vừa cấu hình.
* **Phương thức kích hoạt:** Không yêu cầu người dùng phải gõ prompt phức tạp. Kích hoạt trực tiếp thông qua các nút thao tác nghiệp vụ ngữ cảnh (Contextual CTAs) như: `[Giải thích chỉ tiêu này]`, `[Kiểm định vi phạm giả định]`, `[Tạo bản ghi nhớ bằng chứng]`.
* **Đầu ra chuyên biệt:** Thay vì trả về văn bản dài dòng, Agent tạo ra các thực thể dữ liệu có cấu trúc gọi là **Artifacts** (bản tóm tắt, bảng đối chiếu, thẻ hành động) và các đề xuất thay đổi dữ liệu có kiểm soát (**Action Proposals**).

### 1.3. Bảng So Sánh Hai Chế Độ Tương Tác

| Tiêu chí | Chế độ Hội thoại (Conversational Mode) | Chế độ Quy trình Nhúng (Embedded Workflow) |
| :--- | :--- | :--- |
| **Vai trò chính** | Thầy hướng dẫn học tập (AI Tutor / Coach) | Trợ lý phân tích định lượng tại chỗ (Task Specialist) |
| **Vị trí UI** | Global Floating Panel / Drawer trượt | Nằm ngay trong khối nghiệp vụ của trang |
| **Cách kích hoạt** | Nhập văn bản câu hỏi, chọn gợi ý học tập | Bấm nút hành động ngữ cảnh (Contextual CTA) |
| **Phạm vi ngữ cảnh** | Lịch sử cuộc trò chuyện + Tiến độ học tập | Toàn bộ dữ liệu hiển thị trên màn hình hiện tại |
| **Phương thức phản hồi** | Đoạn văn bản gợi mở Socratic, công thức KaTeX | Artifacts có cấu trúc, thẻ bằng chứng, đề xuất ghi |
| **Quyền ghi dữ liệu** | Chỉ ghi nhận phản hồi và đánh giá sau kiểm tra | Đề xuất tác vụ ghi (`ActionProposal`) cần người dùng duyệt |

---

## 2. Hướng Dẫn Chi Tiết Cho Từng Bề Mặt Nghiệp Vụ (Surfaces)

Hệ thống chia làm 6 phân hệ (Surfaces). Mỗi phân hệ phục vụ một mục tiêu nghiên cứu riêng biệt, với ranh giới an toàn được kiểm soát chặt chẽ.

```text
+------------------------------------------------------------------------------------+
|                                CÁC BỀ MẶT NGHIỆP VỤ                                |
+------------------+------------------+------------------+---------------------------+
| 1. Home Journey  | 2. Learn Hub     | 3. BCTC Workspace| 4. Simulation Lab         |
| Hành trình gợi mở| Bài học & Tutor  | Bóc tách BCTC    | Nghiên cứu chiến lược     |
+------------------+------------------+------------------+---------------------------+
| 5. News Intelligence                | 6. Market & Portfolio                        |
| Lọc nhiễu & Bóc tách sự kiện vĩ mô  | Giám sát thị trường & Danh mục thử nghiệm    |
+-------------------------------------+----------------------------------------------+
```

---

### 2.1. Phân Hệ Home (Home Journey & Onboarding)

* **Mục tiêu:** Định hướng lộ trình nghiên cứu cá nhân hóa, gợi ý "Hành động tối ưu tiếp theo" (Next-Best-Action) dựa trên dữ liệu hoàn thành thực tế, loại bỏ trạng thái hoang mang khi bắt đầu phiên làm việc.
* **Cách kích hoạt Agent:**
  * Tự động khởi chạy khi tải trang chủ sau khi xác thực thành công.
  * Hoặc người dùng bấm nút `[Làm mới đề xuất học tập]` tại góc phải thẻ hành trình.
* **Loại Artifact / Output nhận được:**
  * **Thẻ hành động tối ưu (`NextBestActionCardV1`):** Hiển thị rõ tiêu đề nhiệm vụ, lý do khuyến nghị dựa trên bằng chứng, liên kết trực tiếp (Deeplink) tới bài học hoặc mô phỏng, và thời hạn hết hạn của đề xuất.
* **Quy trình tương tác người dùng:**
  1. Người học xem thẻ đề xuất tại trung tâm màn hình Home.
  2. Đọc khối giải thích lý do: *"Hôm qua bạn vừa hoàn thành bài học về Tỷ suất sinh lời, bước tiếp theo là thực hành tính toán độ biến động lịch sử trên Simulation Lab"*.
  3. Người học có 3 lựa chọn tương tác:
     * Bấm `[Bắt đầu ngay]`: Chuyển hướng thẳng tới bài tập liên quan.
     * Bấm `[Để sau (Snooze)]`: Tạm ẩn thẻ trong vòng 24 giờ.
     * Bấm `[Đổi chủ đề khác]`: Yêu cầu Agent đề xuất hành động theo lộ trình song song.
* **Ranh giới cấm (Forbidden Actions):**
  * ❌ Tuyệt đối cấm Agent tự ý suy diễn tình trạng tài sản, thu nhập hay mức độ rủi ro tài chính của cá nhân.
  * ❌ Tuyệt đối cấm tạo thông điệp hối thúc, giục giã hoặc gợi ý các hành động đầu tư mang tính FOMO.
  * ❌ Tuyệt đối cấm chạy các tác vụ chạy ngầm định kỳ (Background Cron/Daemon) khi người dùng không mở trang.

---

### 2.2. Phân Hệ Học Tập (Learn Hub)

* **Mục tiêu:** Giúp học viên nắm vững lý thuyết kinh tế lượng, mô hình định lượng và phân tích tài chính thông qua phản hồi sư phạm hai chiều.
* **Cách kích hoạt Agent:**
  * Bôi đen một đoạn lý thuyết hoặc công thức toán -> Click menu nổi `[Giải thích cho tôi]`.
  * Tại các bài tập trắc nghiệm/tình huống -> Bấm nút `[Cần gợi ý Socratic]`.
  * Sau khi hoàn thành bài đọc -> Bấm `[Kiểm tra mức độ hiểu (Checkpoint)]`.
* **Loại Artifact / Output nhận được:**
  * **Bản mổ xẻ công thức (`FormulaWalkthrough`):** Phân rã công thức toán thành các biến số, đơn vị đo, điều kiện biên và ý nghĩa kinh tế.
  * **Gợi ý từng bước (`SocraticHint`):** Gợi mở các mối quan hệ nguyên nhân - kết quả mà không làm lộ đáp án trắc nghiệm.
  * **Thẻ đánh giá Checkpoint (`CheckpointReview`):** Bảng tổng hợp các điểm đã nắm vững và các điểm còn hiểu sai lệch (Misconceptions).
* **Quy trình tương tác người dùng:**
  ```text
  [Chọn đoạn văn/công thức] ---> [Bấm "Giải thích cho tôi"] 
       ---> [AgentRunPanel hiển thị] 
       ---> [Hiển thị bảng giải thích có nguồn dẫn giáo trình]
       ---> [Học viên trả lời câu hỏi đối thoại của AI]
       ---> [Agent đề xuất lưu Checkpoint thành công vào hồ sơ]
  ```
* **Ranh giới cấm (Forbidden Actions):**
  * ❌ Tuyệt đối cấm tiết lộ đáp án đúng của câu hỏi kiểm tra (`correct_answer` được bảo vệ nghiêm ngặt tại Backend, Agent không thể truy cập).
  * ❌ Tuyệt đối cấm Agent tự ý đánh dấu người dùng "Đã vượt qua bài học" nếu người dùng chưa hoàn thành câu hỏi kiểm chứng xác định.

---

### 2.3. Phân Hệ Phân Tích BCTC (BCTC Workspace)

* **Mục tiêu:** Hỗ trợ đọc hiểu báo cáo tài chính doanh nghiệp niêm yết có đối chiếu số liệu nguồn, phân rã chỉ số kế toán và đánh giá chất lượng lợi nhuận (Earnings Quality).
* **Cách kích hoạt Agent:**
  * Tại bảng Báo cáo kết quả kinh doanh / Cân đối kế toán: Chọn một dòng chỉ tiêu -> Bấm biểu tượng 💡 `[Bóc tách chỉ tiêu]`.
  * Chọn 2 hoặc nhiều quý trên thanh công cụ -> Bấm nút `[So sánh kỳ & Phân tích nguyên nhân]`.
  * Tại tab Phân tích tỷ số -> Bấm `[Đánh giá chất lượng lợi nhuận (Quality of Earnings)]`.
* **Loại Artifact / Output nhận được:**
  * **Thẻ chỉ tiêu kế toán (`LineItemExplanation`):** Định nghĩa chuẩn mực kế toán (VAS/IFRS), công thức tính toán, quy tắc ghi nhận doanh thu/chi phí và các cảnh báo bóp méo số liệu thường gặp.
  * **Bản ghi nhớ chất lượng lợi nhuận (`EarningsQualityMemo`):** Đối chiếu tương quan giữa Lợi nhuận thuần và Dòng tiền thuần từ hoạt động kinh doanh (CFO), phát hiện các tín hiệu cảnh báo (Red Flags) như tăng trưởng tồn kho vượt trội doanh thu.
* **Quy trình tương tác người dùng:**
  1. Người dùng chọn mã cổ phiếu (ví dụ: `FPT`) và niên độ báo cáo.
  2. Bấm `[Đánh giá chất lượng lợi nhuận]`.
  3. Hệ thống kích hoạt `bctc.resolve_report` và `bctc.calculate_ratio` lấy dữ liệu xác định từ Engine.
  4. `<AgentRunPanel />` hiển thị quá trình đối chiếu.
  5. Thẻ `AgentArtifactCard` xuất hiện. Người dùng bấm vào thẻ để mở `<EvidenceDrawer />` kiểm tra từng con số với BCTC gốc.
* **Ranh giới cấm (Forbidden Actions):**
  * ❌ Tuyệt đối cấm Agent tự bịa đặt, ngoại suy các con số ngoài báo cáo chính thức đã công bố.
  * ❌ Tuyệt đối cấm đưa ra kết luận khẳng định doanh nghiệp gian lận hay vi phạm pháp luật; chỉ được nêu các sai lệch định lượng cần đối chiếu thêm.
  * ❌ Tuyệt đối cấm đưa ra khuyến nghị mua, bán, nắm giữ hoặc định giá mục tiêu cổ phiếu.

---

### 2.4. Phòng Thí Nghiệm Mô Phỏng (Simulation Lab)

* **Mục tiêu:** Hỗ trợ người học xây dựng khung nghiên cứu chiến lược (Hypothesis Framing), rà soát các cạm bẫy phương pháp luận (Overfitting, Data Leakage, Look-ahead Bias) và đọc hiểu báo cáo kết quả kiểm thử (Backtest Review).
* **Cách kích hoạt Agent:**
  * Sau khi cấu hình tham số chiến lược (vũ trụ cổ phiếu, khung thời gian, điều kiện vào/ra lệnh) -> Bấm nút `[Kiểm tra tiền trạm (Preflight Validation)]`.
  * Tại màn hình kết quả chạy Backtest -> Bấm nút `[Phê bình chiến lược (Result Critique)]`.
  * Chọn 2 phiên chạy trong lịch sử -> Bấm nút `[So sánh các phiên chạy (Compare Runs)]`.
* **Loại Artifact / Output nhận được:**
  * **Bản kiểm tra tiền trạm (`PreflightChecklist`):** Cảnh báo về vi phạm giả định thống kê, độ dài dữ liệu không đủ hoặc tần suất giao dịch phi thực tế.
  * **Bản đánh giá rủi ro (`BacktestCritiqueArtifact`):** Đánh giá mức độ sụt giảm tài sản tối đa (Max Drawdown), tỷ số Sharpe thực tế sau khi trừ chi phí trượt giá và phí giao dịch giả định.
  * **Đề xuất chạy mô phỏng (`ActionProposal`):** Đề xuất tinh chỉnh tham số để kiểm tra tính bền vững (Stress Testing).
* **Quy trình tương tác người dùng:**
  ```text
  [Cấu hình tham số chiến lược] ---> [Bấm "Preflight Validation"]
       ---> [Nhận Checklist cảnh báo thiên lệch dữ liệu]
       ---> [Sửa tham số theo gợi ý]
       ---> [Bấm "Chạy Backtest"]
       ---> [Hộp thoại ActionProposalReview xuất hiện]
       ---> [Người dùng kiểm tra thông số tài nguyên & bấm "Confirm Action"]
       ---> [Hệ thống chạy Backtest xác định và xuất báo cáo kiểm chứng]
  ```
* **Ranh giới cấm (Forbidden Actions):**
  * ❌ Tuyệt đối cấm liên kết tài khoản chứng khoán hoặc sinh lệnh giao dịch thật ra thị trường.
  * ❌ Tuyệt đối cấm cam kết hoặc ngụ ý rằng chiến lược đem lại lợi nhuận thật trong tương lai.
  * ❌ Tuyệt đối cấm tự động kích hoạt tiến trình Backtest nặng mà không có sự nhấn xác nhận từ người dùng.

---

### 2.5. Phân Hệ Tin Tức Tình Báo (News Intelligence)

* **Mục tiêu:** Chắt lọc thông tin vĩ mô và doanh nghiệp, phân tách rạch ròi giữa dữ kiện thực tế (Fact) và tin đồn/nhận định (Claim), gắn nhãn mức độ quan trọng và liên kết với các bài học kinh tế.
* **Cách kích hoạt Agent:**
  * Tại màn hình luồng tin: Chọn một cụm tin tức (News Cluster) -> Bấm nút `[Tạo tóm tắt đa nguồn (Multi-Source Brief)]`.
  * Đọc một bài báo chi tiết -> Bấm nút `[Bóc tách tác động ngành (Impact Analysis)]`.
* **Loại Artifact / Output nhận được:**
  * **Bản tóm tắt bằng chứng tin tức (`NewsEvidenceBrief`):**
    * Bảng phân loại 3 tầng: Dữ kiện xác thực (Verified Facts), Tuyên bố của các bên (Claims), và Giả thuyết phân tích (Hypotheses).
    * Bảng điểm quan trọng (Importance Score) được tính toán bởi thuật toán miền xác định (Deterministic Scoring Engine).
    * Danh mục nguồn tin đối chiếu và các mắt xích thông tin còn thiếu (Information Gaps).
  * **Thẻ liên kết học tập (`LearnImpactLink`):** Gợi ý các bài học liên quan trong Learn Hub (ví dụ: tin về lãi suất điều hành sẽ liên kết tới bài học *"Cơ chế truyền dẫn chính sách tiền tệ"*).
* **Quy trình tương tác người dùng:**
  1. Người học xem luồng tin tức thị trường.
  2. Bấm vào cụm tin tức biến động tỷ giá.
  3. Chọn `[Tạo tóm tắt đa nguồn]`.
  4. Hệ thống chạy qua quy trình lọc mã độc ngôn ngữ (Prompt Injection Defense).
  5. Đọc bản Brief trong giao diện, đối chiếu các nguồn tin độc lập tại `EvidenceDrawer`.
* **Ranh giới cấm (Forbidden Actions):**
  * ❌ Tuyệt đối cấm Agent tự ý biến chỉ số tâm lý (Sentiment) hoặc tin tức thành khuyến nghị mua/bán cổ phiếu.
  * ❌ Tuyệt đối cấm Agent tự ý truy cập các đường dẫn URL ngoài hệ thống (Arbitrary Web Scraping).
  * ❌ Tuyệt đối cấm xem nội dung văn bản trong bài báo là chỉ dẫn điều khiển hệ thống (Bảo vệ chống Indirect Prompt Injection).

---

### 2.6. Phân Hệ Thị Trường & Danh Mục Thử Nghiệm (Market & Portfolio)

* **Mục tiêu:** Quan sát trạng thái thị trường tổng thể (Độ rộng thị trường, phân bổ dòng tiền) và phân tích rủi ro danh mục thử nghiệm (Paper Portfolio), đo lường mức độ tập trung và kịch bản sốc giá.
* **Cách kích hoạt Agent:**
  * Tại tab Giám sát thị trường -> Bấm nút `[Giải thích nhịp đập thị trường (Market Breadth Review)]`.
  * Tại tab Danh mục thử nghiệm (Paper Portfolio) -> Bấm nút `[Rà soát rủi ro tập trung & Sốc giá (Stress Test)]`.
* **Loại Artifact / Output nhận được:**
  * **Bản đánh giá danh mục thử nghiệm (`PortfolioReviewArtifactV1`):** Phân tích tỷ trọng tiền mặt/cổ phiếu, hệ số beta danh mục, mức độ nhạy cảm trước kịch bản VN-Index giảm 5%, 10% hoặc biến động lãi suất.
* **Quy trình tương tác người dùng:**
  1. Người học thiết lập một danh mục cổ phiếu thử nghiệm bằng tiền ảo (Paper Cash).
  2. Bấm `[Rà soát rủi ro tập trung]`.
  3. Agent phân tích các mã nắm giữ thông qua công cụ đọc dữ liệu xác định của `DataHub`.
  4. Xuất bản đánh giá nêu rõ: tỷ trọng ngành nào đang vượt ngưỡng an toàn học thuật (>25%), rủi ro thanh khoản khi thị trường biến động mạnh.
* **Ranh giới cấm (Forbidden Actions):**
  * ❌ Tuyệt đối cấm Agent tự động đặt lệnh mua/bán, hủy lệnh hay tái cân bằng danh mục thử nghiệm.
  * ❌ Tuyệt đối cấm Agent can thiệp hay chỉnh sửa Watchlist của người dùng mà không có lệnh trực tiếp.
  * ❌ Mọi phân tích phải hiển thị rõ nhãn cảnh báo: **"Danh mục mô phỏng (Paper Portfolio) — Phục vụ nghiên cứu lý thuyết"**.

---

## 3. Hướng Dẫn Sử Dụng Các Thành Phần Giao Diện Cốt Lõi (Core UI Components)

Hệ thống cung cấp 3 thành phần giao diện chuyên dụng để mang lại tính minh bạch tuyệt đối (Transparency) và bảo vệ quyền kiểm soát của người dùng (Human-In-The-Loop).

---

### 3.1. `<AgentRunPanel />` — Bảng Điều Khiển Tiến Trình Agent

Component này hiển thị trạng thái vòng đời thực thi của tác tử AI khi người dùng kích hoạt bất kỳ tác vụ nào.

```text
+-----------------------------------------------------------------------------+
| [Agentic Task]  ID: run_9a7b1c3e...                [ RUNNING ]   [ Cancel ] |
+-----------------------------------------------------------------------------+
|                                                                             |
|                           ↻ Agent is working...                             |
|                                                                             |
+-----------------------------------------------------------------------------+
| Generated Artifacts:                                                        |
| +-------------------------------------------------------------------------+ |
| | BCTC Result                                         earnings_memo v1.0  | |
| | [✓ 4 claims]   [📚 3 sources]   [⚠️ 1 limitations applied]              | |
| +-------------------------------------------------------------------------+ |
+-----------------------------------------------------------------------------+
```

#### Các Trạng Thái Vòng Đời (Lifecycle States)
* **`IDLE`:** Trạng thái sẵn sàng, chưa có tác vụ nào chạy.
* **`RUNNING` (Màu xanh dương/tím nhạt):** Tác tử đang gọi các công cụ dữ liệu ngầm, phân tích thông tin. Hiển thị hiệu ứng xoay (spinner ↻).
* **`REVIEWING`:** Hệ thống đang chạy bộ lọc kiểm định tính xác thực của số liệu (Numeric Reviewer) và an toàn nội dung.
* **`AWAITING_CONFIRMATION`:** Tác tử đã sinh ra một đề xuất hành động cần người dùng duyệt.
* **`COMPLETED` (Huy hiệu xanh lục):** Tác vụ hoàn thành chuẩn xác. Thẻ kết quả `AgentArtifactCard` xuất hiện bên dưới.
* **`DEGRADED` (Huy hiệu vàng cam):** Hoàn thành nhưng có một số nguồn phụ trợ bị thiếu hoặc quá thời hạn (Stale Data). Hệ thống vẫn cung cấp kết quả kèm cảnh báo giới hạn.
* **`FAILED` (Huy hiệu đỏ):** Tác vụ gặp lỗi hệ thống hoặc không vượt qua ngưỡng an toàn. Hiển thị thông điệp lỗi rõ ràng, dễ hiểu.
* **`CANCELED`:** Tác vụ đã được người dùng chủ động hủy bằng nút `[Cancel]`.

#### Thao Tác Của Người Dùng
* **Hủy tác vụ (`Cancel`):** Khi tác vụ đang ở trạng thái `RUNNING` hoặc `REVIEWING`, người dùng có thể bấm nút **`[Cancel]`** bất kỳ lúc nào để ngắt kết nối polling, tiết kiệm tài nguyên và trả giao diện về trạng thái ban đầu.

---

### 3.2. `<AgentArtifactCard />` & `<EvidenceDrawer />` — Thẻ Kết Quả & Ngăn Kéo Bằng Chứng

Toàn bộ kết quả đầu ra của AI không dừng lại ở câu chữ vô căn cứ mà được đóng gói thành các bằng chứng có thể kiểm chứng độc lập.

```text
                                              +--------------------------------------+
+------------------------------------------+  | Evidence & Citations             [✕] |
| BCTC Result           earnings_memo v1.0 |  +--------------------------------------+
|                                          |  | Domain: financials | Type: memo      |
| ✓ 4 claims    📚 3 sources               |  | Status: verified (v1.0)              |
| ⚠️ 1 limitations applied                 |  +--------------------------------------+
+------------------------------------------+  | Sources (3)                          |
                     |                        | • report: Q4_2025_AUDITED (bctc)     |
              (Click vào thẻ)                 | • ratio: gross_margin (engine)       |
                     |                        +--------------------------------------+
                     v                        | Verified Claims (4)                  |
          [MỞ EVIDENCE DRAWER] -------------> | 1. Biên LN gộp đạt 32.5% (+1.2% YoY) |
                                              | 2. Dòng tiền CFO âm 120 tỷ VND       |
                                              +--------------------------------------+
                                              | Limitations                          |
                                              | • Báo cáo chưa có kiểm toán độc lập  |
                                              +--------------------------------------+
```

#### Cấu Trúc Thẻ `<AgentArtifactCard />`
* Nằm gọn trong giao diện làm việc, hiển thị ngắn gọn:
  * Tên miền nghiên cứu (`domain`) và loại sản phẩm (`artifact_type`).
  * Phiên bản dữ liệu (`v1.0`).
  * Chỉ số đo lường độ tin cậy: Số lượng luận điểm đã xác thực (`claims`), số nguồn tài liệu đối chiếu (`sources`), và số lượng giới hạn áp dụng (`limitations`).

#### Trải Nghiệm Khám Phá Với `<EvidenceDrawer />`
* **Cách mở:** Bấm chuột trực tiếp vào thẻ `AgentArtifactCard`.
* **Hiệu ứng giao diện:** Một ngăn kéo bề ngang 420px trượt êm ái từ cạnh phải màn hình, không làm che khuất hoàn toàn bảng dữ liệu chính.
* **Nội dung hiển thị:**
  1. **Huy hiệu kiểm tra:** Thể hiện rõ trạng thái `verified` (đã đối chiếu thành công với cơ sở dữ liệu gốc) hoặc `draft` (bản nháp đang trong quá trình thử nghiệm).
  2. **Danh mục Nguồn trích dẫn (Sources):** Ghi rõ mã tài nguyên (`resource_id`), loại tài nguyên (`kind`), phân hệ cung cấp (`module`) và thời điểm lấy dữ liệu.
  3. **Danh sách Luận điểm kiểm chứng (Verified Claims):** Từng nhận định được gạch đầu dòng rõ ràng, kèm con số cụ thể và công thức tương ứng.
  4. **Giới hạn & Rủi ro (Limitations):** Nêu rõ các trường hợp ngoại lệ, dữ liệu thiếu hoặc khoảng trống phân tích mà học viên cần lưu tâm.
* **Cách đóng:** Bấm biểu tượng `✕` tại góc trên hoặc nhấn phím tắt **`Escape`** trên bàn phím.

---

### 3.3. `<ActionProposalReview />` — Thành Phần Xác Nhận Tác Vụ Ghi (Human-In-The-Loop)

Mọi hành động làm biến đổi dữ liệu hệ thống (lưu kết quả nghiên cứu, đánh dấu tiến độ bài học, khởi tạo phiên chạy mô phỏng tốn tài nguyên) **BẮT BUỘC** phải tạo ra một đề xuất (`ActionProposal`) và chờ người dùng bấm duyệt.

```text
+-----------------------------------------------------------------------------+
| Action Proposal: execute_simulation_run                 [ HIGH RISK ]       |
| Target: simulation_run (strat_momentum_v2)                                  |
+-----------------------------------------------------------------------------+
| Payload Preview:                                                            |
| {                                                                           |
|   "blueprint_id": "strat_momentum_v2",                                      |
|   "universe": ["VN30"],                                                     |
|   "date_range": ["2023-01-01", "2025-12-31"],                               |
|   "slippage_bps": 15,                                                       |
|   "initial_capital": 100000000                                              |
| }                                                                           |
+-----------------------------------------------------------------------------+
| Expires in: 4m 32s                                [ Reject ]  [ Confirm ]   |
+-----------------------------------------------------------------------------+
```

#### Các Yếu Tố Trực Quan Quan Trọng
1. **Phân loại mức độ rủi ro (Risk Class Badges):**
   * `LOW RISK` (Huy hiệu xanh): Lưu bài học vào danh mục cá nhân, lưu ghi chú nghiên cứu.
   * `MEDIUM RISK` (Huy hiệu vàng): Cập nhật checkpoint hoàn thành bài học, lưu tham số bộ lọc.
   * `HIGH RISK` (Huy hiệu đỏ): Kích hoạt chạy Backtest chuyên sâu dài hạn, xóa phiên làm việc cũ.
2. **Xem trước tải trọng thay đổi (Payload Preview):** Khối mã hiển thị chính xác đối tượng, trường dữ liệu và giá trị sắp được ghi vào cơ sở dữ liệu. **Nguyên tắc: Không có bất ngờ (Zero-Surprise).**
3. **Đồng hồ đếm ngược hết hạn (Expiration Timer):**
   * Mỗi đề xuất chỉ có hiệu lực trong một khung thời gian giới hạn (thông thường từ 5 đến 10 phút).
   * Khi hết thời gian, trạng thái chuyển thành **`Expired`**, nút `[Confirm Action]` lập tức bị vô hiệu hóa (disabled) để ngăn chặn việc thực thi các lệnh đã cũ hoặc không còn phù hợp bối cảnh.
4. **Quyền quyết định của người dùng:**
   * **Bấm `[Reject]`:** Bác bỏ đề xuất. Tác vụ bị hủy bỏ ngay lập tức, không để lại bất kỳ thay đổi nào trên hệ thống.
   * **Bấm `[Confirm Action]`:** Hệ thống gửi mã xác thực (`confirmation_token`) và khóa chống trùng lặp (`idempotency_key`) về Backend để thực thi tác vụ ghi một cách an toàn.

---

## 4. Các Nguyên Tắc An Toàn & Độ Tin Cậy (Trust & Safety)

Để đảm bảo Northstar Finance Lab luôn là môi trường học thuật mẫu mực, hệ thống vận hành dựa trên 4 trụ cột an toàn:

```text
                  +------------------------------------------------+
                  |         4 TRỤ CỘT TRUST & SAFETY TẠI           |
                  |             NORTHSTAR FINANCE LAB              |
                  +------------------------------------------------+
                                           |
    +------------------+-------------------+------------------+-------------------+
    |                  |                                      |                   |
    v                  v                                      v                   v
+--------------+  +----------------------+             +---------------+  +---------------+
| 1. MINH BẠCH |  | 2. CƠ CHẾ BẰNG CHỨNG |             | 3. PHÊ DUYỆT  |  | 4. BẢO VỆ     |
|   RANH GIỚI  |  |      XÁC ĐỊNH        |             |    CON NGƯỜI  |  |   DỮ LIỆU     |
+--------------+  +----------------------+             +---------------+  +---------------+
| • Chỉ nghiên |  | • Số liệu từ Engine  |             | • HITL bắt    |  | • Chống mã    |
|   cứu/học tập| • LLM không tự bịa   |             |   buộc cho ghi|   độc prompt  |
| • Không uỷ   | • Trích dẫn đầy đủ   |             | • Xem trước   | • Cách ly dữ  |
|   thác/broker|   nguồn & phiên bản  |             |   mọi thay đổi|   liệu ngoài  |
+--------------+  +----------------------+             +---------------+  +---------------+
```

### 4.1. Minh Bạch Ranh Giới (Boundary Transparency)
* Luôn hiển thị thông báo miễn trừ trách nhiệm giáo dục trên mọi màn hình nghiên cứu.
* Mọi phân tích chỉ số, định giá mô phỏng và kiểm định đều nhằm rèn luyện tư duy phản biện cho học viên, không cấu thành lời mời chào hay khuyến khích tham gia giao dịch tiền tệ thực tế.

### 4.2. Cơ Chế Bằng Chứng Xác Định (Deterministic Provenance)
* **Quy tắc Vàng:** Mô hình ngôn ngữ lớn (LLM) chỉ đóng vai trò diễn giải ngôn ngữ tự nhiên và tổ chức thông tin; **tuyệt đối không để LLM tự tính toán số học hoặc suy diễn số liệu tài chính**.
* Mọi phép tính toán (tỷ số thanh toán, biên lợi nhuận, độ lệch chuẩn, hệ số hồi quy) bắt buộc phải do các Engine định lượng xác định (`src/risk_dashboard/engines/quant/`) xử lý và ký xác thực phiên bản trước khi hiển thị cho người dùng.

### 4.3. Phê Duyệt Con Người (Human-In-The-Loop)
* Trí tuệ nhân tạo là người trợ tá, con người là người quyết định cuối cùng.
* Không có bất kỳ dòng dữ liệu cá nhân nào, phiên chạy mô phỏng nào hay bài kiểm tra nào được ghi nhận mà thiếu sự bấm duyệt chủ động của người dùng thông qua giao diện `ActionProposalReview`.

### 4.4. Phòng Vệ Tác Động Gián Tiếp (Indirect Prompt Injection Defense)
* Khi tiếp nhận văn bản từ báo chí bên ngoài, báo cáo thường niên hoặc thuyết minh tài chính, hệ thống coi toàn bộ dữ liệu đầu vào là **Nội dung chưa tin cậy (Untrusted Content)**.
* Dữ liệu này được bọc trong các thẻ cô lập (Data Isolation Blocks) để ngăn ngừa các cuộc tấn công ngôn ngữ cố tình điều hướng Agent phá vỡ các nguyên tắc an toàn.

---

## 5. Bảng Tra Cứu Luồng Nghiệp Vụ Tương Tác (User Journey Cheat Sheet)

Bảng hướng dẫn nhanh dành cho người dùng và kiểm thử viên khi thao tác trên hệ thống:

| Bạn muốn làm gì? | Vào màn hình (Surface) | Thao tác kích hoạt | Giao diện AI phản hồi | Cần lưu ý gì? |
| :--- | :--- | :--- | :--- | :--- |
| **Tìm bài học tiếp theo phù hợp** | `Home` | Bấm `[Làm mới đề xuất]` | `NextBestActionCardV1` hiển thị nhiệm vụ và lý do | Tự do chọn bắt đầu, hoãn hoặc đổi chủ đề |
| **Hiểu một công thức toán khó** | `Learn Hub` | Bôi đen công thức -> `[Giải thích cho tôi]` | `AgentRunPanel` -> `FormulaWalkthrough` giải thích biến số | Không có lời khuyên đầu tư; thuần túy toán học |
| **Nhận gợi ý khi bí bài trắc nghiệm** | `Learn Hub` | Bấm `[Cần gợi ý Socratic]` | Hộp thoại hội thoại đưa ra câu hỏi gợi mở | Agent không đưa đáp án; bạn cần tự chọn đáp án |
| **Xác thực chỉ số tài chính của công ty** | `BCTC Workspace` | Chọn dòng chỉ tiêu -> `[Bóc tách chỉ tiêu]` | `AgentArtifactCard` -> Mở `EvidenceDrawer` xem nguồn BCTC | Đối chiếu lại số liệu với BCTC đính kèm trong Drawer |
| **Kiểm tra thiên lệch chiến lược** | `Simulation Lab` | Cấu hình xong -> Bấm `[Preflight Validation]` | `PreflightChecklist` chỉ rõ nguy cơ Overfitting | Điều chỉnh tham số trước khi chạy để kết quả chuẩn |
| **Chạy kiểm thử mô phỏng chiến lược** | `Simulation Lab` | Bấm `[Chạy Backtest]` | `ActionProposalReview` đếm ngược chờ Confirm | Cần bấm **Confirm Action**; hoàn toàn là Paper test |
| **Bóc tách sự kiện từ nhiều bài báo** | `News Intelligence` | Chọn cụm tin -> `[Tạo tóm tắt đa nguồn]` | `NewsEvidenceBrief` tách biệt Fact và Claim | Điểm số do Engine tính; tin tức không phải lời khuyên mua |
| **Đo lường mức chịu sốc của danh mục** | `Market & Portfolio` | Chọn danh mục -> `[Rà soát rủi ro tập trung]` | `PortfolioReviewArtifact` mô phỏng sốc giá định lượng | Thuần túy là Sandbox thử nghiệm; không kết nối sàn |

---

## 6. Tổng Kết

Hệ thống **Northstar Finance Lab — Agentic Quantum** được thiết kế nhằm dung hòa giữa sức mạnh lý luận của Trí tuệ Nhân tạo hiện đại và sự chặt chẽ, chính xác tuyệt đối của Khoa học Tài chính Định lượng. Bằng việc phân định rạch ròi giữa hai chế độ tương tác, chuẩn hóa các thành phần UI kiểm chứng và đặt người dùng ở vị trí làm chủ mọi quyết định ghi dữ liệu, nền tảng mang lại một môi trường học tập và nghiên cứu an toàn, minh bạch và có tính ứng dụng học thuật cao.

