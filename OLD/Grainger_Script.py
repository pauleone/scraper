import requests

sku = "38ER63"
expected_price = "36.10"
scraperapi_key = "6453db25bf5f6850acc588933f86e467"
url = f"https://www.grainger.com/product/info?productArray={sku}"
proxy_url = f"http://api.scraperapi.com?api_key={scraperapi_key}&url={url}"

headers = {
    "User-Agent": "Mozilla/5.0",
    "Accept": "application/json",
    "Referer": "https://www.grainger.com/",
}

response = requests.get(proxy_url, headers=headers)
data = response.json()

actual_price = data[sku]["price"]["sell"]["price"]
formatted = data[sku]["price"]["sell"]["formattedPrice"].strip("$")

if formatted != expected_price:
    print(f"[!] Price changed: was ${expected_price}, now ${formatted}")
    # trigger deeper scrape or log change
else:
    print(f"[✓] Price still ${expected_price}")
