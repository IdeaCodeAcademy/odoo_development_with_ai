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
