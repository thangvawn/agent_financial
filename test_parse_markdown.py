import json
import sys
from pathlib import Path

# Thêm src vào sys.path để import
sys.path.insert(0, "/Users/mac/Documents/Dự án Agent Tài chính/src")

from risk_dashboard.modules.financials_product.api.public import _dataset_from_markdown_artifact
from risk_dashboard.schemas.financials import FinancialDataset

upload_id = "bctc-fba91462c92205c2"
metadata = {"upload_id": upload_id, "ticker": "FPT", "period": "2024-Q1"}
extraction = {"status": "markdown_ready"}

dataset = _dataset_from_markdown_artifact(metadata, extraction)
print(dataset.model_dump_json(indent=2))
