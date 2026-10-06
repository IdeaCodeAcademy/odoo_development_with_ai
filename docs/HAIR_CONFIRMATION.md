# Commercial Confirmation and Cancellation

After Quality Officer approval, a Manager/Admin uses Compute Price, reviews the
Commercial tab and total, then uses Confirm Purchase. Each line
requires approved grade, type, length and positive payable kg. The pricing engine
must find exactly one active rule for company/type/grade/length and purchase date.
Missing prices fail without partially confirming a purchase. If rates, currency
or classification change after quoting, confirmation requires explicit repricing
and review. Returning to draft clears the quote along with quality approval.

Confirmation saves rule, per-kg rate and currency-rounded line amount. It retains
company currency, seller name, type/grade/length labels and length bounds as
historical snapshots. Header amount totals sum the rounded line amounts. Changes
to rules, names, length definitions or company currency do not rewrite confirmed
values. Repeated confirmation keeps the original time, actor and pricing.

Confirmed inputs cannot change through UI, ORM, RPC or import. Copying creates a
fresh draft without copied inspection/confirmation provenance or monetary values.
There is no correction workflow for confirmed financial information.

Managers/Admin may cancel Draft, Inspection or Confirmed purchases with a
mandatory reason. Cancellation retains snapshots and records actor/time; retries
retain that provenance. Rejected and Cancelled are terminal. Paid/Received states
are not implemented and must use a defined future reversal workflow, not this
cancellation path. Buyers and Quality Officers cannot confirm/cancel.

These actions use company access rules, private action-only snapshot writes and
ORM row locks. Standard chatter tracks confirmation/cancellation. No payments,
accounting entries or stock movements are created by this feature. Manager price overrides are implemented as described below.

Fourteen automated tests cover snapshots/retries, rule/name/bounds/currency changes,
missing approval/pricing, quote review/staleness/reset, protected input and snapshot forgery, role isolation,
reasoned cancellation and foreign-company actions. Only synthetic test rates are
used; no real or sample rates are activated in hair_demo.

## Manager price override

On the Commercial tab, Manager/Admin can open Override Price on a quoted line,
enter a positive finite per-kg rate and a mandatory reason. Only approved,
freshly quoted inspection purchases can be overridden. A changed base rule,
classification or company currency requires Compute Price and another review.

Protected line fields retain the matrix base rate, latest actor, timestamp and
reason. Every rate change posts the previous/new rate, currency, line and reason
to standard Odoo chatter, whose author and timestamp provide the audit trail.
Repeated application of the current rate is a no-op. Repeated negotiated changes
retain the original matrix rate and each chatter entry. No custom duplicate
audit model, sudo, context bypass or raw SQL is needed.

Confirmation preserves the negotiated rate and rounded amount while checking
that the underlying matrix rule remains applicable and unchanged. Repricing or
returning to draft clears the current override provenance; chatter history
remains. Copies start without overrides. Confirmed/terminal prices cannot be
overridden. Buyer, Quality Officer and public calls, forged provenance/defaults,
foreign-company access and unauthorized wizard creation are tested.
