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
all purchase lines are fully received. Product mapping, partial receipt posting and purchase-to-lot links are implemented.

## Partial stock receipts

Assign Hair Inventory / Warehouse User. This role inherits standard stock user
permissions and reads/updates fully paid or received hair purchases, without
Buyer, Quality Officer or NRC authority. In Hair Receipts, choose a paid purchase,
a company Incoming operation (supplier → internal stock), and purchase lines with
positive quantities at 0.001 kg precision. Choose the operation explicitly; no
warehouse/location policy is inferred. Draft records do not change stock.

Receive Hair checks full payment, source-line/company consistency, active mapped
products and cumulative received quantities under ORM purchase/receipt locks.
Each posted receipt creates one standard picking, one move and one source lot
per receipt line. Repeated posting of the same receipt is a no-op. Database
uniqueness prevents multiple pickings/moves/lots for the same receipt/source line.
Different partial receipts create separate traceable lots. Only complete receipt
of every purchase line changes Paid to Received. Seller statistics include
Received purchases; Cashier payment history remains readable after receipt.

Lots link through receipt line → purchase line → purchase and expose frozen
seller/type/grade/length labels, purchase date and original lot kg in the Hair
Source section. Stock quants/lot quantities come from standard stock operations.
The Product Unit precision is raised to at least 3 on fresh installation, using
standard configuration data; existing installations must apply the same setting
before receipt. This global Odoo precision setting also affects other stock units.

Completed receipt records, source moves/details and lot source/product/company
cannot be rewritten. Direct/context stock-source forgery, adding moves/details to
completed transfers and re-receiving a source lot from a supplier outside its
original receipt are blocked. Linked standard return operations are blocked until
a reversal policy is defined. Ordinary downstream stock operations retain standard
Odoo permissions. No raw SQL or custom accounting entries are introduced.

Every partial receipt updates provenance on the locked purchase, forcing stale
repeatable-read transactions to retry, and refreshes cumulative quantity caches.
Ten receipt tests exercise partial/full and multi-line completion, exact 1 g
quantities, lot/quant traceability, retries, payment/over-receipt guards, role/NRC
and company isolation, atomic failures, source/context forgery, extra stock detail
prevention, immutability and return blocking. Real rates, mapped products and
receipt operations require business configuration; no business purchases are seeded.

Further partial receipts reuse the original source product even if the Hair Type
mapping changes. Original source products retain compatible kg/lot configuration;
archiving them prevents further receipt. Historical product references stay fixed.
