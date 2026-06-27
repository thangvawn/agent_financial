from pathlib import Path

path = Path("data/financial_uploads/bctc-fba91462c92205c2/document.md")
rows = []
in_table = False
for line in path.read_text(encoding="utf-8").splitlines():
    stripped = line.strip()
    if stripped == "| page | code | metric | label | current_value | previous_value | confidence |":
        in_table = True
        continue
    if in_table and stripped.startswith("| ---"):
        continue
    if in_table and not stripped.startswith("|"):
        break
    if not in_table or not stripped.startswith("|"):
        continue
    cells = [cell.strip().replace("\\|", "|") for cell in stripped.strip("|").split("|")]
    if len(cells) < 7:
        continue
    rows.append(cells)
print(f"Parsed {len(rows)} rows")
