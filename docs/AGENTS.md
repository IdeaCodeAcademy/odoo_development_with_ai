# Project instructions

You are implementing an Odoo 20.0 Community project.

Read before working:
1. docs/REQUIREMENTS.md
2. docs/ARCHITECTURE.md
3. docs/ROADMAP.md
4. docs/STATE.md

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
9. Update docs/STATE.md.
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

## Odoo contribution guidelines

Read and follow these official Odoo guidelines before implementing changes or
creating commits:

- [Git guidelines](https://www.odoo.com/documentation/19.0/contributing/development/git_guidelines.html)
- [Coding guidelines](https://www.odoo.com/documentation/19.0/contributing/development/coding_guidelines.html)

Apply the Git guidelines to commit structure, commit messages, and change scope.
Apply the coding guidelines to Python, XML, JavaScript, model conventions, and
module organization as relevant to the change.

These references are for Odoo 19.0. This project targets Odoo 20.0 Community;
verify version-dependent APIs and behavior against Odoo 20.0 documentation and
the installed Odoo 20.0 implementation. Use Odoo 20.0 conventions when they
differ from the linked Odoo 19.0 guidance.
