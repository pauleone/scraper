# Scraper

This project scrapes prices from various vendor websites and records them into a Google Sheet. It also exposes a small Flask API that can trigger the scraper remotely.

## Requirements

- Python 3.10+
- [pip](https://pip.pypa.io/en/stable/)

Install Python dependencies and Playwright browsers:

```bash
pip install -r requirements.txt
playwright install
```

`playwright install` is required the first time to download the Chromium browser used for scraping.

## Service account credentials

The scraper uses a Google service account to access the spreadsheet. Set an environment variable pointing to your JSON credentials before running the scripts:

```bash
export SERVICE_ACCOUNT_FILE=/path/to/your-service-account.json
```

If the variable is not set the default path `caster-scraper-a25d671c35f0.json` in the repository root is used.

## Running the API

Start the Flask server with:

```bash
python3 api.py
```

Send a POST request to `/scrape` to begin scraping. For example:

```bash
curl -X POST http://localhost:5050/scrape
```

The endpoint launches `scraper.py` and returns its console output.

## Google Sheet structure

The sheet contains a header row followed by one row per item. Columns are organised as:

1. **Item name** – human readable identifier (not used by the script)
2. **Vendor** – e.g. Grainger, Uline
3. **URL** – product page to scrape
4. **CSS selector** – optional selector for the price element
5. **Div class** – optional fallback class name
6. **Expected price** – optional reference value

Each execution appends a new column with the current date and the scraped prices.
