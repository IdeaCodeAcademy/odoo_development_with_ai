# Project State

## Initialization and Phase 0 - Complete

- Requirements, architecture, roadmap and agent instructions are under docs/.
- Official Odoo 19 Git/coding guidelines read through the GitHub connector from
  odoo/documentation branch 19.0; earlier website timeout blocker is resolved.
- ECC Python patterns and security-review guidance applied.
- Odoo 20.0 Community build 20.0-20260926 and PostgreSQL 16 run through Compose.
- Environment checks pass: Compose validation, PostgreSQL readiness and HTTP.
- `hair_demo` created with standard Odoo demo data; login is admin, password is
  stored in local Git-ignored `.demo_credentials` with file mode 0600.
- User confirmed MMK; hair_demo company currency set to MMK and verified.
- Demo URL: http://localhost:8071/web/login?db=hair_demo.

## ICA Web Responsive - Complete

- Odoo 20 source copied from the local IdeaCodeAcademy/odoo_app_store checkout;
  source commit and license recorded in THIRD_PARTY.md.
- Installed in hair_demo. Login and responsive home menu verified in browser.
- Removed internal-user sudo from partner location updates.
- Five automated tests cover location access/company isolation and theme ownership.

## Phase 1 - Hair Base - Complete

- hair_base provides type, texture, color, grade and length configuration,
  list/form/search views, menus, ordering and archive behavior.
- Company-specific permissions use the installed Odoo 20 unified ir.access API.
- Readers cannot mutate; configuration admins create/update/archive, not delete.
- Public/unrelated internal users are denied; company reads/creates/writes and
  attempted unauthorized company-context changes are tested.
- Company reassignment is checked before write; Odoo 20 constraints run in sudo.
- Length validation rejects negative, infinite and reversed bounds.
- Eight automated tests cover configuration, bounds, access controls and views.
- Installed in hair_demo with illustrative master data; Hair Types/Virgin Hair
  verified in browser, and authenticated demo checks pass.

## Phase 2 - Seller Management - Complete foundation

- Buyer creates/edits/archives sellers; Manager/Admin accesses optional NRC.
- res.partner extension, configurable seller types and menus installed in hair_demo.
- NRC protection verified for views, ORM reads/writes/search and imports.
- Company isolation and unrelated contact permissions tested.
- Seller intake history is implemented by hair_purchase; confirmed purchase/value
  statistics still depend on the commercial workflow.

## Phase 3 - Draft Intake and Weight Feature - Complete

- hair_purchase provides draft headers, unique sequences and multiple hair lines.
- User confirmed kg at 0.001 kg (1 g) scale resolution; three decimal places.
- Gross less tare/waste/moisture/other deductions computes payable kg and totals.
- Server validation rejects negative/nonfinite weights and excessive deductions.
- Company isolation, relation integrity and forged calculated values are tested.
- Seven intake tests cover calculations, validation, permissions and view loading.
- Inspection submission and commercial confirmation are implemented; payment/stock effects remain pending.

## Phase 4 - Pricing Configuration/Selection Feature - Complete

- Company-currency price per kg rules by type, grade, length and effective dates.
- Active overlap rejected, including bounds changed on shared length definitions.
- Exact/range/open lengths and inclusive date boundaries supported.
- Exactly one matching rule is required; archived/missing/ambiguous rules rejected.
- Private quote API computes currency-rounded payable kg × rate.
- Configuration admins mutate; hair users read; companies remain isolated.
- Eight pricing tests pass. No real rates seeded in hair_demo.
- Confirmation now applies quotes and preserves historical snapshots. Price
  override audit remains pending; the entire Pricing Engine phase is not declared complete.

## Seller Intake History Feature - Complete

- Seller form shows Intakes button, intake count, total payable kg and last date.
- Draft intakes are explicitly labeled; no claim of confirmed purchases/payments.
- Grouped ORM aggregation uses caller permissions without sudo.
- Buyer/Manager/Admin field/action access enforced; foreign sellers denied.
- Four tests cover updates, reassignment, action defaults and security.

## Quality Inspection/Grade Approval Feature - Complete

- Buyer submits type/length/positive payable kg lines for inspection.
- Separate Quality Officer grades every line and approves or rejects with a reason.
- Approval records inspector/time; retries retain provenance.
- Submitted inputs and approved findings are immutable; return to draft resets
  approval. Reopening approval requires a reason and logs previous grades.
- Copy produces a fresh draft without approval or inspection provenance.
- Company access, direct/context forgery, role/NRC separation and views tested.
- Uses ORM row locks and standard chatter/attachments; no sudo or raw SQL.
- Extended criterion configuration remains pending; no quality thresholds invented.

## Commercial Confirmation/Cancellation Feature - Complete

- Manager/Admin confirms only quality-approved, complete positive-kg intakes.
- Exactly one applicable pricing rule required per line; missing prices fail atomically.
- Explicit Compute Price records reviewable quotes and actor/time. Confirmation
  rejects stale pricing/classification/currency until repriced and reviewed.
- Rate/amount/rule, currency, seller/type/grade/length labels and bounds snapshot.
- Confirmed values survive rule/name/length/company-currency configuration changes.
- Direct snapshots/input forgery denied; copy creates a new unapproved draft.
- Reasoned Manager cancellation retains actor/time and historical monetary values.
- Repeated confirm/cancel calls retain original provenance; ORM parent row locking.
- Nine tests pass, including quote freshness/reset; no actual payments/accounting/stock operations created.
- Price override audit/UI remains a subsequent feature.

## Latest validation

- `ruff check .`: all checks passed, using the Odoo runbot rule configuration.
- scripts/test_addons.py: exit 0, 0 failed, 0 errors, 58 executed tests
  (56 custom and 2 automatically selected web cases).
- Isolated test database: hair_test_0e4ef99bbefc.
- hair_purchase installed/updated in hair_demo; Hair Intakes list browser-verified.
- Environment and authenticated demo checks passed after quality/confirmation update.
- Demo history fields and seller-filtered action verified through authenticated RPC.

## Delegated workflow policy

User authorized suitable commercial/quality policy. Manager/Admin will confirm,
override prices (with a reason) and cancel. Quality Officer will approve final
grades. Confirmation requires seller, positive payable kg, hair type, length,
approved grade and a valid pricing rule. Implement these server-enforced actions
in later workflow features; this authorization resolves the role-policy blocker.

## Pending business pricing data

MMK and 0.001 kg resolution are confirmed. Real prices per kg by type/grade/length
and effective dates remain missing. No real/sample rate rules are activated in
hair_demo. Synthetic rates exercise development tests without guessing business
prices; this data gap does not prevent independent workflow implementation.

## Exact blocker and required input for inventory integration

Receipt/payment policy is not defined: may stock be received for confirmed
unpaid/partially paid purchases, or only after full payment? A question presenting
these two policies has been sent. This decision changes receipt state guards and
is required before implementing stock receipt behavior.

Required input: choose fully-paid-only receipt or confirmed unpaid/partial receipt.
Remaining work: price override audit/UI, extended quality criteria, inventory/lot
receipt after this policy, payment/accounting, confirmed seller statistics and
later roadmap phases. No guessed receipt/reversal policy has been activated.
