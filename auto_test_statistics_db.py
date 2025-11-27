import unittest
import time
import os
import shutil  # Thư viện để copy file
from datetime import datetime
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager

# Import Database từ app của bạn
from app import app, db, History, UPLOAD_FOLDER

# --- CẤU HÌNH ---
BASE_URL = "http://127.0.0.1:5000"
TIME_WAIT = 2.0

# Đường dẫn ảnh gốc (Ảnh mẫu để test)
BASE_DIR = os.path.abspath(os.path.dirname(__file__))
SOURCE_IMG_PATH = os.path.join(BASE_DIR, "static", "test_uploads", "ban-phim-van-phong-1.jpg")

# Tên file giả lập sẽ lưu vào server
TARGET_FILENAME = "Test_Direct_DB.jpg"
TARGET_IMG_PATH = os.path.join(BASE_DIR, "static", "uploads", TARGET_FILENAME)  # Đường dẫn vật lý
WEB_IMG_PATH = f"/static/uploads/{TARGET_FILENAME}"  # Đường dẫn web


class TestStatisticsDirectDB(unittest.TestCase):

    def setUp(self):
        print(f"\n{'=' * 60}")
        print(">>> 🚀 Đang khởi động trình duyệt Chrome...")
        chrome_options = Options()
        self.driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=chrome_options)
        self.driver.maximize_window()
        self.seed_database()

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


    def tearDown(self):
        print(">>> 🏁 Test xong. Đóng trình duyệt sau 3 giây.")
        time.sleep(3)
        self.driver.quit()

        # Dọn dẹp: Xóa file ảnh giả sau khi test
        if os.path.exists(TARGET_IMG_PATH):
            os.remove(TARGET_IMG_PATH)
            print("   🧹 Đã dọn dẹp file ảnh test.")

    def seed_database(self):
        self.login_helper()
        """Hàm này tiêm dữ liệu thẳng vào DB và ổ cứng mà không cần Upload"""
        print("   [Seeding] Đang tạo dữ liệu giả lập...")

        # A. Copy file ảnh vào thư mục uploads (Giả lập việc server đã lưu ảnh)
        if not os.path.exists(SOURCE_IMG_PATH):
            raise FileNotFoundError(f"Không thấy ảnh mẫu tại: {SOURCE_IMG_PATH}")

        shutil.copy(SOURCE_IMG_PATH, TARGET_IMG_PATH)
        print("   ✅ Đã copy file ảnh vào thư mục uploads.")

        # B. Chèn bản ghi vào Database (SQLite)
        # Cần dùng app_context() để truy cập DB
        with app.app_context():
            # Tạo bản ghi mới
            record = History(
                timestamp=datetime.now().strftime("%d/%m/%Y %H:%M:%S"),
                image_path=WEB_IMG_PATH,  # Đường dẫn web tới ảnh vừa copy
                original_path=WEB_IMG_PATH,  # Dùng chung ảnh này làm ảnh gốc luôn
                source="Direct DB Test",
                name=TARGET_FILENAME,
                results_json='[{"name": "Test Object", "qty": 99}]'  # Dữ liệu giả
            )
            db.session.add(record)
            db.session.commit()

            # Lưu lại ID để tí nữa kiểm tra xóa
            self.created_id = record.id
            print(f"   ✅ Đã chèn bản ghi vào DB với ID: {self.created_id}")

    def login(self):
        print("   [Login] Đăng nhập nhanh...")
        self.driver.get(f"{BASE_URL}/login")

        time.sleep(2)

        self.driver.find_element(By.CSS_SELECTOR, ".sign-in-container input[name='username']").send_keys("admin")
        self.driver.find_element(By.CSS_SELECTOR, ".sign-in-container input[name='password']").send_keys("123")
        self.driver.find_element(By.CSS_SELECTOR, ".sign-in-container button").click()

        time.sleep(1)

    # --- TEST CASE ---
    def test_statistics_page(self):
        driver = self.driver

        # 1. Vào thẳng trang Thống kê (Không cần upload nữa!)
        print(">>> [Step 1] Vào trang Thống kê...")
        driver.get(f"{BASE_URL}/statistics")
        time.sleep(TIME_WAIT)

        # 2. Kiểm tra dữ liệu vừa tiêm vào có hiện lên không
        print(f">>> [Step 2] Tìm kiếm ảnh '{TARGET_FILENAME}' trong danh sách...")

        # Tìm danh sách li
        items = driver.find_elements(By.CSS_SELECTOR, "#history-list li")
        found = False
        target_item = None

        for item in items:
            if TARGET_FILENAME in item.text:
                found = True
                target_item = item
                break

        self.assertTrue(found, "Lỗi: Không thấy dữ liệu vừa chèn trong danh sách!")
        print("   ✅ Đã thấy bản ghi trong danh sách.")

        # 3. Click vào để xem chi tiết
        target_item.click()
        time.sleep(1)

        # Kiểm tra thông tin chi tiết
        d_source = driver.find_element(By.ID, "d-source").text
        self.assertEqual(d_source, "Direct DB Test")
        print("   ✅ Thông tin chi tiết hiển thị đúng.")

        # 4. Test chức năng Xóa (Để dọn sạch DB)
        print(">>> [Step 3] Thử xóa bản ghi này...")
        delete_btn = driver.find_element(By.ID, "btn-delete")
        delete_btn.click()
        time.sleep(0.5)

        driver.switch_to.alert.accept()  # OK Confirm
        time.sleep(1)
        driver.switch_to.alert.accept()  # OK Success

        print("   ✅ Đã thực hiện thao tác xóa.")
        time.sleep(1)


if __name__ == "__main__":
    unittest.main()