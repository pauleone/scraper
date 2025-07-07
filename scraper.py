import os
import datetime
import time
import re
import logging
from google.oauth2.service_account import Credentials
from googleapiclient.discovery import build
from playwright.sync_api import sync_playwright, TimeoutError as PlaywrightTimeout
from bs4 import BeautifulSoup
import json

# Setup logging
logging.basicConfig(level=logging.INFO, format="%(message)s")
logger = logging.getLogger()

# --- CONFIG ---
SPREADSHEET_ID = '1UmYEGz8jibtvNUkq5X5HbG3lCdZTfQ4Blooq9bwDZwc'
SHEET_NAME = 'Caster Links'
ERROR_LOG_SHEET = 'Error Log'
SERVICE_ACCOUNT_FILE = os.environ.get("GOOGLE_CREDS_JSON")

# --- Google Sheets Auth ---
scopes = ['https://www.googleapis.com/auth/spreadsheets']
creds = Credentials.from_service_account_file(SERVICE_ACCOUNT_FILE, scopes=scopes)
service = build('sheets', 'v4', credentials=creds)

# --- Helpers ---
def get_today_header():
    return datetime.datetime.today().strftime('%Y-%m-%d')

def get_next_column(values):
    return len(values[0]) + 1  # assumes headers in first row

def write_error_log(row_index, vendor, url, error):
    error_data = [[str(datetime.datetime.now()), str(row_index), vendor, url, error]]
    service.spreadsheets().values().append(
        spreadsheetId=SPREADSHEET_ID,
        range=f"{ERROR_LOG_SHEET}!A1",
        valueInputOption='USER_ENTERED',
        body={'values': error_data}
    ).execute()

def write_price(sheet_data, row_index, price, col_letter, date_str):
    range_write = f"{SHEET_NAME}!{col_letter}{row_index+1}"
    header_cell = f"{SHEET_NAME}!{col_letter}1"
    service.spreadsheets().values().update(
        spreadsheetId=SPREADSHEET_ID,
        range=range_write,
        valueInputOption='USER_ENTERED',
        body={'values': [[price]]}
    ).execute()
    service.spreadsheets().values().update(
        spreadsheetId=SPREADSHEET_ID,
        range=header_cell,
        valueInputOption='USER_ENTERED',
        body={'values': [[date_str]]}
    ).execute()

def get_column_letter(col_index):
    result = ''
    while col_index > 0:
        col_index, remainder = divmod(col_index - 1, 26)
        result = chr(65 + remainder) + result
    return result

# --- Scraper Logic ---
def extract_price(playwright, vendor, url, selector, div_structure):
    browser = playwright.chromium.launch(headless=True)
    context = browser.new_context()
    page = context.new_page()
    try:
        page.goto(url, timeout=30000)

        # --- Vendor-specific logic ---
        if vendor.lower() == "grainger":
            content = page.content()
            data_text = re.search(r'window\.__PRELOADED_STATE__\s*=\s*(\{.*?\});', content, re.DOTALL)
            if data_text:
                data_json = json.loads(data_text.group(1))
                offers = data_json.get("productDetail", {}).get("product", {}).get("offers", [])
                if offers:
                    return f"${offers[0]['price']}"
            raise Exception("Grainger price not found in JSON.")

        elif vendor.lower() == "uline":
            html = page.content()
            soup = BeautifulSoup(html, "html.parser")
            attrib_tag = soup.find("attrib")
            if attrib_tag and attrib_tag.text.strip():
                return attrib_tag.text.strip()

        elif vendor.lower() == "menards":
            html = page.content()
            soup = BeautifulSoup(html, "html.parser")
            el = soup.select_one("td[data-at-id='full-price-discount-edlp']")
            if el:
                return el.text.strip()

        elif vendor.lower() == "castercity.com":
            page.wait_for_selector(".woocommerce-Price-amount.amount", timeout=10000)
            el = page.query_selector(".woocommerce-Price-amount.amount")
            if el:
                return el.inner_text().strip()

        # --- Fallback to Default Method ---
        if selector:
            page.wait_for_selector(selector, timeout=10000)
            el = page.query_selector(selector)
            if el:
                return el.inner_text().strip()

        elif div_structure:
            html = page.content()
            soup = BeautifulSoup(html, "html.parser")
            div = soup.find(attrs={"class": div_structure})
            if div:
                return div.text.strip()

        raise Exception("No price found using any method.")

    except Exception as e:
        raise e
    finally:
        context.close()
        browser.close()

# --- Main Execution ---
def main():
    sheet = service.spreadsheets().values().get(
        spreadsheetId=SPREADSHEET_ID, range=SHEET_NAME
    ).execute()
    values = sheet.get('values', [])

    if not values or len(values) < 2:
        logger.error("Sheet is empty or missing data")
        return

    today_str = get_today_header()
    next_col = get_next_column(values)
    col_letter = get_column_letter(next_col)

    headers = values[0]
    rows = values[1:]

    with sync_playwright() as p:
        for idx, row in enumerate(rows, start=1):
            try:
                vendor = row[1] if len(row) > 1 else ''
                url = row[2] if len(row) > 2 else ''
                selector = row[3] if len(row) > 3 else ''
                div_structure = row[4] if len(row) > 4 else ''
                expected_price = row[5] if len(row) > 5 else ''

                if not url:
                    continue

                logger.info(f"➡️  [{vendor}] Checking {url}")
                price = extract_price(p, vendor, url, selector, div_structure)

                if not price:
                    raise Exception("Price not found")

                logger.info(f"✅ [{vendor}] Found price: {price}")
                write_price(values, idx, price, col_letter, today_str)

            except Exception as e:
                logger.warning(f"❌ [{vendor}] Price not found: {str(e)}")
                write_price(values, idx, "$0.00", col_letter, today_str)
                write_error_log(idx + 1, vendor, url, str(e))

    logger.info("✅ All done.")

if __name__ == "__main__":
    main()