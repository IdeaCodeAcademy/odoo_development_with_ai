# Odoo 20.0 Development Environment

Docker Compose runs Odoo 20.0 and PostgreSQL 16.

## Setup

1. Install and start Docker Desktop.
2. Create `odoo_pg_pass` containing your database password. This file is ignored by Git.
3. Run:

```bash
docker compose up -d --build
```

Open http://localhost:8071 and create your Odoo database and administrator account.
The host port is 8071 because 8069 is used by another local Odoo instance.

## Development

Place custom modules in `addons/`. Add Python dependencies to `requirements.txt`
and rebuild the web image. Odoo settings are in `config/odoo.conf`; the database
password is supplied through the Docker secret.

```bash
docker compose logs -f web
docker compose ps
docker compose restart web
docker compose down
```

The `odoo-web-data` and `odoo-db-data` volumes preserve application and database
data when containers stop. Avoid removing these volumes if you need the data.

## Project documentation

- [Agent instructions](docs/AGENTS.md)
- [Requirements](docs/REQUIREMENTS.md)
- [Architecture](docs/ARCHITECTURE.md)
- [Roadmap](docs/ROADMAP.md)
- [Implementation state](docs/STATE.md)

Read these documents before working on the project.
