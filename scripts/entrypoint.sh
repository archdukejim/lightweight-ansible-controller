#!/bin/bash
set -e

# Default to production HTTPS unless DEV_MODE is true
if [ "$DEV_MODE" = "true" ]; then
    echo "Starting in DEVELOPMENT mode (HTTP)..."
    exec uvicorn app.main:app --host 0.0.0.0 --port 8080
else
    echo "Starting in PRODUCTION mode (HTTPS)..."
    
    # Generate self-signed cert if missing
    if [ ! -f /certs/cert.pem ] || [ ! -f /certs/key.pem ]; then
        echo "No certificates found in /certs. Generating self-signed certificates..."
        mkdir -p /certs
        openssl req -x509 -newkey rsa:4096 -keyout /certs/key.pem -out /certs/cert.pem -sha256 -days 365 -nodes -subj "/CN=lightweight-ansible-controller"
    fi
    
    exec uvicorn app.main:app --host 0.0.0.0 --port 8443 --ssl-keyfile /certs/key.pem --ssl-certfile /certs/cert.pem
fi
