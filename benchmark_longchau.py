import time
import os
import psutil
import requests
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from playwright.sync_api import sync_playwright

# URL danh mục thuốc / thực phẩm chức năng trên Long Châu
TARGET_URL = "https://nhathuoclongchau.com.vn/thuc-pham-chuc-nang"

def get_memory_usage():
    """Hàm lấy lượng RAM hiện tại (tính bằng MB)"""
    process = psutil.Process(os.getpid())
    return process.memory_info().rss / (1024 * 1024)

# ==========================================
# 1. CÔNG CỤ 1: REQUESTS + BEAUTIFULSOUP
# ==========================================
def scrape_with_bs4(url):
    headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}
    resp = requests.get(url, headers=headers)
    soup = BeautifulSoup(resp.text, "html.parser")
    
    # Tìm tên sản phẩm (thay đổi selector class cho phù hợp cấu trúc HTML)
    products = soup.find_all("h3") # Ví dụ tiêu đề sản phẩm
    titles = [p.get_text(strip=True) for p in products]
    return len(titles)

# ==========================================
# 2. CÔNG CỤ 2: SELENIUM (Headless)
# ==========================================
def scrape_with_selenium(url):
    options = Options()
    options.add_argument("--headless=new") # Chạy ngầm không bật cửa sổ
    options.add_argument("--disable-gpu")
    options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64)")
    
    driver = webdriver.Chrome(options=options)
    driver.get(url)
    
    # Thao tác cuộn trang để kích hoạt tải dữ liệu (cho RQ2)
    driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
    time.sleep(2)
    
    products = driver.find_elements("tag name", "h3")
    count = len(products)
    driver.quit()
    return count

# ==========================================
# 3. CÔNG CỤ 3: PLAYWRIGHT (Headless)
# ==========================================
def scrape_with_playwright(url):
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        page.goto(url)
        
        # Thao tác cuộn trang (cho RQ2)
        page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
        page.wait_for_timeout(2000)
        
        products = page.query_selector_all("h3")
        count = len(products)
        browser.close()
        return count

# ==========================================
# HÀM ĐO VÀ SO SÁNH (BENCHMARK)
# ==========================================
def run_benchmark(tool_name, tool_func, url):
    print(f"\n--- Đang chạy thử nghiệm với: {tool_name} ---")
    mem_before = get_memory_usage()
    t_start = time.time()
    
    try:
        items_count = tool_func(url)
    except Exception as e:
        print(f"Lỗi khi chạy {tool_name}: {e}")
        return
        
    t_end = time.time()
    mem_after = get_memory_usage()
    
    exec_time = round(t_end - t_start, 2)
    mem_used = round(mem_after - mem_before, 2)
    
    print(f"Số lượng sản phẩm lấy được: {items_count}")
    print(f"Thời gian thực thi (RQ1): {exec_time} giây")
    print(f"Lượng RAM tiêu tốn (RQ1): {mem_used} MB")

if __name__ == "__main__":
    # Chạy lần lượt để đo đạc thông số
    run_benchmark("Requests + BeautifulSoup", scrape_with_bs4, TARGET_URL)
    run_benchmark("Selenium", scrape_with_selenium, TARGET_URL)
    run_benchmark("Playwright", scrape_with_playwright, TARGET_URL)