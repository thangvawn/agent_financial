import json

data = json.load(open('data/financial_uploads/bctc-fba91462c92205c2.json'))

for page in data.get('ocr', {}).get('pages', []):
    for row in page.get('statement_rows', []):
        if 'TẢI SẢN' in row.get('raw_text', '') or 'NGAN HAN' in row.get('raw_text', '') or 'NGẮN HẠN' in row.get('raw_text', '') or 'TONG' in row.get('raw_text', ''):
            print(f"Page {page['page']}: {row['raw_text']}")
            print(f"  -> current: {row.get('current_value')}, previous: {row.get('previous_value')}")

