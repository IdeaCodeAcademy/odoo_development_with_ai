# Project instructions

You are implementing an Odoo 20.0 Community project.

Read before working:
1. REQUIREMENTS.md
2. ARCHITECTURE.md
3. ROADMAP.md
4. STATE.md

Work autonomously.

For each feature:
1. Inspect existing implementation.
2. Identify dependencies.
3. Implement the smallest complete feature.
4. Add/update security.
5. Add automated tests.
6. Run relevant tests.
7. Fix failures before continuing.
8. Update documentation.
9. Update STATE.md.
10. Commit the completed feature.

Never:
- invent business requirements
- modify Odoo core
- bypass ORM without justification
- weaken access control to make tests pass
- mark a feature complete while tests fail

Use Odoo 20 conventions.

Git commits must follow Odoo contribution conventions:
[TYPE] module: short description

Examples:
[ADD] hair_purchase: add hair purchase intake
[IMP] hair_purchase: compute net hair weight
[FIX] hair_inventory: correct lot traceability
[ADD] hair_dashboard: add purchase KPI dashboard
