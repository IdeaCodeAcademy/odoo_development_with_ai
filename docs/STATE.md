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

## Latest validation

- `python3 scripts/test_addons.py`: exit 0, 0 failed, 0 errors, 15 executed
  tests (13 custom tests and 2 automatically selected web suite cases).
- Test database: hair_test_6e09cdc90408; isolated from hair_demo.
- `python3 scripts/check_environment.py`: passed.
- `python3 scripts/check_demo.py`: authentication, installed modules and web passed.
- `git diff --check`: passed.
- Test databases are retained for diagnosis; no business database was changed.

## Phase 2 policy and next work

User specified: Buyer can create/edit sellers; Manager/Admin can view NRC.
This policy resolves the seller authorization question. Implement hair_supplier
next, retaining company isolation and field-level NRC protection. Purchase
history/statistics depend on hair_purchase and will be added there.
