# Vận hành bộ lọc định lượng

**Cập nhật lọc ngành 01/11/2026:** bảng giá hiện dùng `snapshot?industry=<ICB code>` và danh mục ICB Vietcap cấp3; không gọi screener EOD cho nhóm ngành. Cách nối cũ thiếu industry trong toàn bộ quote đã được thay thế. [Nguyên nhân, sửa và kiểm chứng dữ liệu thật](../../memory/sessions/2026-11-01-sector-filter-real-data.md). Các mô tả engine dưới đây vẫn áp dụng cho API tín hiệu riêng.

Ngày 01/11/2026. Trạng thái: **verified cho engine/API/UI với dữ liệu kiểm thử**, **chưa xác minh vận hành đầy đủ trên dữ liệu thị trường thật**. Công thức: `vn-eod-1.0.0`. Xem [đặc tả](quant-stock-screener.md).

**Cập nhật cùng ngày:** user đã yêu cầu bỏ hàng preset khỏi bảng giá. Phần UI chọn 12 tín hiệu/đếm/reset và sort điểm đã gỡ; engine/API/import bên dưới vẫn còn, sau yêu cầu tiếp theo, bộ chọn chỉ báo kỹ thuật cũng đã gỡ; nhóm ngành được gộp vào thanh sort và vẫn dùng API để lọc toàn universe. Xem [thanh sort/ngành mới](../../memory/sessions/2026-11-01-compact-market-toolbar.md). Các mô tả UI preset trong bản triển khai ban đầu dưới đây là lịch sử; xem [session thay đổi](../../memory/sessions/2026-11-01-remove-signal-filters.md).

## Hành vi đã áp dụng

- 12 bộ lọc và các chỉ báo kỹ thuật dùng kết quả do backend tính; frontend không còn suy đoán tín hiệu từ giá hiện tại/P/E/khối lượng của 50 dòng đang hiển thị.
- Duyệt toàn bộ universe có trong snapshot bảng giá, kiểm tra lịch sử/điều chỉnh/phiên chốt/thanh khoản rồi xếp hạng. Lọc sàn/ngành/điều kiện và phân trang xảy ra sau đó. “Toàn bộ” là phạm vi nhà cung cấp đã cung cấp, không chứng nhận bao phủ mọi mã niêm yết.
- Ngày chốt dùng lịch giao dịch có nguồn và mốc 16:00 Asia/Ho_Chi_Minh. Điểm xếp hạng 0–100 cần ít nhất 20 quan sát hợp lệ; không đủ thì để trống. Điểm không phải xác suất tăng giá.
- Giao diện hiển thị số mã đạt, đã đánh giá, thiếu dữ liệu, cũ hoặc không đủ điều kiện. Mỗi mã có ngày chốt, nguồn, giá trị quan sát và từng điều kiện. Hai bộ hồi phục/co hẹp có nhãn thử nghiệm.
- Con trỏ phân trang giữ nguyên snapshot và bộ điều kiện. Giá hiện tại được cập nhật độc lập; thứ tự sắp xếp giữ theo snapshot để không lặp/bỏ mã giữa các trang. Hủy yêu cầu cũ khi đổi bộ lọc. Tải lại định kỳ 60 giây khi tab hiển thị.
- Snapshot bất biến lưu theo ID; sửa công thức phải tăng version. `observed_on` là ngày đánh giá. `triggered_on` chỉ dùng cho giao cắt RSI hồi phục và mất MA20 đã kiểm tra phiên trước; chưa có tính năng xem lịch sử tín hiệu 5 phiên.

## Giới hạn dữ liệu hiện tại

Phiên kiểm tra ngày 01/11 xác nhận bản `vnstock 4.0.2` đang cài không có `Market.equity(...).trade_history`. Adapter cần schema có OHLC điều chỉnh, matched volume và **giá trị khớp thực tế**, theo [tài liệu Market](https://www.vnstocks.com/docs/vnstock/thi-truong-market). Một phép đọc public VNDIRECT trả 403; đây không phải nguồn thay thế khả dụng trong phiên này. Không nâng gói, mua dữ liệu hoặc thay thông tin đăng nhập tự động.

Adapter thu thập giá đã có, nhưng chưa kiểm chứng thành công với feed có quyền truy cập phù hợp. Bản adapter dùng price index cho benchmark, trong khi lịch sử cổ phiếu ghi `corporate_action_adjusted`; hai return basis chưa tương thích nên RS/momentum để trống. Chỉ nhập benchmark/cổ phiếu cùng quy ước lợi suất sau khi nguồn chứng minh được quy ước đó; không đổi nhãn metadata để vượt cổng kiểm tra.

Lịch khối ngoại, sự kiện cổ tức và BCTC point-in-time hiện đi qua bundle chuẩn hóa, chưa có adapter tự động. Ngành tài chính chưa có profile riêng, vì vậy các quy tắc chất lượng/cổ tức cần profile không đánh giá ngân hàng/chứng khoán/bảo hiểm. Lịch sử chart cũ thiếu metadata không được chuyển thành dữ liệu screener. Cache runtime được đọc tại lượt này có 1.521 mã đều unknown, session chưa xác minh và provider_unavailable. Khi chưa đủ dữ liệu, số mã đạt bằng 0 không đồng nghĩa thị trường không có mã thỏa điều kiện; xem số “thiếu dữ liệu” để phân biệt.

Chưa backtest ngoài mẫu, chưa chứng nhận lợi nhuận, phí/giao dịch thực tế hoặc tính tối ưu của các ngưỡng. Kiểm thử bằng dữ liệu tổng hợp chỉ chứng minh phép tính và hành vi phần mềm.

## Hợp đồng đầu vào

Cache mặc định `data/vn_screener/`, tách khỏi DB người dùng, không đưa vào Git. Có thể đổi bằng `VN_SCREENER_CACHE_DIR`. Lịch, input từng mã, checkpoint/queue và snapshot là JSON; ghi file atomically. Không có endpoint public để ghi/import.

Một bundle có cấu trúc dưới đây; ví dụ chỉ mô tả schema, không đủ lịch sử để kích hoạt tín hiệu:

```json
{
  "calendar": {
    "source": "provider/calendar-version",
    "valid_through": "2026-11-02",
    "sessions": ["2026-10-29", "2026-10-30", "2026-11-02"]
  },
  "inputs": {
    "AAA": {
      "security_type": "common_stock",
      "industry": "Tên nhóm ngành",
      "history": {
        "source": "provider/dataset-version",
        "price_unit": "VND",
        "price_basis": "corporate_action_adjusted",
        "adjustment_reference": "reference-to-verified-corporate-actions",
        "return_basis": "provider-defined-return-convention",
        "volume_basis": "split_adjusted",
        "bars": [{
          "date": "2026-10-30", "is_final": true,
          "open": 40000, "high": 42000, "low": 39500, "close": 41500,
          "volume": 1000000, "matched_turnover_vnd": 41000000000
        }]
      }
    }
  }
}
```

`sessions` tăng dần, không trùng, là phiên thực tế; có phạm vi lịch bao phủ toàn bộ lịch sử nhập và tới hiện tại/phiên tới để tính hạn cập nhật. Không suy diễn ngày lễ từ thứ trong tuần trong bundle. Lịch sử cổ phiếu cần liên tục theo lịch này; nến không final, lỗi hoặc thiếu trường không được nội suy. Đơn vị OHLC là VND, không phải nghìn VND. Giá trị khớp là VND thực tế, không được lấy close × volume. Benchmark nhập qua khóa VNINDEX/HNXINDEX/UPCOMINDEX với `index_price`, `index_points`, `volume_basis: index` và cùng return basis với cổ phiếu.

Các phần tùy chọn trong input từng mã:

| Phần | Trường bắt buộc và quy ước |
| --- | --- |
| `foreign` | `source`, `value_unit: VND`, `scope: matched`, `items` đủ 20 phiên; mỗi phiên có `date`, `is_final`, `available_at`, `buy_value`, `sell_value`, `matched_turnover_vnd`. Giá trị không âm; turnover >0. Không trộn thỏa thuận vào số khớp lệnh. |
| `fundamentals` | `source`, `complete: true`, `available_at`, `period_end`, `profile: non_financial`, `valuation_date` đúng ngày chốt. Các số TTM: `net_income_ttm`, `cfo_ttm`, `equity`, `eps_ttm`, `ebitda_ttm`, `net_debt`, `ebit_ttm`, `enterprise_value`, `raw_close`, `roe_ttm` dạng tỷ lệ. BCTC không quá 180 ngày tính từ period_end. |
| `fundamentals.annual` | Ba năm liên tiếp đã công bố, mỗi năm có source/complete/available_at/period_end, `cfo`, `cash_dividends_paid`, `eps`, `regular_dividend_dps`, `dividend_complete: true`. Năm mới nhất không quá 550 ngày. Payout cùng kỳ tài chính; cash coverage dùng tổng CFO/tổng tiền cổ tức ba năm. |
| `dividends` | `source`, `complete_through` đúng ngày chốt, `items` gồm `type: cash`, `regular: true`, `dps`, `announced_at`, `ex_date`, `paid_at`, `share_basis_date` đúng ngày chốt. DPS đã đưa về cùng cơ sở số cổ phần. Không tính cổ tức cổ phiếu hoặc đặc biệt. Yield dùng ex-date 365 ngày; tính đều dùng tiền đã trả ba năm lịch hoàn chỉnh. |

Mọi trường tiền tệ là VND, DPS/EPS là VND/cổ phần; không đưa tỷ lệ phần trăm nguyên vào trường fraction (ROE 20% là 0.20). `available_at`/`announced_at` phải phản ánh thời điểm công bố thật, ưu tiên ISO timestamp có timezone; dữ liệu sau 16:00 ngày chốt không được dùng. Import kiểm tra lịch sử của **mọi** record trước khi bắt đầu ghi. Mỗi input được thay thế toàn bộ, vì vậy cần gộp các phần đang có khi cập nhật bundle. Không coi bundle như chứng nhận nguồn: bên cung cấp vẫn phải chịu trách nhiệm provenance và corporate actions.

## Lệnh vận hành

Chạy từ repo. Ví dụ dùng cache tạm để xác minh bundle trước:

```sh
PYTHONPATH=src .venv/bin/python -m risk_dashboard.cli.stock_screener \
  --cache-dir /private/tmp/northstar-screener-review \
  --quotes data/vn_market/snapshot.json \
  --import-bundle /absolute/path/verified-bundle.json
```

`--build` tính lại từ input đã có. `--collect` chạy một batch adapter nếu môi trường có đúng capability và quyền dữ liệu. Khi xác minh xong có thể trỏ `--cache-dir` tới cache ứng dụng. Nếu chỉ dùng bundle, đặt `ENABLE_VN_SCREENER=0` để job không thay dữ liệu nhập. Job mặc định đi cùng scheduler VN Market; phải bật scheduler đó để thu thập tự động.

Collector dùng process lock, queue cố định theo phiên chốt, checkpoint sau từng mã, tối đa 30 mã/batch, khoảng nghỉ 4,1 giây. Khi lỗi nguồn: giữ input cũ, dừng batch, retry sau một giờ tại mã chưa thành công; lỗi kéo dài của một mã có thể chặn phần queue sau, cần kiểm tra nguồn/import. Mốc phiên đổi sau 16:00 nên lần chạy buổi sáng không ngăn lần chốt buổi chiều. Lịch quá hạn buộc thử cập nhật lại. Adapter mới không được suy đoán dữ liệu thiếu hoặc bỏ qua quyền truy cập.

API đọc: `GET /api/v1/public/data-hub/vn-market/screener`, query `preset`, `technical`, `sector`, `exchange`, `sort`, `limit` (1–100), `cursor`, `snapshot_id`. Kết quả có snapshot/version/ngày chốt, tổng và coverage, lý do thiếu dữ liệu, catalog công thức, items với conditions/metrics/score. Đổi điều kiện phải bỏ cursor cũ. `freshness: stale` giữ được snapshot cũ nhưng UI ghi rõ cần cập nhật.

## Kiểm chứng

Backend: dùng `scripts/qa/run_isolated_tests.py`; runner đặt DB, uploads, screener cache trong thư mục tạm và tắt job trước import. Frontend: unit/lint/CSS/build tạm; browser dùng API thật trên localhost, DB/cache riêng và 81 mã tổng hợp. Bằng chứng, giới hạn và số test ở [session triển khai](../../memory/sessions/2026-11-01-quant-screener-implementation.md).
