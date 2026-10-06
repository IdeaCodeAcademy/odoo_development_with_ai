# Project Roadmap

Every completed feature includes security, automated tests, passing validation,
documentation, STATE.md and an Odoo-style commit. Security is implemented in
each phase; Phase 10 reviews it across the complete workflow.

| Phase | Scope and acceptance gate |
| --- | --- |
| 0 - Environment | Compose build/start, PostgreSQL readiness, Odoo HTTP and isolated test runner verified |
| 1 - Hair Base | Configurable types, textures, colors, grades and lengths; company rules; archive and bound validation tests |
| 2 - Supplier Management | res.partner seller extensions, sensitive-field policy and permission tests; seller access policy required |
| 3 - Purchase Intake | Header/lines, sequence, weights and deductions; invalid weight/transition tests |
| 4 - Pricing Engine | Effective rules, non-overlap, historical snapshot, override audit/permissions; actual pricing context required |
| 5 - Quality / Grading | Inspection evidence, required criteria, rejection and grade approval; inspection policy required |
| 6 - Inventory + Lot Tracking | Standard stock receipt/lots, source links and idempotency; receipt/payment policy required |
| 7 - Payment Integration | Partial/full tracking and optional accounting bridge; journals and reversal policy required |
| 8 - Processing / Yield | Standard manufacturing, input/output lots, loss/yield tests |
| 9 - Dashboard | ORM KPIs, period filters, company isolation and performance verification |
| 10 - Security / Audit | Cross-role, cross-company, protected corrections and concurrency review |
| 11 - UAT / Stabilization | Business-approved scenarios, fixes, migration/backup instructions and release checks |

Core workflow: Seller → Hair Intake → Weight → Quality/Grade → Pricing
→ Confirmation → Payment → Inventory Lot.

Implementation order follows dependencies; no phase is declared complete while
its tests fail. Outstanding business decisions are tracked in STATE.md.

## Current feature progress

- Phase 0 and Phase 1 are complete.
- Phase 2 seller foundation and intake history are complete; confirmed purchase/value statistics remain.
- Phase 3 draft intake and kg weight feature is complete; inspection submission
  depends on the quality workflow.
- Phase 4 pricing configuration, selection and private quote calculation are
  implemented; applying quotes, confirmation snapshots and override audit remain.
- Later phases remain pending. See STATE.md for validated results and required
  business configuration; these feature milestones do not imply full release.
