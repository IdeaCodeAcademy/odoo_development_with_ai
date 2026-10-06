# Architecture

## Platform and layout

Odoo 20.0 Community and PostgreSQL 16 run through Docker Compose. Custom
modules live under `addons/`. Odoo core remains unmodified. Business logic uses
ORM methods, constraints, ACLs and record rules; raw SQL needs documented
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
Archive unused configuration rather than removing history. Future transaction
relations use ondelete='restrict' and check_company=True.

Lengths are in inches. An exact length has equal inclusive bounds; a range has
inclusive minimum/maximum, or an explicit open upper bound. Bounds are finite,
nonnegative and ordered. Master definitions can overlap because their pricing
context does not exist yet; Phase 4 enforces rule-context non-overlap.

Hair users read master data; configuration administrators create/update/archive
it. No deletion permission is granted. Administrators inherit configuration
access. Global company rules apply to all five models; no public/portal ACLs.
Buyer, quality, cashier, warehouse and branch authority are introduced in the
owning transactional modules after their policies are defined.

## Verification

Run environment smoke checks, then Odoo TransactionCase tests in a dedicated
hair_test database. Never run module tests against a business database. Test
installation, validation, archive behavior, read/write/delete permissions,
public access rejection and multi-company reads/writes. Use post-install tests
and stop-after-init, without exposing the test container's HTTP port.

## Decisions required before later features

- Which roles may create/edit sellers and view NRC/identification information?
- Which inspection criteria are required, and who approves the final grade?
- Which roles may confirm, override prices, cancel or correct purchases?
- Are receipts allowed before full payment, and what is the reversal policy?
- Are branches enabled initially, and how are users assigned to branches?
- Which weight precision/UoM, currency, real rates and effective dates apply?

These decisions gate the affected features, not independent foundation work.
