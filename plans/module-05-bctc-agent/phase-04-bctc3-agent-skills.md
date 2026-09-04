---
phase: 4
title: "BCTC3 — Agent Skills (5 Manifests)"
status: completed
priority: P1
effort: "6h"
dependencies: [2]
---

# Phase 4: BCTC3 — Agent Skills & Prompt Templates

## Overview

Tạo 5 versioned skill manifests + prompt templates cho BCTC Agent. Skills xác định orchestration flow: guard → pin report/revision → classify intent → call read-only tools → numeric reviewer → teaching response hoặc reviewed memo.

## Requirements

### Functional

5 skills (§6 trong plan doc):

| Skill ID | Mục đích | Tools sử dụng |
|---|---|---|
| `bctc.explain_line_item.v1` | Giải thích một dòng mục BCTC | resolve_report, resolve_line_item |
| `bctc.compare_periods.v1` | So sánh kỳ kế toán | resolve_report, compare_periods |
| `bctc.ratio_walkthrough.v1` | Hướng dẫn tính ratio từng bước | resolve_report, calculate_ratio |
| `bctc.earnings_quality_review.v1` | Đánh giá chất lượng lợi nhuận | resolve_report, build_evidence_table, calculate_ratio |
| `bctc.research_checklist.v1` | Câu hỏi cần kiểm tra tiếp | resolve_report, trace_provenance |

- Mỗi skill có `SkillManifest` dataclass
- Prompt templates sử dụng surface context (company, period, statement, line_item)
- Orchestration: deterministic UI-intent routing (row click → explain, formula pick → ratio_walkthrough)
- Zero buy/sell phrasing trong adversarial prompt set
- **KHÔNG** import provider SDK trực tiếp — skills work through Agentic Core

### Non-functional

- Mọi numeric trong response trace về tool result
- Response luôn kèm: report_id, revision_id, period, currency, unit, source, fetched_at

## Related Code Files

### Create

- `src/risk_dashboard/modules/financials_product/skills/__init__.py`
- `src/risk_dashboard/modules/financials_product/skills/manifests.py`
- `src/risk_dashboard/modules/financials_product/skills/prompts/__init__.py`
- `src/risk_dashboard/modules/financials_product/skills/prompts/explain_line_item.py`
- `src/risk_dashboard/modules/financials_product/skills/prompts/compare_periods.py`
- `src/risk_dashboard/modules/financials_product/skills/prompts/ratio_walkthrough.py`
- `src/risk_dashboard/modules/financials_product/skills/prompts/earnings_quality_review.py`
- `src/risk_dashboard/modules/financials_product/skills/prompts/research_checklist.py`
- `tests/test_bctc_agent_skills.py`

### Pattern reference

- `src/risk_dashboard/modules/learning/skills/manifests.py` — exact pattern to follow
- `src/risk_dashboard/modules/learning/skills/prompts/` — prompt template pattern

## Implementation Steps

### Step 1: Create `skills/manifests.py`

```python
@dataclass(frozen=True)
class SkillManifest:
    skill_id: str
    version: str
    description: str
    required_tools: tuple[str, ...]
    required_scopes: tuple[str, ...]
    risk_class: str = "read"
    zero_leakage_enforced: bool = False
    max_tool_calls: int = 3
    timeout_ms: int = 5000
```

5 manifests instantiated + `get_skill_manifest(skill_id)` lookup function.

### Step 2: Create prompt templates

Each prompt template follows structure:

```python
# explain_line_item.py
EXPLAIN_LINE_ITEM_PROMPT = """
## Nhiệm vụ
Giải thích dòng mục "{line_item}" trong báo cáo {statement} của {company} kỳ {period}.

## Quy tắc bắt buộc
1. Mọi con số PHẢI đến từ tool `bctc.resolve_line_item`
2. Phải kèm: report_id, revision_id, period, currency, unit, source
3. KHÔNG đưa khuyến nghị mua/bán
4. KHÔNG tự tạo số liệu
5. Giải thích bằng tiếng Việt, thuật ngữ giữ nguyên tiếng Anh khi cần

## Cấu trúc trả lời
1. **Định nghĩa**: Dòng mục này là gì
2. **Giá trị**: Con số + đơn vị + kỳ + nguồn
3. **Thành phần**: Gồm những gì (composition)
4. **Lưu ý**: Caveats và limitations
5. **Câu hỏi kiểm tra**: Một câu hỏi để learner tự kiểm tra hiểu biết

## Giới hạn
{limitations}
"""
```

### Step 3: Create tests

- `test_skill_manifests_count` — 5 manifests
- `test_get_skill_manifest_by_id` — lookup works
- `test_skill_required_tools_valid` — all tool_ids exist in tool manifests
- `test_prompt_templates_have_placeholders` — verify format strings
- `test_no_buy_sell_language_in_prompts` — regex scan for buy/sell/mua/bán/khuyến nghị

## Success Criteria

- [ ] 5 skill manifests registered
- [ ] All prompt templates use tool-required citations
- [ ] Zero buy/sell phrasing in prompt templates
- [ ] `get_skill_manifest(skill_id)` returns correct manifest
- [ ] ≥5 tests pass
