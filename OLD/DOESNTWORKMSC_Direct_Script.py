from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
import time
import re

BRIGHTDATA_USER = 'caster_scraper-zone-us'  # Replace if needed
BRIGHTDATA_PASS = 'Welc0me??PL??'      # From your zone
BRIGHTDATA_HOST = 'brd.superproxy.io'
BRIGHTDATA_PORT = 22225

def extract_price(text):
    matches = re.findall(r'\$?\d{1,5}[\.,]\d{2}', text)
    return matches[0] if matches else None

def scrape_msc_with_brightdata():
    proxy = f"http://{BRIGHTDATA_USER}:{BRIGHTDATA_PASS}@{BRIGHTDATA_HOST}:{BRIGHTDATA_PORT}"

    chrome_options = Options()
    chrome_options.add_argument("--headless=new")
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument(f'--proxy-server={proxy}')
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--window-size=1920,1080")

    driver = webdriver.Chrome(options=chrome_options)

    try:
        url = "https://www.mscdirect.com/product/details/66019001"
        driver.get(url)
        time.sleep(10)  # Let JS render
        text = driver.page_source
        match = re.search(r'id="webPriceId".*?>\s*\$?([\d,]+\.\d{2})', text)
        if match:
            price = f"${match.group(1)}"
            print(f"[BrightData MSC Price] {price}")
            return price
        else:
            print("Price not found via BrightData rendering.")
    finally:
        driver.quit()

scrape_msc_with_brightdata()
