# Architecture

## Platform and layout

Odoo 20.0 Community and PostgreSQL 16 run through Docker Compose. Custom
modules live under `addons/`. Odoo core remains unmodified. Business logic uses
ORM methods, constraints and Odoo access controls; raw SQL needs documented
justification. Check version-dependent APIs against the installed Odoo source.

## Modules and dependency direction

| Module | Dependencies | Responsibility |
| --- | --- | --- |
| hair_base | base | Company-scoped types, textures, colors, grades and length definitions; master-data user/configuration groups |
| hair_supplier | hair_base, contacts | Extend res.partner for seller identity/type and restricted information |
| hair_purchase | hair_base, hair_supplier, mail | Purchase headers/lines, weights, inspection, pricing, confirmation, receipts |
| hair_inventory | hair_purchase, stock | Standard stock receipt, lots and source purchase links |
| hair_payment | hair_purchase, account | Optional accounting/payment bridge using standard accounting models |
| hair_processing | hair_inventory, mrp | Standard manufacturing input/output lots, loss and yield |
| hair_dashboard | hair_purchase, hair_inventory, hair_processing | ORM analytical reporting and KPIs |

Dependencies point toward foundation modules only. Seller purchase statistics
are added by hair_purchase, avoiding a hair_supplier → hair_purchase cycle.
Payment tracking belongs to hair_purchase; accounting integration is optional
and isolated in hair_payment. Exact journals/provider setup requires business
configuration before implementation. Branch functionality is deferred until
branch membership/access policy is supplied; company isolation starts now.

## Workflow and transaction boundaries

Seller → Hair Intake → Weight → Quality/Grade → Pricing → Confirmation
→ Payment → Inventory Lot.

A hair.purchase header carries company, seller, buyer, currency, date, sequence
and lifecycle. hair.purchase.line carries classification, measured/deducted/net
weight, grade, selected pricing rule and the confirmed price snapshot. Multiple
lines are supported from the first intake implementation.

Draft → Inspection → Confirmed → Paid → Received, with Rejected and Cancelled
terminal states. Payment status is separate (unpaid/partial/paid). Future receipt
policy must specify whether partially/unpaid confirmed purchases can be received.
State changes run through authorized server actions; direct write/import/RPC
cannot bypass protected values or transition validation. Confirmation freezes
classification, weight, seller, grade, rate, rule and currency-rounded amount.
Until a correction policy is supplied, protected confirmed values stay immutable.

Inspection retains inspector, time, decision, grade, reason and standard
attachments. Pricing uses effective dates, company, optional branch, type,
grade, length and UoM/currency. Reject missing or ambiguous matching rules rather
than selecting an arbitrary rate. Prevent overlapping active rules in the same
pricing context. Preserve historical prices independently of mutable rules.

Stock uses stock.picking/move/move.line/lot and a source line link. Accounting
uses account.move/payment. Manufacturing uses mrp.production and standard stock
moves. Confirm/payment/receipt/completion actions must be retry-safe and tested
with database uniqueness and concurrency protection where needed.

## Phase 1 master data

Separate models: hair.type, hair.texture, hair.color, hair.grade and hair.length.
Each record has required company, name, ordering and active status. No seed
prices or mandatory classifications are inferred from illustrative examples.
Demo-only records provide illustrative type, texture, color, grade and length.
Archive unused configuration rather than removing history. Future transaction
relations use ondelete='restrict' and check_company=True.

Lengths are in inches. An exact length has equal inclusive bounds; a range has
inclusive minimum/maximum, or an explicit open upper bound. Bounds are finite,
nonnegative and ordered. Master definitions can overlap because their pricing
context does not exist yet; Phase 4 enforces rule-context non-overlap.

Hair users read master data; configuration administrators create/update/archive
it. No deletion permission is granted. Administrators inherit configuration
access. The installed Odoo 20 build uses unified ir.access permissions/restrictions
(instead of ir.model.access/ir.rule). ir.access.csv grants read to users and
create/read/update to configuration administrators. Global company restrictions
apply to all five models; no public/portal permissions. Company reassignment is
authorized before write because Odoo 20 runs constraints with sudo.
Buyer, quality, cashier, warehouse and branch authority are introduced in the
owning transactional modules after their policies are defined.

## Verification

Run environment smoke checks, then Odoo TransactionCase tests in a dedicated
hair_test database. Never run module tests against a business database. Test
installation, validation, archive behavior, read/write/delete permissions,
public access rejection and multi-company reads/writes. Use post-install tests
and stop-after-init, without exposing the test container's HTTP port.

## Decisions required before later features

- Seller policy resolved: Buyers create/edit; Managers/Admin access NRC.
- Quality policy delegated: Quality Officer approves final grade; type, length
  and grade are required for pricing. Additional criteria remain configurable.
- Commercial policy delegated: Manager/Admin confirm, override with reason and
  cancel. Protected confirmed corrections remain prohibited without a correction workflow.
- Are receipts allowed before full payment, and what is the reversal policy?
- Are branches enabled initially, and how are users assigned to branches?
- Weight unit resolved: kg. Resolution confirmed: 0.001 kg (1 g). Currency confirmed: MMK. Real rates and effective dates need configuration.

These decisions gate the affected features, not independent foundation work.

## Implemented draft intake

Weights use fixed three-decimal kg precision as confirmed by the user. Drafts
use company currency and generated references, support multiple lines and
standard mail attachments. Calculated quantities are protected from direct
write/import. Changing company after adding lines is prohibited. Only draft
state is implemented until pricing/quality and commercial action policies are
ready; no financial or stock effects occur.

Ruff uses the Odoo runbot configuration in ruff.toml and must pass before commits.

## Pricing rule selection

hair.pricing.rule belongs to hair_purchase and uses company currency and per-kg
rates. Required matching dimensions are company, type, grade, inclusive length
bounds and effective dates. Active overlaps are rejected; length master changes
revalidate affected rules. Matching covers the whole chosen intake length
interval and returns exactly one rule or a validation error. Company isolation
and configuration-admin mutation permissions are enforced. Rates have no fixed
quantity precision; payable weights remain three-decimal kg quantities. No real
rates are seeded. Quote application, confirmation snapshots and override audit
remain distinct pending features.

## Seller intake history

hair_purchase extends res.partner with a seller-filtered intake action and grouped
nonstored count/payable kg/last-date metrics. The grouped ORM query runs without
sudo; fields and action require Buyer access. Dependencies invalidate totals when
intakes, line weights or seller/date change. Draft metrics are labeled as intakes;
confirmed purchased-weight/value statistics belong to the later commercial flow.
