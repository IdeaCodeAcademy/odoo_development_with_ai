# Hair inventory configuration

hair_inventory depends on hair_purchase and standard Odoo stock. Configuration
administrators map each Hair Type to an existing stock product. Products must
be stock-tracked, use lot tracking and kg units; shared or matching-company
products are allowed. No products, prices or warehouse choices are invented.

Readers can inspect mappings; configuration mutation uses inherited hair.type
permissions/company restrictions. Linked product changes are revalidated across
all mapped types, including archived types. Narrow sudo serves integrity
validation only, retaining product write permissions and exposing no other data.
Archived products cannot resolve for receipt. Five tests verify valid/missing
mapping, units/tracking, product changes, archive behavior, roles and companies.

Receipt quantity policy: the user allows partial receipts after full payment.
Cumulative received kg must not exceed payable kg. Received is reached only after
all purchase lines are fully received. Product mapping is implemented; receipt
posting and purchase-to-lot links are the next feature.
