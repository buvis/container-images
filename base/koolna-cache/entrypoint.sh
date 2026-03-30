#!/bin/sh
set -eu

SSL_DIR="/etc/squid/ssl_cert"
CA_CERT="$SSL_DIR/ca.pem"
CA_KEY="$SSL_DIR/ca.key"
SSL_DB="/var/spool/squid/ssl_db"
NAMESPACE="${KOOLNA_NAMESPACE:-default}"
CONFIGMAP_NAME="koolna-cache-ca"

# Generate CA cert on first start
if [ ! -f "$CA_CERT" ]; then
  echo "generating CA certificate..."
  openssl req -new -newkey rsa:2048 -sha256 -days 3650 -nodes \
    -x509 -subj "/CN=koolna-cache-ca" \
    -keyout "$CA_KEY" -out "$CA_CERT"
  chown proxy:proxy "$CA_CERT" "$CA_KEY"
  chmod 600 "$CA_KEY"
fi

# Export CA cert to ConfigMap
export_ca_configmap() {
  TOKEN=$(cat /var/run/secrets/kubernetes.io/serviceaccount/token)
  CA_BUNDLE=/var/run/secrets/kubernetes.io/serviceaccount/ca.crt
  API_SERVER="https://kubernetes.default.svc"

  cert_data=$(cat "$CA_CERT" | sed 's/"/\\"/g' | awk '{printf "%s\\n", $0}')

  payload="{\"apiVersion\": \"v1\", \"kind\": \"ConfigMap\", \"metadata\": {\"name\": \"$CONFIGMAP_NAME\", \"namespace\": \"$NAMESPACE\"}, \"data\": {\"ca.crt\": \"$cert_data\"}}"

  http_code=$(curl -s -o /dev/null -w "%{http_code}" -X PUT \
    -H "Authorization: Bearer $TOKEN" \
    -H "Content-Type: application/json" \
    --cacert "$CA_BUNDLE" \
    "$API_SERVER/api/v1/namespaces/$NAMESPACE/configmaps/$CONFIGMAP_NAME" \
    -d "$payload")

  if [ "$http_code" = "404" ]; then
    http_code=$(curl -s -o /dev/null -w "%{http_code}" -X POST \
      -H "Authorization: Bearer $TOKEN" \
      -H "Content-Type: application/json" \
      --cacert "$CA_BUNDLE" \
      "$API_SERVER/api/v1/namespaces/$NAMESPACE/configmaps" \
      -d "$payload")
  fi

  if [ "$http_code" != "200" ] && [ "$http_code" != "201" ]; then
    echo "warning: failed to export CA to ConfigMap ($http_code)"
  else
    echo "CA certificate exported to ConfigMap $CONFIGMAP_NAME"
  fi
}

# Export CA if running in Kubernetes (service account present)
if [ -f /var/run/secrets/kubernetes.io/serviceaccount/token ]; then
  export_ca_configmap
else
  echo "not running in Kubernetes, skipping ConfigMap export"
fi

# Initialize squid cache directories
echo "initializing cache directories..."
squid -z --foreground -f /etc/squid/squid.conf 2>&1

# Initialize SSL certificate database
if [ ! -d "$SSL_DB" ]; then
  echo "initializing SSL certificate database..."
  /usr/lib/squid/security_file_certgen -c -s "$SSL_DB" -M 64MB
  chown -R proxy:proxy "$SSL_DB"
fi

echo "starting squid..."
exec squid -N -f /etc/squid/squid.conf
