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
- Purchase history/statistics remain dependent on hair_purchase.

## Phase 3 - Draft Intake and Weight Feature - Complete

- hair_purchase provides draft headers, unique sequences and multiple hair lines.
- User confirmed kg at 0.001 kg (1 g) scale resolution; three decimal places.
- Gross less tare/waste/moisture/other deductions computes payable kg and totals.
- Server validation rejects negative/nonfinite weights and excessive deductions.
- Company isolation, relation integrity and forged calculated values are tested.
- Seven intake tests cover calculations, validation, permissions and view loading.
- Inspection submission/confirmation and commercial effects are not implemented.

## Latest validation

- `ruff check .`: all checks passed, using the Odoo runbot rule configuration.
- scripts/test_addons.py: exit 0, 0 failed, 0 errors, 29 executed tests
  (27 custom and 2 automatically selected web cases).
- Isolated test database: hair_test_d27b8623f932.
- Installed in hair_demo; browser Hair Intakes list verified. Environment and
  authenticated demo checks passed.

## Next work and delegated workflow policy

User authorized suitable commercial/quality policy. Manager/Admin will confirm,
override prices (with a reason) and cancel. Quality Officer will approve final
grades. Confirmation requires seller, positive payable kg, hair type, length,
approved grade and a valid pricing rule. Implement these server-enforced actions
in later workflow features; this authorization resolves the role-policy blocker.

Next: configurable company/type/grade/length/date pricing rule selection. Real
rates and company currency are business configuration and will not be invented.
