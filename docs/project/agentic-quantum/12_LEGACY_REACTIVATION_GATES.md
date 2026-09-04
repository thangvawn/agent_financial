# 12 — Legacy Modules: Reactivation Gates

> Modules: `goals`, `financial_health`, `community`, `guided_investing`
> Current status: archived/hold
> Policy: không đưa vào Agentic Quantum rollout hiện tại

## 1. Mục đích

Tài liệu này ngăn việc “agent hóa” các module archived chỉ vì code vẫn còn trong repository. Mỗi module chỉ được tái kích hoạt khi product, regulatory, data, security và maintenance case đã được chứng minh. Trước gate đó, Agentic Core không register skill/tool của các module này.

## 2. Gate chung

Mọi module legacy phải đạt tất cả điều kiện:

1. Product owner và target user/outcome rõ ràng.
2. Module source of truth, API, data ownership và maintainer được xác nhận.
3. Archived reason đã được giải quyết và ghi bằng ADR.
4. Auth/account migration and retention complete.
5. Regulatory/advisory boundary reviewed.
6. Deterministic service/tool baseline passes tests.
7. Gold set, threat model, feature flag, rollout and rollback exist.
8. Không làm suy giảm roadmap P0/P1 hiện tại.

## 3. Goals

Potential capability: goal-based learning journey, không tự động đưa investment plan.

Required gates:

- goal taxonomy and explicit user consent;
- goal correction/delete/export;
- no inference of sensitive wealth/income from conversation;
- deterministic eligibility and next-step plan;
- separation between education goal and regulated advice;
- integration with Home only through compact summary.

Suggested work packages if approved: `GOAL0` product revalidation → `GOAL1` data/auth migration → `GOAL2` deterministic planning → `GOAL3` agent explanation → `GOAL4` eval/pilot.

## 4. Financial Health

Potential capability: educational explanation of user-entered health metrics.

Required gates:

- explicit financial data collection purpose and retention;
- encryption/access controls and field-level redaction;
- validated formulas and locale assumptions;
- high-stakes disclaimer/escalation policy;
- no inferred sensitive health/financial profile memory;
- independent security/privacy review.

Suggested packages: `FH0` policy/data review → `FH1` deterministic calculator validation → `FH2` read-only explanation → `FH3` safety eval → `FH4` limited pilot.

## 5. Community

Potential capability: moderated learning discussion summarization and concept routing.

Required gates:

- moderation/abuse/spam policy and appeals;
- consent and attribution for user-generated content;
- stored prompt injection isolation;
- copyright/privacy/takedown workflow;
- no agent impersonation or autonomous posting;
- human moderation capacity and abuse metrics.

Suggested packages: `COM0` community policy → `COM1` moderation baseline → `COM2` read-only summary/retrieval → `COM3` adversarial eval → `COM4` cohort pilot.

## 6. Guided Investing

This is the highest-risk legacy domain. Potential agent capability is limited to education and scenario explanation unless legal/compliance approves more.

Required gates:

- jurisdiction and regulatory classification;
- suitability/advisory boundary and disclosures;
- instrument/data licensing;
- conflict-of-interest and ranking policy;
- full audit, explanation and human escalation;
- no transaction execution in current Agentic Quantum architecture;
- external legal/compliance approval before product experiment.

Suggested packages: `GI0` legal/product decision → `GI1` education-only deterministic content → `GI2` evidence tools → `GI3` advice-boundary eval → `GI4` explicitly approved pilot.

## 7. Forbidden shortcuts

- Không bỏ `ARCHIVE.md` rồi register module mà thiếu ADR.
- Không dùng generic chatbot prompt thay cho validated domain service.
- Không reuse memory từ Learn/BCTC làm suitability profile.
- Không bật mutation/action chỉ vì Agentic Core hỗ trợ confirmation.
- Không gọi feature “personalized investing” dựa trên inferred preferences.
- Không dùng community content như trusted instructions/knowledge nếu chưa moderation.

## 8. Reactivation decision record

Mỗi proposal phải ghi:

| Field | Required content |
|---|---|
| Outcome | user problem and measurable benefit |
| Owner | product, engineering, domain and compliance owners |
| Source of truth | authoritative data/service |
| Risk class | privacy, financial, content and operational risks |
| Allowed actions | read/proposal/confirmed write/forbidden |
| Dependencies | identity, runtime, tools, reviewers, data licenses |
| Eval | quality, safety, security and economics thresholds |
| Rollout | feature flag, cohorts and rollback |
| ADR | why archived cause is resolved |

## 9. Definition of Ready for any reactivation

- Gate checklist approved and evidence linked.
- Module has maintained deterministic baseline and tests.
- Identity/ownership and data deletion tested.
- Agent-vs-AI-assist classification completed.
- Non-goals and forbidden actions are explicit.
- Dedicated module plan is created; this gate document is not itself an implementation authorization.

## 10. Validation checkpoint

Yêu cầu bổ sung (tài liệu này không có work-package table nên requirement được ghi trực tiếp ở đây):

- **Baseline test suite** — mỗi legacy module phải có regression tests capture current legacy behavior TRƯỚC mọi reactivation. Không có baseline suite → không mở gate.

- Entry criteria: baseline test suite tồn tại và capture current legacy behavior; reactivation gate criteria đã định nghĩa (§2 gate chung + module-specific gates §3–§6).
- Exit criteria (quantitative):
  - 100% legacy behavior được cover bởi baseline tests trước reactivation;
  - zero reactivation không qua passing gate;
  - mọi reactivated module re-enter qua AT-phase entry criteria.
- Validation gate: Hold tier (master §14A.1) — chỉ mở qua explicit reactivation gate.

## 11. Open decisions

- Legacy module nào là reactivation candidate (`goals`, `financial_health`, `community`, `guided_investing` — thứ tự ưu tiên)?
- Ai là baseline test owner cho mỗi module?
- Ai là gate approver (product, engineering, compliance)?

