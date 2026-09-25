import requests
from bs4 import BeautifulSoup
import pandas as pd
import time

BASE_URL = "https://gochek.vn/collections/all"
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
}

all_products = []
page = 1

while True:
    url = f"{BASE_URL}?page={page}"
    print(f"Đang cào dữ liệu trang {page}...")
    
    response = requests.get(url, headers=HEADERS)
    if response.status_code != 200:
        print(f"Dừng lại do lỗi HTTP {response.status_code}")
        break

    soup = BeautifulSoup(response.text, "html.parser")
    
    # Tìm các khối sản phẩm (thường nằm trong thẻ có class chứa 'product' hoặc 'pro-item')
    items = soup.select(".product-item, .pro-item, .product-block, div[data-product-id]")
    
    # Nếu không tìm thấy bằng class trên, tìm theo selector thẻ bọc chung
    if not items:
        items = soup.find_all("div", class_=lambda c: c and "product" in c.lower())

    # Nếu trang không còn sản phẩm nào -> Đã cào hết toàn bộ website
    if not items:
        print("Đã hết trang dữ liệu!")
        break

    count_page = 0
    for item in items:
        # 1. Tên sản phẩm
        title_tag = item.select_one(".product-title, .pro-name, h3, h2")
        title = title_tag.get_text(strip=True) if title_tag else None

        # 2. Giá sản phẩm
        price_tag = item.select_one(".product-price, .pro-price, .current-price, .price")
        price = price_tag.get_text(strip=True) if price_tag else "Liên hệ"

        # 3. Đường link chi tiết sản phẩm
        link_tag = item.select_one("a[href]")
        link = "https://gochek.vn" + link_tag["href"] if link_tag and link_tag["href"].startswith("/") else (link_tag["href"] if link_tag else None)

        if title and not any(p["Tên sản phẩm"] == title for p in all_products):
            all_products.append({
                "Tên sản phẩm": title,
                "Giá": price,
                "Link sản phẩm": link
            })
            count_page += 1

    if count_page == 0:
        # Nếu trang vẫn trả về thẻ nhưng không bóc được sản phẩm mới nào thì dừng
        break

    page += 1
    time.sleep(1) # Nghỉ 1 giây để không làm quá tải máy chủ website

# Lưu toàn bộ dữ liệu cào được thành file Excel / CSV
df = pd.DataFrame(all_products)
df.to_csv("gochek_products.csv", index=False, encoding="utf-8-sig")
df.to_excel("gochek_products.xlsx", index=False)

print(f"\n Hoàn tất! Thu thập được tổng cộng {len(all_products)} sản phẩm.")
print("Đã lưu kết quả vào file 'gochek_products.xlsx' và 'gochek_products.csv'.")