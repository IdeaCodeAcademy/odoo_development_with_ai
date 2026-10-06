# Seller Management

`hair_supplier` extends standard Contacts with seller status, company, configurable
seller type, alternative phone, township and notes. Archive sellers to retain history.
Buyers create/edit sellers. Managers and Administrators can read/write optional NRC;
field-level protection applies to views, ORM, RPC, search and imports. Existing
contact permissions do not grant seller management. Company isolation applies to
all sellers. Purchase statistics will be added by hair_purchase.

Seven automated tests cover seller mutations, NRC protection, imports, unrelated
contact permissions, company isolation, validation and form visibility.

## Intake history

When hair_purchase is installed, the seller form provides an Intakes smart
button, total intake payable kg and last intake date. The button opens that
seller's intakes and defaults the seller/company for a new record. These figures
include draft intake records; they do not represent confirmed purchased stock or
paid purchases. Commercial purchase/value statistics follow confirmation.

Aggregation uses one Odoo `_read_group` call under the current user's company
access rules, without sudo. History fields and the action are restricted to
Buyers/Managers/Admin. Totals update after lines or seller/date change, and empty
history returns zero totals and no date.
