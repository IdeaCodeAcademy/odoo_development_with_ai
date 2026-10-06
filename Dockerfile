# Odoo 20.0 Docker image for development
FROM odoo:20.0

USER root

COPY ./requirements.txt /mnt/requirements.txt
RUN pip install --no-cache-dir --target=/opt/odoo-dependencies -r /mnt/requirements.txt
ENV PYTHONPATH=/opt/odoo-dependencies

USER odoo
