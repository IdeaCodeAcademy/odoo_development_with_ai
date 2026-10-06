# Odoo 20.0 Development Environment with Docker

## Overview

This repository contains a complete Odoo 20.0 development environment set up with Docker. Odoo is an all-in-one business software that includes CRM, e-commerce, billing, accounting, manufacturing, project management, and warehouse management capabilities.

## Prerequisites

- Docker (version 20.10 or higher)
- Docker Compose (version 2.0 or higher)

## Setup

### 1. Clone the repository

```bash
git clone git@github.com:IdeaCodeAcademy/odoo_development_with_ai.git
cd odoo_development_with_ai

### 2. Build and start the containers

```bash
docker-compose up -d

### 3. Verify the setup

Once the containers are running, you can access Odoo at:

- **Web Interface**: http://localhost:8069
- **Odoo Database**: The database will be created automatically

### 4. Access Odoo

1. Open your web browser
2. Navigate to http://localhost:8069
3. Log in with the default credentials:
   - **Username**: admin
   - **Password**: admin

### 5. First-time configuration

1. Configure your database settings
2. Install necessary modules
3. Set up your company information
4. Configure email settings if needed

## Configuration

### Custom Modules

To add custom Odoo modules:

1. Create your modules in the `custom_addons/` directory
2. Each module should have the standard Odoo directory structure
3. The modules will be automatically detected by Odoo

### Database Configuration

The default database is:
- **Host**: odoo-db
- **Port**: 5432
- **Username**: odoo
- **Password**: odoo
- **Database**: postgres

### Odoo Configuration

The Odoo configuration is stored in `config/odoo.conf` and includes:
- Database connection settings
- Server configuration
- Addon paths
- Logging settings

## Usage

### Running in development mode

```bash
# Start with auto-restart on changes
docker-compose up -d

# View logs
mkdir -p logs
docker logs -f odoo_20

# Stop containers
docker-compose down

# Restart containers
docker-compose restart

### Working with data

The following data volumes are persisted:
- `odoo_data`: Odoo application data
- `odoo_addons`: Odoo addons (shared volume)
- `postgres_data`: PostgreSQL database

To preserve data when stopping containers:

```bash
# Stop without removing data volumes
docker-compose down

# Remove data volumes (WARNING: this will delete all data)
docker-compose down -v

### Adding new modules

To add new Odoo modules to your development environment:

1. Create a new module directory in `custom_addons/`
2. Follow standard Odoo module structure
3. Include an `__manifest__.py` file
4. Restart the Odoo container

### Security

In production, you should:

1. Change the default admin password
2. Configure secure email settings
3. Use HTTPS
4. Implement proper access controls
5. Regularly update Odoo and dependencies

## Development Workflow

### 1. Initial Setup

1. Run `docker-compose up -d` to start the environment
2. Access Odoo at http://localhost:8069
3. Create an admin user and set up your database

### 2. Module Development

1. Develop Odoo modules in the `custom_addons/` directory
2. Test changes in the development environment
3. Push to version control when ready

### 3. Testing

1. Use the development environment for testing
2. Back up your data before making significant changes
3. Test modules thoroughly before deployment

## Troubleshooting

### Common Issues

#### Odoo won't start

Check the logs:

```bash
docker-compose logs -f odoo_20
```

#### Database connection errors

Ensure the PostgreSQL container is running:

```bash
docker-compose ps
```

#### Port conflicts

Check if another service is using port 8069 or 5432:

```bash
lsof -i :8069
lsof -i :5432
```

#### Slow performance

Increase Docker resources in Docker Desktop or Docker Engine configuration.

## Support

For help with this setup, please check the Odoo documentation or contact the development team.

## License

This project is part of the Odoo 20.0 development environment setup.

---

*Part of the IdeaCodeAcademy Odoo Development with AI project*

## Technical Details

### Docker Images Used

- **Odoo 20.0**: Official Odoo Docker image for development
- **PostgreSQL 15**: Official PostgreSQL Docker image for database

### Network Configuration

The containers communicate over the default Docker network. You can access:

- `odoo_20`: Odoo application container
- `odoo_db_20`: PostgreSQL database container

### Volume Management

All data is stored in Docker volumes, which will persist even if containers are recreated.

## Next Steps

Once you have the environment running:

1. Log in and configure your Odoo instance
2. Install necessary starter modules
3. Set up your company and business processes
4. Start developing custom Odoo modules

## Alternatives

If you prefer not to use Docker:

1. **Install Odoo directly**: Follow the official Odoo installation guide
2. **Use Odoo.sh**: Git-based deployment for small installations
3. **Use Odoo Enterprise**: For production deployments with additional features

## Contribution Guidelines

When contributing to this setup:

1. Follow the existing code style
2. Add comments for complex configuration
3. Test changes in a development environment first
4. Update documentation as needed

This README was generated as part of the Odoo 20.0 development environment setup.

---