# Nghiên cứu bộ lọc cổ phiếu định lượng

- Date: 2026-11-01, Asia/Ho_Chi_Minh. Status: **proposed** cho logic; **verified** cho quan sát source/cache tại thời điểm kiểm tra.
- Request: nghiên cứu và đề xuất lại logic tín hiệu theo hướng định lượng. Chưa được yêu cầu triển khai engine hay thay quy tắc đang chạy.
- Deliverable: [đặc tả đề xuất](../../engineering/specs/quant-stock-screener.md) có quy ước dữ liệu, 12 preset, công thức/ranking, kiểm chứng ngoài mẫu, API/UI và thứ tự triển khai. Tham khảo nguồn gốc MSCI/AQR, hướng dẫn công thức Fidelity và nghiên cứu Deflated Sharpe của tác giả; ngưỡng riêng là giả thuyết, chưa được backtest tại Việt Nam.
- Evidence: [audit cache](../../../../output/qa/quant-screener-proposal/data-audit.json), đọc source stockFilters/GlobalTerminalPage/data-hub feed và API. Snapshot 1.521 mã thiếu các chỉ báo; daily cache31 mã, 7 mã≥200 phiên, 3 mã≥274 phiên, không có metadata điều chỉnh trong các khóa đã kiểm tra. File dài không mặc nhiên mới; audit không chứng nhận feed/provider.
- Proposal: EOD mặc định, kiểm tra chất lượng trước tính; scan trước phân trang; separate per-preset score và cảnh báo; giải thích điều kiện; không dùng score như xác suất. Các nhãn quá mạnh như “dòng tiền vào”, “đu đỉnh”, “VCP” thay bằng mô tả đo được/proxy có giới hạn.
- Validation: kiểm tra liên kết local và tính tay ví dụ breakout; chưa chạy backtest, không sửa source ứng dụng, không ghi DB sản xuất, không deploy. Staging fingerprint giữ nguyên `38f8fe1906f7dcd23ef9f97d84a7bab92051ebf08cc60ac7bc90a6bcd21d41ec`.
- Next: khi người dùng yêu cầu triển khai, bắt đầu từ dữ liệu chuẩn có provenance/adjustment, rồi sáu preset OHLCV cơ bản. Các đề xuất ở đây không tự trở thành task ready.
