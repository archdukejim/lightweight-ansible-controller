FROM python:3.11-slim

# Install sshpass for Ansible password authentication & openssl for cert generation
RUN apt-get update && apt-get install -y --no-install-recommends \
    sshpass \
    openssl \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /opt/controller

# Copy requirements and install
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Create necessary directories
RUN mkdir -p /playbooks /certs /opt/controller/app /opt/controller/scripts

# Copy application files
COPY app/ /opt/controller/app/
COPY scripts/ /opt/controller/scripts/

RUN chmod +x /opt/controller/scripts/entrypoint.sh

# Expose HTTP and HTTPS ports
EXPOSE 8080 8443

ENV PLAYBOOKS_DIR=/playbooks
ENV PYTHONPATH=/opt/controller

ENTRYPOINT ["/opt/controller/scripts/entrypoint.sh"]
