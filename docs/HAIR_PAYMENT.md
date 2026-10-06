# Purchase payment tracking

This feature records seller payments made outside Odoo. Posting a record does
not transfer money, call a provider, create an accounting entry or reconcile a
bank statement. The optional account bridge remains a separate future module.

Configure company-specific Payment Methods as a configuration administrator.
No providers or real payments are seeded. Assign the separate Cashier role to
users who record payments; Managers are not automatically Cashiers. System
administrators inherit Cashier. Cashiers read/update confirmed/paid purchases
and read their lines, without Buyer/Quality/NRC permissions.

In Payment Records, select a confirmed purchase, enter a positive amount at its
frozen currency precision, date, method, reference and notes. Post Payment Record
records the actor and posting time and adds a purchase chatter entry. Drafts do
not settle balances. Partial payments keep the purchase Confirmed; full settlement
sets Paid. Payment totals/status remain protected derived fields. Seller purchase
statistics include both Confirmed and Paid purchases with historical currencies.

Posting locks the purchase and payment through ORM, rechecks the outstanding
balance and rejects overpayment, inactive/foreign-company methods, invalid amounts
and unconfirmed/rejected/cancelled purchases. Reposting the same record is a no-op.
For integrations, reuse the stable request_key when retrying payment creation;
a database uniqueness constraint blocks duplicate requests. A distinct key is a
new record, not a retry. Stored totals use standard compute_sudo to expose only
aggregates to purchase readers; payment details require Buyer or Cashier access.

Cancelled purchases and their unposted payment drafts are hidden from standalone
Cashiers; Buyers can still review their history. Draft payment details can be corrected or removed by Cashiers. Posted records
cannot be edited, moved, deleted or copied into another posted payment. Direct
provenance/state writes and forged defaults are blocked. Purchases with any
posted amount cannot be cancelled, including partial settlement, until a defined
reversal workflow exists. Paid confirmation retries preserve existing values.

Full payment is the prerequisite for inventory receipt integration.
Partial inventory/lot receipt is implemented by hair_inventory; reversals,
separate payment vouchers and accounting remain pending. Purchase QWeb receipts are implemented; see HAIR_PURCHASE_RECEIPT.md.
Seven payment tests exercise partial/full settlement, posting retry, overpayment,
invalid precision/values, roles/NRC/company isolation, provenance/context forgery,
immutable records/cancellation, views and duplicate request keys.
