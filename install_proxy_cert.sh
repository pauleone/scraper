#!/bin/bash
# install_proxy_cert.sh - Install proxy certificate for Google API requests
# Usage: sudo ./install_proxy_cert.sh

set -e

CERT_PATH="/usr/local/share/ca-certificates/envoy-mitmproxy-ca-cert.crt"

if [ ! -f "$CERT_PATH" ]; then
    echo "Place your proxy certificate at $CERT_PATH" >&2
    echo "Then run this script again to install it." >&2
    exit 1
fi

sudo update-ca-certificates

export REQUESTS_CA_BUNDLE="$CERT_PATH"

echo "System certificates updated." >&2
echo "REQUESTS_CA_BUNDLE set to $CERT_PATH" >&2

