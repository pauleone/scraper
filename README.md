# scraper

This project uses Python to scrape data and update a Google Sheets document. When running inside a network that intercepts HTTPS traffic, Google API calls may fail with SSL errors unless the proxy's certificate is trusted. This repository includes guidance for configuring certificate trust.

## Installing the proxy certificate

1. Obtain the proxy's certificate (for example `envoy-mitmproxy-ca-cert.crt`).
2. Copy the certificate to `/usr/local/share/ca-certificates/`.
3. Run the helper script to install it:

```bash
sudo ./install_proxy_cert.sh
```

The script updates the system trust store and sets the `REQUESTS_CA_BUNDLE` environment variable to the certificate path.

If you prefer manual steps, run `sudo update-ca-certificates` and then add the following to your shell profile:

```bash
export REQUESTS_CA_BUNDLE=/usr/local/share/ca-certificates/envoy-mitmproxy-ca-cert.crt
```

## Troubleshooting

- **SSL: CERTIFICATE_VERIFY_FAILED** – Verify that the certificate file exists and that `REQUESTS_CA_BUNDLE` points to it. Use `echo $REQUESTS_CA_BUNDLE` to check the value.
- **Permission denied** when running the script – Ensure you execute the script with `sudo` so it can write to system certificate locations.
- After updating certificates you may need to restart the application or shell so that new environment variables take effect.
