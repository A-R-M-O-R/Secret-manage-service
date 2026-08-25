#!/usr/bin/env bash

set -euo pipefail

NGINX_LOG_DIR="/var/log/secret-service/nginx"
NGINX_BLOCKLIST_DIR="/var/log/secret-service/nginx-blocklist"
NGINX_BLOCKLIST_FILE="${NGINX_BLOCKLIST_DIR}/blocked_ips.conf"

echo "Preparing host paths for Secret Management Service observability..."

echo "Creating log directory: ${NGINX_LOG_DIR}"
sudo mkdir -p "${NGINX_LOG_DIR}"

echo "Creating blocklist directory: ${NGINX_BLOCKLIST_DIR}"
sudo mkdir -p "${NGINX_BLOCKLIST_DIR}"

echo "Creating nginx log files if they do not exist..."
sudo touch "${NGINX_LOG_DIR}/access.log"
sudo touch "${NGINX_LOG_DIR}/access_wazuh.json"
sudo touch "${NGINX_LOG_DIR}/error.log"

if [ ! -f "${NGINX_BLOCKLIST_FILE}" ]; then
  echo "Creating empty blocklist file: ${NGINX_BLOCKLIST_FILE}"
  sudo tee "${NGINX_BLOCKLIST_FILE}" >/dev/null <<'EOF'
# Temporary IP blocklist for Wazuh Active Response.
# Format:
#   192.168.31.110 1;
#
# Empty file = no IP is blocked.
EOF
fi

echo "Setting permissions..."
sudo chmod 755 "${NGINX_LOG_DIR}"
sudo chmod 755 "${NGINX_BLOCKLIST_DIR}"

sudo chmod 644 "${NGINX_LOG_DIR}/access.log"
sudo chmod 644 "${NGINX_LOG_DIR}/access_wazuh.json"
sudo chmod 644 "${NGINX_LOG_DIR}/error.log"
sudo chmod 644 "${NGINX_BLOCKLIST_FILE}"

echo
echo "Done."
echo
echo "Nginx logs:"
echo "  ${NGINX_LOG_DIR}/access.log"
echo "  ${NGINX_LOG_DIR}/access_wazuh.json"
echo "  ${NGINX_LOG_DIR}/error.log"
echo
echo "Nginx temporary blocklist:"
echo "  ${NGINX_BLOCKLIST_FILE}"