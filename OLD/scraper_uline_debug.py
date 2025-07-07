import asyncio
from playwright.async_api import async_playwright
from bs4 import BeautifulSoup
import re

# Target URL and selector
URL = "https://www.uline.com/Product/Detail/H-3615/Platform-Trucks/Pneumatic-Caster-for-Platform-Trucks-Swivel-8-x-2-1-2?gQT=1"
CSS_SELECTOR = "td.PriceCellChartcopyItemW10H18"

def extract_price(text):
    match = re.search(r'\$?\d{1,5}[\.,]?\d{0,2}', text)
    return match.group() if match else None

async def main():
    print(f"Scraping ULINE page: {URL}")
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False)  # Set headless=True to hide browser
        page = await browser.new_page()
        try:
            await page.goto(URL, timeout=60000)
            await page.wait_for_selector(CSS_SELECTOR, timeout=10000)
            element = await page.query_selector(CSS_SELECTOR)
            inner_html = await element.inner_html()
            print(f"Raw HTML: {inner_html}")

            # Use BeautifulSoup to extract the price
            soup = BeautifulSoup(inner_html, "html.parser")
            text = soup.get_text(strip=True)
            price = extract_price(text)

            print("✅ Extracted price:", price if price else "❌ No price found")

        except Exception as e:
            print("❌ Error:", str(e))
        finally:
            await browser.close()

if __name__ == "__main__":
    asyncio.run(main())
