import json
from risk_dashboard.modules.financials_product.api.public import _load_upload_metadata, _dataset_from_markdown_artifact

metadata = _load_upload_metadata('bctc-fba91462c92205c2')
extraction = json.load(open('data/financial_uploads/bctc-fba91462c92205c2.json')).get('extraction', {})

# Wait, extraction isn't saved in the JSON in my curl!
# My curl updated the JSON. Let's load the JSON and use it.
data = json.load(open('data/financial_uploads/bctc-fba91462c92205c2.json'))
dataset = _dataset_from_markdown_artifact(metadata, data.get('extraction', {}))

print(json.dumps(dataset, indent=2))
