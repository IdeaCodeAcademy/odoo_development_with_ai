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

## Latest validation

- scripts/test_addons.py: exit 0, 0 failed, 0 errors, 22 executed tests
  (20 custom and 2 automatically selected web cases).
- Isolated test database: hair_test_0c1b9c2fbd98.
- Environment and authenticated demo checks pass.

## Next work

Phase 3 draft intake and weights. User specified kilograms. Scale resolution
is pending clarification; development precision is configurable, initially 3
kg decimal places. Commercial confirmation awaits pricing/quality policy.
