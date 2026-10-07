# Hair Base

Phase 1 provides company-specific hair types, textures, colors, grades and
length definitions. Open Hair Purchasing → Configuration to maintain them.

Assign Hair Master Data / User for read access, or Configuration Administrator
for creation, updates and archiving. Odoo administrators inherit configuration
access. Public/portal and unrelated internal users receive no access. Deletion
is unavailable; archive configuration instead. Company switching controls which
company's data is visible, and company reassignment requires permission.

Lengths use inches. Equal bounds describe an exact length; differing bounds
describe an inclusive range. No Upper Limit supports a range such as 27+.
Bounds must be finite, nonnegative and ordered. Overlap validation belongs to
Phase 4 pricing contexts, which are not implemented yet.

Illustrative demo master data is loaded only when Odoo demo data is enabled.
There are no real price rules, sellers, purchases or payments yet.

Run `python3 scripts/test_addons.py` for validation, permission, company
isolation and view tests in a fresh test database.

## Application icon

Hair Purchasing uses a bundled 256 × 256 PNG hair-bundle icon in the application
launcher. The standard menu web_icon attribute loads it; existing menu groups
and access permissions apply. Upgrade hair_base and reload the browser to refresh
the cached launcher image.
