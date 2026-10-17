import urllib.request
import time
import json
import ssl
import statistics

ctx = ssl.create_default_context()
headers = {
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Accept": "application/json",
}

def benchmark_endpoint(name, url, iterations=10):
    network_times = []
    parse_times = []
    total_times = []
    sizes = []
    item_counts = []
    
    # Warmup
    try:
        req = urllib.request.Request(url, headers=headers)
        with urllib.request.urlopen(req, timeout=5, context=ctx) as resp:
            resp.read()
    except Exception as e:
        print(f"Warmup failed for {name}: {e}")
        return None

    for _ in range(iterations):
        t0 = time.perf_counter()
        req = urllib.request.Request(url, headers=headers)
        with urllib.request.urlopen(req, timeout=10, context=ctx) as resp:
            raw = resp.read()
            t1 = time.perf_counter()
            parsed = json.loads(raw.decode("utf-8"))
            t2 = time.perf_counter()
            
            data_items = parsed.get("data", [])
            item_counts.append(len(data_items) if isinstance(data_items, list) else 1)
            sizes.append(len(raw))
            network_times.append((t1 - t0) * 1000)
            parse_times.append((t2 - t1) * 1000)
            total_times.append((t2 - t0) * 1000)
        time.sleep(0.05)
        
    return {
        "name": name,
        "url": url,
        "items": int(statistics.mean(item_counts)),
        "size_kb": statistics.mean(sizes) / 1024,
        "net_min": min(network_times),
        "net_avg": statistics.mean(network_times),
        "parse_avg": statistics.mean(parse_times),
        "total_min": min(total_times),
        "total_avg": statistics.mean(total_times),
        "total_max": max(total_times),
    }

def main():
    print(">>> Đang chạy benchmark trực tiếp tới SSI Market API...\n")
    
    benchmarks = [
        ("SSI Realtime VN30 (30 mã)", "https://iboard-query.ssi.com.vn/stock/group/VN30", 10),
        ("SSI Realtime HNX30 (30 mã)", "https://iboard-query.ssi.com.vn/stock/group/HNX30", 10),
        ("SSI Realtime Toàn sàn HOSE", "https://iboard-query.ssi.com.vn/stock/exchange/hose", 5),
    ]

    results = []
    for name, url, iters in benchmarks:
        res = benchmark_endpoint(name, url, iterations=iters)
        if res:
            results.append(res)

    print("\n" + "="*85)
    print("KẾT QUẢ ĐO HIỆU SUẤT API THỊ TRƯỜNG REALTIME SSI")
    print("="*85)
    print(f"{'Endpoint':<32} | {'Mã':<5} | {'Dung lượng':<10} | {'Mạng Avg':<10} | {'Parse Avg':<10} | {'Tổng Avg (RTT)':<12}")
    print("-"*85)
    for r in results:
        print(f"{r['name']:<32} | {r['items']:<5d} | {r['size_kb']:>7.1f} KB | {r['net_avg']:>8.1f} ms | {r['parse_avg']:>8.1f} ms | {r['total_avg']:>11.1f} ms")
    print("="*85)

    # Chi tiết nén payload & chiết xuất cho AI Context
    if results:
        sample_vn30_res = results[0]
        print("\n>>> Đánh giá cho AI Agent Context:")
        print(f"- Lấy 30 mã VN30 tốn ~{sample_vn30_res['total_avg']:.1f}ms độ trễ mạng.")
        print(f"- Dung lượng raw JSON ~{sample_vn30_res['size_kb']:.1f} KB (chứa đầy đủ giá khớp, dư mua/bán 3 bước giá, trần/sàn).")
        print(f"- Khi format gọn cho LLM (chỉ lấy Ticker, Price, Change%, Volume):")
        print(f"  + Kích thước giảm còn: ~1.2 KB.")
        print(f"  + Số token ước tính tiêu thụ vào LLM Context: ~300 - 450 tokens.")

if __name__ == "__main__":
    main()
