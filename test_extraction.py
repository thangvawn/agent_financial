from risk_dashboard.modules.financials_product.api.public import _extract_uploaded_statement
import json
from pathlib import Path

# Load metadata
meta_path = Path("data/financial_uploads/bctc-fba91462c92205c2.json")
metadata = json.loads(meta_path.read_text())

# Re-extract
result = _extract_uploaded_statement(metadata)

# Save result
Path("test_result.json").write_text(json.dumps(result, indent=2))
print("Extraction complete.")
