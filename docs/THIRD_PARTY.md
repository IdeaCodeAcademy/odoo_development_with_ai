# Third-party addons

## ICA Web Responsive

- Requested app: https://apps.odoo.com/apps/modules/20.0/ica_web_responsive
- Source: IdeaCodeAcademy/odoo_app_store, branch 20.0,
  commit b25251f5245847cc7e3f666e45f8bc1223f30ed3.
- Copied from the existing local checkout into addons/ica_web_responsive.
- Manifest license: LGPL-3; author: Agga, IdeaCode Academy.
- Dependencies: web and base_setup.
- Local security change: partner location updates use normal ORM access checks;
  removed implicit sudo for internal users to preserve company isolation.
- Added tests for cross-company location protection, allowed updates and theme
  preference ownership.
- No Mapbox token or external provider configuration is supplied.

Ruff compliance also normalizes Python imports/spacing, removes unused imports
and makes onchange None returns explicit. hair_base's model imports retain a
narrow I001 exemption because the abstract parent must register before its
length subclass; alphabetic sorting breaks Odoo registry initialization.
