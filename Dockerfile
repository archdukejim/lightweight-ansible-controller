FROM registry.access.redhat.com/ubi9/ubi-minimal:latest

# Install EPEL (for sshpass) and required packages to enforce FIPS compatibility when running on FIPS host
RUN rpm -ivh https://dl.fedoraproject.org/pub/epel/epel-release-latest-9.noarch.rpm && \
    microdnf install -y python3 python3-pip sshpass openssl && \
    microdnf clean all

WORKDIR /opt/controller

# Copy requirements and install
COPY requirements.txt .
RUN pip3 install --no-cache-dir -r requirements.txt

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
