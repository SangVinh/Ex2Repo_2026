import requests
from bs4 import BeautifulSoup
import pandas as pd
import time

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
}

def get_all_courses():
    """Hàm lấy tất cả các khóa học trên trang titv.vn"""
    courses = []
    page = 1
    
    while True:
        url = f"https://titv.vn/khoa-hoc/page/{page}/" if page > 1 else "https://titv.vn/khoa-hoc/"
        print(f"Đang tìm khóa học ở trang {page}: {url}")
        
        try:
            resp = requests.get(url, headers=HEADERS, timeout=15)
        except Exception as e:
            print(f"Lỗi kết nối trang {page}: {e}")
            break
            
        if resp.status_code != 200:
            print(f"Dừng tìm khóa học (Mã phản hồi: {resp.status_code})")
            break
            
        soup = BeautifulSoup(resp.text, "html.parser")
        
        # Tìm các thẻ chứa link khóa học (thường nằm trong thẻ h2, h3 hoặc class course-title)
        links = soup.select(".course-title a, .entry-title a, article a[href*='/khoa-hoc/']")
        
        found_in_page = 0
        for a in links:
            title = a.get_text(strip=True)
            href = a.get("href")
            
            # Lọc bỏ các liên kết trùng hoặc liên kết trang chủ / phân trang
            if title and href and href.startswith("https://titv.vn/khoa-hoc/") and href != "https://titv.vn/khoa-hoc/":
                if not any(c["url"] == href for c in courses):
                    courses.append({"title": title, "url": href})
                    found_in_page += 1
                    
        if found_in_page == 0:
            break
            
        page += 1
        time.sleep(1)
        
    return courses

def get_lessons_of_course(course_url):
    """Hàm truy cập vào từng khóa học để bóc toàn bộ bài học"""
    lessons = []
    try:
        resp = requests.get(course_url, headers=HEADERS, timeout=15)
        if resp.status_code != 200:
            return lessons
            
        soup = BeautifulSoup(resp.text, "html.parser")
        
        # Tìm danh sách bài học theo các selector LMS phổ biến (LearnPress, MasterStudy...)
        lesson_elements = soup.select(
            ".course-item-title, .section-item-title, .curriculum-item, .lesson-title, "
            ".learn-press-course-curriculum a, .course-curriculum a, li.section-item a"
        )
        
        for idx, el in enumerate(lesson_elements, start=1):
            name = el.get_text(strip=True)
            href = el.get("href", "")
            if name:
                lessons.append({
                    "STT": idx,
                    "Tên bài học": name,
                    "Link bài học": href if href.startswith("http") else ""
                })
                
    except Exception as e:
        print(f"Lỗi khi cào khóa học {course_url}: {e}")
        
    return lessons

def main():
    print("=== BẮT ĐẦU THU THẬP DỮ LIỆU TITV.VN ===")
    courses = get_all_courses()
    print(f"\n=> Tìm thấy tổng cộng {len(courses)} khóa học.\n")
    
    full_data = []
    
    for i, c in enumerate(courses, start=1):
        print(f"[{i}/{len(courses)}] Đang lấy bài học của: {c['title']}")
        lessons = get_lessons_of_course(c["url"])
        
        if not lessons:
            # Trường hợp khóa học không chia danh sách chương mục chi tiết
            full_data.append({
                "Tên khóa học": c["title"],
                "Link khóa học": c["url"],
                "STT bài học": "",
                "Tên bài học": "Không có danh sách bài học chi tiết hoặc cần đăng nhập",
                "Link bài học": ""
            })
        else:
            for les in lessons:
                full_data.append({
                    "Tên khóa học": c["title"],
                    "Link khóa học": c["url"],
                    "STT bài học": les["STT"],
                    "Tên bài học": les["Tên bài học"],
                    "Link bài học": les["Link bài học"]
                })
        
        time.sleep(1) # Tránh gửi request quá nhanh
        
    # Xuất toàn bộ kết quả ra file
    df = pd.DataFrame(full_data)
    df.to_excel("titv_courses_and_lessons.xlsx", index=False)
    df.to_csv("titv_courses_and_lessons.csv", index=False, encoding="utf-8-sig")
    
    print("\n Hoàn tất! Dữ liệu đã được lưu vào:")
    print(" - titv_courses_and_lessons.xlsx")
    print(" - titv_courses_and_lessons.csv")

if __name__ == "__main__":
    main()