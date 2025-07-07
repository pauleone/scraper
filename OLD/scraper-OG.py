import datetime
import asyncio
import re
from urllib.parse import urlparse
from google.oauth2 import service_account
from googleapiclient.discovery import build
from playwright.async_api import async_playwright, TimeoutError as PlaywrightTimeoutError

# === CONFIG ===
SPREADSHEET_ID = '1UmYEGz8jibtvNUkq5X5HbG3lCdZTfQ4Blooq9bwDZwc'
LINKS_TAB = 'Caster Links'
ERROR_TAB = 'Error Log'
START_ROW = 2
CREDENTIALS_FILE = 'caster-scraper-a25d671c35f0.json'
HEADLESS = True  # Set to False for visual debugging

# === VENDOR DEFAULT SELECTORS ===
VENDOR_SELECTOR_MAP = {
    'Harbor Freight': '#dy-pdp-price-label',
    'Menards': '.full-price-discount-edlp',
    'CasterCity.com': '.woocommerce-Price-amount.amount',
    'MSC Direct': '#totalPriceId',
    'Grainger': 'div[data-testid^="pricing-component-"]',
}

# === GOOGLE SHEETS FUNCTIONS ===
def get_sheets_service():
    creds = service_account.Credentials.from_service_account_file(
        CREDENTIALS_FILE,
        scopes=['https://www.googleapis.com/auth/spreadsheets']
    )
    return build('sheets', 'v4', credentials=creds)

def get_links_with_selectors(service):
    range_name = f"{LINKS_TAB}!C{START_ROW}:E"
    result = service.spreadsheets().values().get(
        spreadsheetId=SPREADSHEET_ID, range=range_name).execute()
    return result.get('values', [])

def get_next_col_letter(service):
    result = service.spreadsheets().values().get(
        spreadsheetId=SPREADSHEET_ID, range=f"{LINKS_TAB}!1:1").execute()
    headers = result.get('values', [[]])[0]
    next_col = len(headers) + 1
    result_col = ""
    while next_col > 0:
        next_col, remainder = divmod(next_col - 1, 26)
        result_col = chr(65 + remainder) + result_col
    return result_col

def write_prices(service, col_letter, prices):
    service.spreadsheets().values().update(
        spreadsheetId=SPREADSHEET_ID,
        range=f"{LINKS_TAB}!{col_letter}{START_ROW}",
        valueInputOption="RAW",
        body={"values": prices}
    ).execute()

def write_date_header(service, col_letter):
    today = datetime.date.today().strftime("Price %-m/%-d")
    service.spreadsheets().values().update(
        spreadsheetId=SPREADSHEET_ID,
        range=f"{LINKS_TAB}!{col_letter}1",
        valueInputOption="RAW",
        body={"values": [[today]]}
    ).execute()

def log_errors(service, errors):
    if not errors:
        return
    today = datetime.datetime.now().isoformat()
    values = [[today, url, selector, error] for url, selector, error in errors]
    service.spreadsheets().values().append(
        spreadsheetId=SPREADSHEET_ID,
        range=f"{ERROR_TAB}!A1",
        valueInputOption="USER_ENTERED",
        insertDataOption="INSERT_ROWS",
        body={"values": values}
    ).execute()

# === SCRAPING HELPERS ===
def extract_price(text):
    matches = re.findall(r"\$\s?\d{1,3}(?:,\d{3})*(?:\.\d{2})", text)
    return matches[0] if matches else None

def guess_vendor_from_url(url):
    host = urlparse(url).netloc.lower()
    if 'harborfreight' in host:
        return 'Harbor Freight'
    if 'menards' in host:
        return 'Menards'
    if 'castercity' in host:
        return 'CasterCity.com'
    if 'mscdirect' in host:
        return 'MSC Direct'
    if 'grainger' in host:
        return 'Grainger'
    return None

async def enhanced_semantic_price_scan(page):
    selector_patterns = [
        '[class*="price"]',
        '[id*="price"]',
        '[class*="amount"]',
        '[itemprop="price"]',
        'meta[property="product:price:amount"]'
    ]
    for selector in selector_patterns:
        try:
            elements = await page.query_selector_all(selector)
            for element in elements:
                try:
                    if "meta" in selector:
                        content = await element.get_attribute("content")
                        price = extract_price(content or "")
                    else:
                        text = await element.inner_text()
                        price = extract_price(text or "")
                    if price:
                        return price
                except Exception:
                    continue
        except Exception:
            continue
    return None

async def fetch_price_from_page(page, url, selector=None):
    try:
        if "mcmaster.com" in url:
            return "Login required – skipping"

        await page.goto(url, timeout=20000)
        await page.wait_for_timeout(3000)

        # Tier 1: Specific selector
        if selector:
            try:
                await page.wait_for_selector(selector, timeout=6000)
                element = await page.query_selector(selector)
                if element:
                    text = await element.inner_text()
                    price = extract_price(text)
                    return price if price else "No price found in selector"
                else:
                    return "Selector not found on page"
            except Exception as sel_error:
                return f"Selector error: {sel_error}"

        # Tier 2: Semantic fallback
        price = await enhanced_semantic_price_scan(page)
        if price:
            return price

        # Tier 3: Raw page content scan
        content = await page.content()
        return extract_price(content) or "No price found in fuzzy scan"

    except PlaywrightTimeoutError:
        return "Timeout"
    except Exception as e:
        return f"Error: {str(e)}"

async def scrape_all(rows):
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=HEADLESS)
        page = await browser.new_page()

        results = []
        errors = []

        for idx, row in enumerate(rows):
            url = row[0].strip() if len(row) > 0 else ""
            manual_selector = row[1].strip() if len(row) > 1 else ""
            vendor_override = row[2].strip() if len(row) > 2 else ""

            if not url:
                results.append([""])
                continue

            selector = None
            if manual_selector:
                selector = manual_selector
            elif vendor_override in VENDOR_SELECTOR_MAP:
                selector = VENDOR_SELECTOR_MAP[vendor_override]
            else:
                guessed = guess_vendor_from_url(url)
                selector = VENDOR_SELECTOR_MAP.get(guessed)

            print(f"Scraping: {url} | Using selector: {selector or 'semantic/fuzzy'}")
            result = await fetch_price_from_page(page, url, selector)

            if result and result.startswith("$"):
                results.append([result])
            else:
                results.append([""])
                errors.append((url, selector or "semantic/fuzzy", result))

        await browser.close()
        return results, errors

# === MAIN ===
def main():
    print("🔁 Starting scraper...")
    service = get_sheets_service()
    links = get_links_with_selectors(service)
    col_letter = get_next_col_letter(service)

    prices, errors = asyncio.run(scrape_all(links))

    write_prices(service, col_letter, prices)
    write_date_header(service, col_letter)
    log_errors(service, errors)
    print("✅ Scraping complete.")

if __name__ == "__main__":
    main()
