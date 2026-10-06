# Odoo 20.0 Docker image for development
FROM odoo:20.0

LABEL maintainer="Odoo Development Team"
LABEL description="Odoo 20.0 development environment"

# Install additional dependencies for development
RUN apt-get update && apt-get install -y --no-install-recommends \
    python3-pip \
    git \
    nano \
    curl \
    wget \
    && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /mnt/omnidoc

# Create necessary directories
RUN mkdir -p addons custom_addons config logs

# Set Odoo configuration
ENV ODOO_CONF=/etc/odoo/odoo.conf

# Copy Odoo configuration
COPY config/odoo.conf /etc/odoo/odoo.conf

# Copy source code (use this as a base image, add your specific modules later)
# In a real setup, you would copy your specific Odoo modules here
COPY . /mnt/omnidoc/

# Set permissions
RUN chown -R odoo:odoo /var/lib/odoo
RUN chown -R odoo:odoo /mnt/omnidoc

EXPOSE 8069

CMD ["odoo", "--config=/etc/odoo/odoo.conf"]