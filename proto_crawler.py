""" 
Dev environment:
Python 3.13.7
Libraries: csv, json, re

Before running:
pip install playwright
playwright install firefox # or chromium

atau jika menggunakan virtualenv:
virtualenv proto_crawler
cd proto_crawler
source bin/activate
python -m pip install playwright
"""

from playwright.sync_api import sync_playwright, TimeoutError as PlaywrightTimeout
import csv, json, re

def crawl_product(url):
    """
    Crawling Tokopedia product page
    Return product data as a dictionary

    Mandatory information: product_name, category, price
    Extra information: 
    rating: average rating of chosen product, help prioritize product
    rating_count: number of customer who gave rating, indicate customer satisfaction
    shop_name: store/seller name, useful for seller analysis

    Di sini kita menggunakan page.locator dari playwright untuk membuka page seperti real browser 
    kemudian cari berdasarkan selector yang dipilih. Sudah dicoba menggunakan requests.get biasa 
    tapi tidak menghasilkan apapun. Untuk pilihan browser bisa menggunakan firefox atau chromium.
    Source: https://playwright.dev/python/docs/api/class-page
    """
    with sync_playwright() as p:
        browser = p.firefox.launch(headless=True) # launch browser in headless mode
        page = browser.new_page()
        print(f"[INFO] Crawling: {url}")
        page.goto(url, timeout=90000)
        """ next bisa ditambahkan failsafe/retry 3x jika terjadi timeout 90 detik """
        page_html = page.content() # simpan html-nya untuk failsafe

        def safe_text(selector):
            """
            function ini digunakan untuk handle error dan sebagai default
            value ("N/A") ketika page.locator gagal menemukan selector/textnya
            """
            try:
                el = page.locator(selector).first
                text = el.text_content()
                return text.strip() if text else "N/A"
            except:
                return "N/A"

        """
        extract information
        """
        product_name = safe_text("h1")
        category = safe_text("a[href*='/p/']")
        price_ori = safe_text("div[data-testid='lblPDPDetailProductPrice']")
        price = "".join(x for x in price_ori if x.isdigit()) # get numeric only price
        rating = safe_text("[data-testid='lblPDPDetailProductRatingNumber']")
        rating_count_ori = safe_text("[data-testid='lblPDPDetailProductRatingCounter']")
        rating_count = "".join(x for x in rating_count_ori if x.isdigit()) # get numeric only

        """ 
        khusus untuk nama toko kita gunakan regex untuk mencari "shopName" 
        di halaman html-nya karena masih belum ketemu selector yang sesuai 
        """
        shop_name = None
        match = re.search(r'"shopName"\s*:\s*"([^"]+)"', page_html)
        if match:
            shop_name = match.group(1)

        """ 
        print di console sebagai alat bantu debuging
        """
        print(f"[INFO] Product name: {product_name}")
        print(f"[INFO] Category: {category}")
        print(f"[INFO] Price: {price}")
        print(f"[INFO] Shop name: {shop_name}")
        print(f"[INFO] Rating: {rating}")
        print(f"[INFO] Rating Count: {rating_count}")

        # bentuk dictionary
        product_dict = {
            "product_name": product_name if product_name else "N/A",
            "category": category if category else "N/A",
            "price": price if price else "N/A",
            "shop_name": shop_name if shop_name else "N/A",
            "rating": rating if rating else "N/A",
            "rating_count": rating_count if rating_count else "N/A",
        }

        # close browser
        browser.close()
        
        return product_dict


def save_result(product, csv_filename="product.csv", json_filename="product.json"):
    """ save data into csv & json file """
    if not product:
        print("[WARN] No product data to process.")
        return
    fieldname = product[0].keys()
    
    with open(csv_filename, "w", newline="", encoding="utf-8") as f:
        """ 
        Tulis ke csv, hanya gunakan tanda quote ketika diperlukan, 
        misalnya ada karakter delimiter (',') di dalam string. 
        Sangat membantu untuk menghasilkan data yang bersih.
        """
        writer = csv.DictWriter(f, quotechar='"', quoting=csv.QUOTE_MINIMAL, fieldnames=fieldname)
        writer.writeheader()
        writer.writerows(product)

    with open(json_filename, "w", encoding="utf-8") as f:
        json.dump(product, f, indent=2, ensure_ascii=False)
    
    print(f"[INFO] Saved CSV → {csv_filename}")
    print(f"[INFO] Saved JSON → {json_filename}")


if __name__ == "__main__":
    """ Masukan url product yang mau di-crawl """
    product_url = [
        #"https://www.tokopedia.com/tokosusumomnkids/grandville-abon-sapi-ayam-100-gr-grandville-beef-chicken-floss-100-gr-ayam-original",
        #"https://www.tokopedia.com/seiko-id/jam-tangan-pria-seiko-5-sports-srpd51k1-automatic-blue-dial-srpd51",
        #"https://www.tokopedia.com/bililagi/cmf-phone-1-5g-8-256gb-global-rom-mediatek-dimensity-7300-light-green-fabbb",
    ]

    all_product = []
    for url in product_url:
        data = crawl_product(url)
        """ build list of dictionary """
        if data:
            all_product.append(data)

    save_result(all_product)


"""
Future Enhancements:
- Asynchronous Crawling for speed
- Database storage for incremental updates
- Automatic product discovery via Tokopedia search URL.
"""