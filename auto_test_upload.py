import unittest
import time
import os
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager

# --- CẤU HÌNH ---
BASE_URL = "http://127.0.0.1:5000"
TIME_WAIT = 4.0  # Thời gian chờ mỗi bước

# 1. Lấy đường dẫn gốc
BASE_DIR = os.path.abspath(os.path.dirname(__file__))
IMG_FOLDER = os.path.join(BASE_DIR, "static", "test_uploads")

# 2. Danh sách các ảnh muốn test (Tên file phải có thật trong thư mục)
IMAGE_LIST = [
    "ban-phim-van-phong-1.jpg",
    "mau-ban-ghe-van-phong-hien-dai-1.jpg",
    "Untitled.png",
    "Man-hinh-van-phong-1.jpg",
    "152.png"
    # Bạn có thể thêm ảnh thứ 3, 4 vào đây...
]


class TestBatchUpload(unittest.TestCase):

    def setUp(self):
        print(f"\n{'=' * 60}")
        print(">>> 🚀 Đang khởi động trình duyệt Chrome...")
        chrome_options = Options()
        self.driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=chrome_options)
        self.driver.maximize_window()

    def tearDown(self):
        print(">>> 🏁 Hoàn tất bộ test. Đóng trình duyệt sau 5 giây.")
        time.sleep(5)
        self.driver.quit()

    def login_helper(self):
        driver = self.driver
        driver.get(f"{BASE_URL}/login")
        print("   ...Đang đăng nhập...")
        driver.find_element(By.CSS_SELECTOR, ".sign-in-container input[name='username']").send_keys("admin")
        driver.find_element(By.CSS_SELECTOR, ".sign-in-container input[name='password']").send_keys("123")
        driver.find_element(By.CSS_SELECTOR, ".sign-in-container button").click()
        time.sleep(2)

        # --- TEST CASE CHÍNH: CHẠY VÒNG LẶP QUA CÁC ẢNH ---

    def test_batch_upload(self):
        driver = self.driver

        # Bước 1: Đăng nhập trước
        self.login_helper()

        actual_title = driver.title
        self.assertTrue("AI" in actual_title, "Lỗi: Chưa vào được trang chủ")
        print("   ✅ Đăng nhập thành công. Bắt đầu test danh sách ảnh.\n")

        # Bước 2: Vòng lặp qua từng ảnh
        for index, img_name in enumerate(IMAGE_LIST, 1):
            print(f"--- 📸 ĐANG TEST ẢNH {index}/{len(IMAGE_LIST)}: {img_name} ---")

            # Tạo đường dẫn tuyệt đối
            full_path = os.path.join(IMG_FOLDER, img_name)

            # Kiểm tra file có tồn tại không
            if not os.path.exists(full_path):
                print(f"   ❌ LỖI: Không tìm thấy file {img_name}, bỏ qua...")
                continue

            # A. Upload ảnh
            print(f"   [1] Chọn file: {img_name}")
            file_input = driver.find_element(By.ID, "fileElem")
            file_input.send_keys(full_path)
            time.sleep(TIME_WAIT)

            # B. Bấm Nhận dạng
            print("   [2] Bấm nút 'Nhận dạng'...")
            predict_btn = driver.find_element(By.CSS_SELECTOR, "button.btn-primary")
            predict_btn.click()

            print("   ⏳ Chờ AI xử lý...")
            time.sleep(6)  # Chờ AI trả kết quả

            # C. Kiểm tra kết quả
            output_text = driver.find_element(By.ID, "output-text").text
            print(f"   ℹ️ Kết quả nhận được: {output_text.replace(chr(10), ', ')}")  # chr(10) là xuống dòng

            # D. QUAN TRỌNG: BẤM NÚT X ĐỂ XÓA ẢNH CŨ
            print("   [3] Bấm nút X để xóa ảnh, chuẩn bị cho ảnh tiếp theo...")

            # Tìm nút X (class .btn-close-img mà ta đã thêm ở bài trước)
            try:
                close_btn = driver.find_element(By.CSS_SELECTOR, ".btn-close-img")
                close_btn.click()
                print("   ✅ Đã xóa ảnh cũ.")
            except:
                print("   ⚠️ Cảnh báo: Không tìm thấy nút X (Có thể ảnh chưa lên?)")

            time.sleep(TIME_WAIT)  # Nghỉ một chút trước khi sang ảnh tiếp theo
            print("-" * 40 + "\n")

        print("✅✅✅ ĐÃ TEST XONG TOÀN BỘ DANH SÁCH ẢNH!")


if __name__ == "__main__":
    unittest.main()