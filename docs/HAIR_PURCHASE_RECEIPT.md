# Hair Purchase Receipt

Open a commercially confirmed purchase and choose **Print → Hair Purchase
Receipt**. Buyer (including Manager/Admin) and Cashier can print it. Draft,
inspection and rejected intakes cannot produce a receipt. A cancelled previously
confirmed purchase prints a prominent CANCELLED label and cancellation reason.

The PDF contains the purchase reference/date, frozen seller and hair
classification, payable kilograms at 0.001 kg precision, confirmed price per kg,
line amounts and currency totals. It also shows payment status, posted payment
amounts, balance and posted payment dates/methods/references. Draft payments and
seller NRC are excluded. Recorded payments do not themselves transfer funds.

The report checks role, underlying purchase read access and company boundaries
on the server. Menu visibility alone does not grant report access. No report
attachment is cached: payment figures reflect the current posted records.

The module explicitly depends on Odoo 20's standard `base_report_wkhtmltox`
PDF engine. The development Docker image supplies wkhtmltopdf. Automated tests
cover HTML snapshots, posted-only payments, roles/company isolation, unconfirmed
purchases, cancelled labels and actual PDF rendering. PDF tests fetch public
assets from the running Compose web service; start the environment before tests.
