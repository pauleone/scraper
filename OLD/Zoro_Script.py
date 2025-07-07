# Zoro_Script.py
import asyncio
from playwright.async_api import async_playwright
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

TARGET_URL = "https://www.zoro.com/marathon-industries-marathon-flat-free-8-swivel-caster-00316/i/G108622439/"
PRICE_SELECTOR = "span[itemprop='price']"

async def scrape_zoro_price():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64)")
        page = await context.new_page()

        logger.info(f"Visiting: {TARGET_URL}")
        try:
            await page.goto(TARGET_URL, timeout=20000)
            await page.wait_for_selector(PRICE_SELECTOR, timeout=10000)
            price_element = await page.query_selector(PRICE_SELECTOR)
            price = await price_element.inner_text() if price_element else None

            if price:
                print(f"✅ Zoro price found: {price}")
            else:
                print("❌ Price element not found.")
        except Exception as e:
            print(f"❌ Error during scraping: {e}")
        finally:
            await browser.close()

if __name__ == "__main__":
    asyncio.run(scrape_zoro_price())