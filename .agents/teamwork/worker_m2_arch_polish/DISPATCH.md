# Worker Polish: Final Polish of LEARN_HUB_ARCHITECTURE.md

**Working Directory**: /Users/mac/Documents/Dự án Agent Tài chính/.agents/teamwork/worker_m2_arch_polish  
**Target File**: `/Users/mac/Documents/Dự án Agent Tài chính/docs/LEARN_HUB_ARCHITECTURE.md`

## Required Edits
Apply the exact 4 fixes identified by `challenger_final`:
1. **Fix DDL Trigger (Lines 702-710)**:
   Replace trigger `trg_courses_v2_updated_at` with the column-scoped trigger:
   ```sql
   CREATE TRIGGER IF NOT EXISTS trg_courses_v2_updated_at
   AFTER UPDATE OF title, slug, description, instructor, tier, category, 
                   total_duration_minutes, thumbnail_url, prerequisites_json, 
                   target_competencies_json, is_active ON learning_courses_v2
   FOR EACH ROW
   BEGIN
       UPDATE learning_courses_v2 
       SET updated_at = CURRENT_TIMESTAMP 
       WHERE course_id = OLD.course_id;
   END;
   ```
2. **Fix Duplicate Foreign Key in Receipts**:
   In `learning_progress_receipts` DDL around line 639, remove the duplicate table-level `FOREIGN KEY (verified_event_id)` definition.
3. **Enhance FinancialCrossLinkService**:
   In `FinancialCrossLinkService.load_ticker_financial_snapshot`, when `data.get("company_name")` is `None`, enrich metadata using a fallback `VN30_COMPANY_REGISTRY` dictionary mapping ticker -> `{"company_name": ..., "industry": ..., "exchange": ...}` (e.g. HPG -> "Tập đoàn Hòa Phát", "Thép & Vật liệu xây dựng", "HOSE"; VNM -> "CTCP Sữa Việt Nam (Vinamilk)", "Thực phẩm & Đồ uống", "HOSE"; FPT -> "CTCP FPT", "Công nghệ thông tin", "HOSE").
4. **Harden Regex Layer 3**:
   Update `_CHOICE_PATTERN` to support whitespace inside brackets `\[\s*[A-D]\s*\]` and `\(\s*[A-D]\s*\)`.

5. **Run Empirical Verification**:
   Execute:
   ```bash
   .venv/bin/pytest tests/test_learn_hub_ddl_empirical.py \
                    tests/test_learn_hub_financial_crosslink_empirical.py \
                    tests/test_learn_hub_socratic_guardian_empirical.py -v
   ```
   Confirm all empirical tests pass.

MANDATORY INTEGRITY WARNING:
DO NOT CHEAT. All implementations must be genuine. DO NOT hardcode test results, create dummy/facade implementations, or circumvent the intended task. A teamwork_preview_auditor will independently verify your work. Integrity violations WILL be detected and your work WILL be rejected.

Write your report to `handoff.md` and send a completion message back to orchestrator via `send_message`.

## 2026-10-10T11:58:40Z
You are worker_m2_arch_polish. Your working directory is /Users/mac/Documents/Dự án Agent Tài chính/.agents/teamwork/worker_m2_arch_polish.
Please read:
- /Users/mac/Documents/Dự án Agent Tài chính/.agents/teamwork/ORIGINAL_REQUEST.md
- /Users/mac/Documents/Dự án Agent Tài chính/PROJECT.md
- /Users/mac/Documents/Dự án Agent Tài chính/.agents/teamwork/worker_m2_arch_polish/DISPATCH.md
- /Users/mac/Documents/Dự án Agent Tài chính/docs/LEARN_HUB_ARCHITECTURE.md

MANDATORY INTEGRITY WARNING:
DO NOT CHEAT. All implementations must be genuine. DO NOT hardcode test results, create dummy/facade implementations, or circumvent the intended task. A teamwork_preview_auditor will independently verify your work. Integrity violations WILL be detected and your work WILL be rejected.

Apply the 4 exact polish items to docs/LEARN_HUB_ARCHITECTURE.md:
1. Column-scoped trigger trg_courses_v2_updated_at (AFTER UPDATE OF title, slug, description, instructor, tier, category, total_duration_minutes, thumbnail_url, prerequisites_json, target_competencies_json, is_active ON learning_courses_v2).
2. Remove duplicate table-level FOREIGN KEY for verified_event_id in learning_progress_receipts.
3. FinancialCrossLinkService: add fallback VN30_COMPANY_REGISTRY profile lookup when company_name is None.
4. Regex Layer 3: update _CHOICE_PATTERN with whitespace flexibility: r"(?i)(?:\[\s*[A-D]\s*\]|\(\s*[A-D]\s*\)|(?:\b(?:đáp án|phương án|chọn|choice|answer|option)\s*(?:là|is|:)?\s*[\*\_]*([A-D])[\*\_]*\b))".
5. Run verification tests:
   .venv/bin/pytest tests/test_learn_hub_ddl_empirical.py tests/test_learn_hub_financial_crosslink_empirical.py tests/test_learn_hub_socratic_guardian_empirical.py -v
   Document pass/fail status in your handoff report.

Write your report to handoff.md and send a completion message back to orchestrator (conversation ID: 97a90bba-b298-4ab1-be4b-07eacc3cdf32).
