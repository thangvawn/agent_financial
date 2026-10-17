# Handoff Report — Final Empirical Challenger (Gate Iteration 2)

**Sender**: `challenger_final`  
**Recipient**: Orchestrator (`97a90bba-b298-4ab1-be4b-07eacc3cdf32`)  
**Workspace**: `/Users/mac/Documents/Dự án Agent Tài chính/.agents/teamwork/challenger_final`  
**Status**: Task Complete (Hard Handoff)  
**Final Verdict**: **REQUEST_CHANGES**  

---

## 1. Observation

1. **DDL Trigger Infinite Recursion (BUG-01)**:
   - File & Lines: `docs/LEARN_HUB_ARCHITECTURE.md:702-710`
   - SQL Code:
     ```sql
     CREATE TRIGGER IF NOT EXISTS trg_courses_v2_updated_at
     AFTER UPDATE ON learning_courses_v2
     FOR EACH ROW
     WHEN OLD.updated_at = NEW.updated_at
     BEGIN
         UPDATE learning_courses_v2 
         SET updated_at = CURRENT_TIMESTAMP 
         WHERE course_id = OLD.course_id;
     END;
     ```
   - Execution Command:
     ```bash
     .venv/bin/pytest tests/test_learn_hub_ddl_empirical.py::test_courses_trigger_doc_ddl_reproduces_recursion_bug -v
     ```
   - Verbatim Output:
     ```text
     FAILED tests/test_learn_hub_ddl_empirical.py::test_courses_trigger_doc_ddl_reproduces_recursion_bug
     E sqlite3.OperationalError: too many levels of trigger recursion
     ```

2. **Duplicate Foreign Key Definition (BUG-03)**:
   - File & Lines: `docs/LEARN_HUB_ARCHITECTURE.md:630-642`
   - Lines 632 and 639 both declare:
     `FOREIGN KEY (verified_event_id) REFERENCES learning_verified_events(event_id) ON DELETE SET NULL`
   - Verbatim Output from `PRAGMA foreign_key_list(learning_progress_receipts)`:
     Two duplicate FK rows targeting `learning_verified_events(event_id)` on column `verified_event_id`.

3. **Financial Cache JSON Metadata Discrepancy (BUG-02)**:
   - File & Lines: `docs/LEARN_HUB_ARCHITECTURE.md:1491-1493`
   - Implementation:
     ```python
     "company_name": data.get("company_name"),
     "industry": data.get("industry"),
     "exchange": data.get("exchange"),
     ```
   - Execution against actual files `data/financials/cache/HPG.json`, `VNM.json`, `FPT.json`:
     `data.get("company_name") == None`, `data.get("industry") == None`, `data.get("exchange") == None`.
   - Verbatim Test Output:
     `assert snapshot["company_name"] is not None` fails with `assert None is not None`.

4. **Socratic Guardrail Edge Case Sensitivity (BUG-04)**:
   - File & Lines: `docs/LEARN_HUB_ARCHITECTURE.md:1696-1733`
   - Regex `_CHOICE_PATTERN` strictly matches `\[[A-D]\]` and `\([A-D]\)`.
   - Test input `'Phương án chính xác là [ A ]'` and `'The choice is a'` bypassed Layer 3 regex, while standard inputs `'Đáp án chính xác là A'` and `'The correct answer is B'` were 100% intercepted and converted to 3-level scaffolding.

5. **Completeness of 13 Features in `PROJECT.md`**:
   - Every single feature (Features 1 through 13) is verified to have exhaustive specifications across `docs/LEARN_HUB_AUDIT_REPORT.md` (M1), `docs/LEARN_HUB_ARCHITECTURE.md` (M2), and `docs/LEARN_HUB_BLUEPRINT.md` (M3).

---

## 2. Logic Chain

1. **Trigger Recursion (BUG-01)**:
   - In SQLite, `CURRENT_TIMESTAMP` returns a static string representing the current time with second resolution (`YYYY-MM-DD HH:MM:SS`) that remains constant for the entire duration of an executing statement and its triggered statements.
   - When an `UPDATE` executes in the same second as the row creation or update, the trigger sets `updated_at = CURRENT_TIMESTAMP`. Since `CURRENT_TIMESTAMP` does not change, `NEW.updated_at` equals `OLD.updated_at`.
   - Therefore, the trigger's `WHEN OLD.updated_at = NEW.updated_at` condition evaluates to `TRUE` again inside the trigger update, firing itself indefinitely until reaching SQLite's recursion limit.
   - Conclusion: The trigger MUST be column-scoped (`AFTER UPDATE OF title, slug, ... ON learning_courses_v2`) to prevent recursive execution on `updated_at`.

2. **Financial Cache Extraction (BUG-02)**:
   - The production cache files in `data/financials/cache/` were created by the raw financial gateway crawler which only populated `periods` and `raw_statements`, leaving `company_name`, `industry`, and `exchange` as `null`.
   - When `FinancialCrossLinkService` reads these fields directly, it outputs `None`, which causes missing metadata in frontend header cards, ticker badges, and AI Tutor context cards.
   - Conclusion: `FinancialCrossLinkService` must implement fallback enrichment from `src/data/vn_market/profiles/{ticker}.json` or a standard dictionary registry (`VN30_COMPANY_REGISTRY`).

3. **Socratic Guardrail Defense-in-Depth (BUG-04)**:
   - While Layer 1 (Context Isolation) prevents the LLM from possessing `correct_answer`, Layer 3 regex should be resilient against whitespace formatting tricks (`[ A ]`).
   - Conclusion: Extend regex `_CHOICE_PATTERN` to `\[\s*[A-D]\s*\]` and `\(\s*[A-D]\s*\)`.

---

## 3. Caveats

- **Scope limitation**: Review-only mandate. No production application files were altered directly. All tests and reproductions were executed via dedicated empirical test files in `tests/test_learn_hub_*.py`.
- **Pre-existing Database State**: `data/db/northstar.db` currently on disk has a malformed disk image from an interrupted prior process; however, all module tests pass 100% when run with fresh/in-memory SQLite connections.

---

## 4. Conclusion

**Final Verdict**: **REQUEST_CHANGES**

The Learn Hub Architecture and Blueprint are structurally robust and cover 100% of the 13 required features. However, before finalizing the architectural milestone, the authoring team must apply the following specific corrections to `docs/LEARN_HUB_ARCHITECTURE.md`:

1. **Patch DDL Trigger (Lines 702-710)**:
   Replace trigger `trg_courses_v2_updated_at` with:
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

2. **Patch FinancialCrossLinkService (Lines 1491-1493)**:
   Add fallback dictionary / profile enrichment for `company_name`, `industry`, and `exchange` when `data.get("company_name")` is `None`.

3. **Remove Duplicate FK**:
   Delete redundant table-level constraint at line 639 of `docs/LEARN_HUB_ARCHITECTURE.md`.

4. **Harden Regex Lớp 3**:
   Update `_CHOICE_PATTERN` to accept whitespace inside brackets/parentheses.

---

## 5. Verification Method

To independently reproduce all findings and verify the remediations, run:

```bash
# 1. Run all 17 empirical challenge tests (DDL, Financial Cache, Socratic Guardian)
.venv/bin/pytest tests/test_learn_hub_ddl_empirical.py \
                 tests/test_learn_hub_financial_crosslink_empirical.py \
                 tests/test_learn_hub_socratic_guardian_empirical.py -v

# 2. Verify DDL trigger recursion reproduction directly:
.venv/bin/pytest tests/test_learn_hub_ddl_empirical.py::test_courses_trigger_doc_ddl_reproduces_recursion_bug -v

# 3. Verify DDL trigger fix:
.venv/bin/pytest tests/test_learn_hub_ddl_empirical.py::test_courses_trigger_remediated_resolves_recursion -v

# 4. Verify raw cache null metadata vs enriched service:
.venv/bin/pytest tests/test_learn_hub_financial_crosslink_empirical.py -v
```
