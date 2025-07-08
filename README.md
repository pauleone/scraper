# scraper

This project scrapes vendor product prices using Playwright and logs the results
in Google Sheets.

## Installation

1. **Install Python requirements**
   ```bash
   python3 -m venv venv
   source venv/bin/activate
   pip install -r requirements.txt
   ```
2. **Install Playwright browsers** (required once per machine)
   ```bash
   playwright install
   ```

## Configuration

The repository includes a service account file named `GOOGLE_APPLICATION_CREDENTIALS`.
Export its path so the Google Sheets API can authenticate:

```bash
export GOOGLE_APPLICATION_CREDENTIALS=$(pwd)/GOOGLE_APPLICATION_CREDENTIALS
```

## Running the scraper

Execute the scraper directly to update the sheet using the legacy script now named `scraper_new.py`:

```bash
python3 scraper_new.py
```

Alternatively, start the Flask API and trigger a run with a POST request:

```bash
# Start the API server
python3 api.py

# In another terminal
curl -X POST http://localhost:5050/scrape
```

## SSL troubleshooting

If you encounter `SSL: CERTIFICATE_VERIFY_FAILED` errors when connecting to
Google Sheets, your system certificates may be outdated. Updating the
`certifi` package often resolves this:

```bash
pip install --upgrade certifi
```

On Linux ensure the `ca-certificates` package is installed. On macOS you can run
`Install Certificates.command` from your Python installation.
