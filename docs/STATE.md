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
- Seller intake history and confirmed purchase statistics are implemented by hair_purchase.

## Phase 3 - Draft Intake and Weight Feature - Complete

- hair_purchase provides draft headers, unique sequences and multiple hair lines.
- User confirmed kg at 0.001 kg (1 g) scale resolution; three decimal places.
- Gross less tare/waste/moisture/other deductions computes payable kg and totals.
- Server validation rejects negative/nonfinite weights and excessive deductions.
- Company isolation, relation integrity and forged calculated values are tested.
- Seven intake tests cover calculations, validation, permissions and view loading.
- Inspection, confirmation and manual payment tracking are implemented; stock/accounting effects remain pending.

## Phase 4 - Pricing Configuration/Selection Feature - Complete

- Company-currency price per kg rules by type, grade, length and effective dates.
- Active overlap rejected, including bounds changed on shared length definitions.
- Exact/range/open lengths and inclusive date boundaries supported.
- Exactly one matching rule is required; archived/missing/ambiguous rules rejected.
- Private quote API computes currency-rounded payable kg × rate.
- Configuration admins mutate; hair users read; companies remain isolated.
- Eight pricing tests pass. No real rates seeded in hair_demo.
- Confirmation now applies quotes and preserves historical snapshots. Price
  override and chatter audit are implemented; real pricing data remains pending.

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
- Manager-only price override UI and audit are implemented (see below).

## Latest validation

- `ruff check .`: all checks passed, using the Odoo runbot rule configuration.
- scripts/test_addons.py: exit 0, 0 failed, 0 errors, 94 executed tests
  (92 custom and 2 automatically selected web cases).
- Isolated test database: hair_test_ae85946a862f.
- Final targeted inventory rerun: 15 tests, 0 failed, 0 errors.
- hair_purchase installed/updated in hair_demo; Hair Intakes list browser-verified.
- Environment and authenticated demo checks passed after inventory receipt update.
- Demo history, receipt/lot views and Product Unit precision >=3 verified through authenticated RPC.

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

## Inventory receipt policy resolved

The user answered that stock receipt before full payment is not permitted.
Unpaid/partially paid purchases must be blocked; only confirmed, fully settled
purchases may be received. The earlier receipt-policy question is resolved.

Next dependency: integrate inventory receipt with the implemented payment tracking and enforce
full settlement through server-side receipt guards. Manual payment tracking and partial receipt are implemented; full payment is enforced during receipt posting. Payment/stock reversal policy remains undefined;
paid/received cancellation must stay prohibited until a reversal workflow exists.
Real rates/effective dates are still required to use the commercial demo flow.
Remaining work: extended quality criteria,
optional accounting, processing, dashboards and later roadmap phases.

## Manager price override feature

- Approved, fresh inspection quotes support Manager/Admin reasoned rate overrides.
- Matrix base rate and latest actor/time/reason are protected from direct writes
  and forged defaults; every changed rate records old/new values in chatter.
- Confirmation revalidates the base pricing rule and preserves negotiated values.
- Repricing/return to draft resets current override fields, retaining audit history.
- Same-rate retries are no-ops; confirmed/terminal rates remain immutable.
- Five additional tests cover audit/retries, invalid rates/reasons, role/company
  isolation, forged provenance, stale rules/reset/copy and wizard/view access.

## Seller confirmed purchase statistics feature

- Buyer/Manager seller form includes confirmed purchase count, kg, last purchase
  date and totals grouped by frozen historical currency without conversion.
- Draft/inspection/rejected/cancelled purchases are excluded. State changes
  invalidate metrics; negotiated prices contribute their confirmed amounts.
- Purchases button filters seller and confirmed state using existing permissions.
- Grouped ORM queries run as the caller without sudo or new access grants.
- Automated tests cover lifecycle/reset, negotiated values, historical currencies,
  action domain, role/public/portal denial and foreign-company seller access.
- Paid and Received purchases contribute to confirmed history.

## Manual payment tracking feature

- Configurable company payment methods and separate Cashier role implemented.
- Draft payment records preserve seller/currency/purchase, amount/date/method,
  reference/notes; posting freezes actor/time and records chatter.
- Partial/full balances and unpaid/partial/paid status; fully settled purchases
  advance to Paid. Seller statistics include Paid purchases.
- Positive finite currency-precision amounts, outstanding balance, active methods,
  company access and confirmed state checked server-side under ORM parent locks.
- Posting retries do not duplicate totals/provenance. Stable request keys have
  database uniqueness; integrations must reuse their key on creation retries.
- Posted payments cannot be mutated/deleted. Any posted payment blocks purchase
  cancellation pending an explicit reversal policy. Direct state/provenance and
  total/context forgery blocked; Cashiers cannot grade/change kg or access NRC.
- Seven automated payment tests added. No real payment/provider or price data seeded.
- Manual record posting does not transfer funds or create accounting entries.
- Accounting bridge, separate payment vouchers and reversals remain pending; inventory receipt is implemented below.

## Inventory product configuration feature

- hair_inventory installed with standard stock dependency; hair type maps to a
  stock-tracked, lot-tracked kg product, shared or same-company.
- Inherited master ACL/company controls; linked product changes validate all
  mappings including archived types. Inactive products cannot resolve for receipt.
- Five tests pass; targeted rerun verifies archived mapping integrity.
- User authorized partial receipts after full payment. Cumulative receipt kg
  cannot exceed payable kg; Received requires complete receipt of all lines.
- Receipt posting and purchase/lot source links are implemented below; reversal workflow remains pending.

## Fully paid partial inventory receipt feature

- Separate Warehouse User inherits standard stock permissions, without Buyer,
  grading or NRC authority. Company restrictions apply to receipt headers/lines.
- Explicit supplier-to-internal Incoming operation; positive 0.001 kg quantities
  against purchase lines. Fully paid status checked server-side under ORM locks.
- Cumulative kg cannot exceed payable kg; all lines complete advances to Received.
- Standard picking/move/lot/quant operations; frozen source labels traced through
  receipt and purchase lines. Every partial receipt has its own source lots.
- Repeated receipt posting is a no-op; database uniqueness for picking/move/lot
  source links. Locked parent is updated for every partial receipt to prevent
  stale cumulative reads across concurrent transactions.
- Completed source quantities/details/links protected; stock-link/context forgery,
  adding stock details/moves, duplicate lot inbound and linked returns blocked.
- Product Unit global precision requires at least three decimals, matching user
  scale resolution. Fresh install hook sets this; demo configuration updated.
- Ten receipt tests cover physical quant/lot effects, partial and multi-line
  completion, limits/security/atomic failure/retries/immutability/returns.
- No reversal or accounting policy inferred. Real prices/product/operation setup
  still required before recording actual business purchases.

## Printable purchase receipt feature

- Bound QWeb PDF receipt for Buyer/Manager/Admin and Cashier, with server-side
  role and company read checks. Unconfirmed purchases cannot print.
- Frozen seller/classification/rate values, 0.001 kg weights, currency amounts
  and posted-only payment details; NRC and draft payments omitted.
- Cancelled confirmed purchases print a prominent label and reason.
- Explicit standard Odoo 20 base_report_wkhtmltox dependency; real PDF test
  passes using public assets from the running Compose service.
- Four report tests added. Full suite: 92 tests, zero failures/errors in
  hair_test_3ea695124065; final confirmation/report rerun: 28 tests, zero
  failures/errors, including rates with more than six decimal places. Ruff passes.
  Demo upgraded; report registration, authentication and startup verified.
- See HAIR_PURCHASE_RECEIPT.md for printing instructions and dependencies.

## Purchase search and filtering feature

- Standard Odoo search view now includes seller phone, type/grade/length text,
  lifecycle/payment status and date periods/custom ranges.
- Classification searches retain confirmed labels after master-name changes.
- Confirmed Purchases includes Confirmed/Paid/Received; Outstanding Payment
  excludes drafts and fully paid purchases. Header grouping includes seller,
  buyer, status, payment status, month and permitted company.
- No new permissions or sudo queries. Two tests exercise actual view domains,
  historical/current names, company isolation and partial/full payment changes.
- Full suite: 94 tests, zero failures/errors in hair_test_ae85946a862f. Ruff and
  environment/authenticated demo search-view checks pass. Demo upgraded.
- Initial test startup exhausted PostgreSQL clients; restarting this project's
  web service released pooled connections, and the fresh isolated rerun passed.
- Branch and inventory-lot search remain pending. Existing missing real rates,
  reversal policy and later processing/quality/dashboard work remain unchanged.
