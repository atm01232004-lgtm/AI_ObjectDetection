import unittest
import time
import os
import shutil
import sys
from datetime import datetime
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager

# --- CẤU HÌNH ĐƯỜNG DẪN ĐỂ IMPORT MODULE ---
current_dir = os.path.dirname(os.path.abspath(__file__))
# Thêm thư mục cha (AI_OB_01) vào sys.path
sys.path.append(os.path.join(current_dir, '..'))

# Import App, Database và Reporter
from app import app, db, History, UPLOAD_FOLDER

from utils.excel_reporter import ExcelReporter


# --- CẤU HÌNH TEST ---
BASE_URL = "http://127.0.0.1:5000"
TIME_WAIT = 2.0

# Đường dẫn ảnh mẫu và ảnh giả lập
BASE_DIR = os.path.abspath(os.path.join(current_dir, '..'))
SOURCE_IMG_PATH = os.path.join(BASE_DIR, "static", "test_uploads", "ban-phim-van-phong-1.jpg")
TARGET_FILENAME = "Test_Direct_DB.jpg"
TARGET_IMG_PATH = os.path.join(BASE_DIR, "static", "uploads", TARGET_FILENAME)
WEB_IMG_PATH = f"/static/uploads/{TARGET_FILENAME}"


class TestStatisticsDirectDB(unittest.TestCase):
    # 1. Khởi tạo bộ báo cáo Excel
    reporter = ExcelReporter(report_folder="AutoTest_Results", report_title="Statistics_Page_Report")

    @classmethod
    def tearDownClass(cls):
        """Xuất file Excel sau khi chạy xong"""
        cls.reporter.save_report()

    def setUp(self):
        print(f"\n{'=' * 60}")
        print(">>> 🚀 Đang khởi động trình duyệt Chrome...")
        chrome_options = Options()
        # chrome_options.add_argument("--headless")
        self.driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=chrome_options)
        self.driver.maximize_window()

        # Khởi tạo biến lưu thông tin báo cáo
        self.test_steps = ""
        self.test_actual = ""
        self.test_status = "FAIL"  # Mặc định là Fail

        # Chuẩn bị dữ liệu
        self.seed_database()

    def tearDown(self):
        """Dọn dẹp và Ghi log báo cáo"""
        print(">>> 🏁 Kết thúc Test Case.")

        # 1. Xác định trạng thái PASS/FAIL dựa trên kết quả chạy
        # (Lấy lỗi từ unittest nếu có)
        outcome = self._outcome.errors
        error_msg = ""
        for test, exc_info in outcome:
            if exc_info:
                self.test_status = "FAIL"
                error_msg = str(exc_info[1])
                self.test_actual = f"Lỗi: {error_msg}"

        # 2. Ghi vào Excel
        self.reporter.add_result(
            case_id="TC_STATS_01",
            module="Statistics Page",
            test_name="Kiểm tra hiển thị và xóa ảnh (Data Seeding)",
            steps=self.test_steps,
            input_data=f"Image: {TARGET_FILENAME}",
            expected="Hiển thị đúng ảnh, xóa thành công",
            actual=self.test_actual,
            status=self.test_status,
            priority="High",
            remarks=error_msg
        )

        # 3. Đóng trình duyệt
        self.driver.quit()

        # 4. Dọn dẹp file ảnh rác
        if os.path.exists(TARGET_IMG_PATH):
            os.remove(TARGET_IMG_PATH)
            print("   🧹 Đã dọn dẹp file ảnh test.")

    def seed_database(self):
        """Tiêm dữ liệu thẳng vào DB và ổ cứng"""
        print("   [Seeding] Đang tạo dữ liệu giả lập...")
        self.test_steps += "1. Seed Data: Copy ảnh và Insert DB\n"

        if not os.path.exists(SOURCE_IMG_PATH):
            # Nếu không có ảnh mẫu thì tạo ảnh đen tạm để test không bị crash
            import cv2
            import numpy as np
            if not os.path.exists(os.path.dirname(SOURCE_IMG_PATH)):
                os.makedirs(os.path.dirname(SOURCE_IMG_PATH))
            dummy = np.zeros((100, 100, 3), np.uint8)
            cv2.imwrite(SOURCE_IMG_PATH, dummy)

        shutil.copy(SOURCE_IMG_PATH, TARGET_IMG_PATH)

        with app.app_context():
            record = History(
                timestamp=datetime.now().strftime("%d/%m/%Y %H:%M:%S"),
                image_path=WEB_IMG_PATH,
                original_path=WEB_IMG_PATH,
                source="Direct DB Test",
                name=TARGET_FILENAME,
                results_json='[{"name": "Test Object", "qty": 99}]'
            )
            db.session.add(record)
            db.session.commit()
            print(f"   ✅ Đã chèn bản ghi ID: {record.id}")

    def login(self):
        print("   [Login] Đăng nhập nhanh...")
        self.test_steps += "2. Đăng nhập hệ thống\n"
        self.driver.get(f"{BASE_URL}/login")
        time.sleep(1)

        self.driver.find_element(By.CSS_SELECTOR, ".sign-in-container input[name='username']").send_keys("admin")
        self.driver.find_element(By.CSS_SELECTOR, ".sign-in-container input[name='password']").send_keys("123")

        # Dùng JS click để tránh lỗi
        btn = self.driver.find_element(By.CSS_SELECTOR, ".sign-in-container button")
        self.driver.execute_script("arguments[0].click();", btn)
        time.sleep(1)

    # --- TEST CASE ---
    def test_statistics_page(self):
        driver = self.driver

        try:
            self.login()

            # 1. Vào trang Thống kê
            print(">>> [Step 1] Vào trang Thống kê...")
            self.test_steps += "3. Vào trang Thống kê\n"
            driver.get(f"{BASE_URL}/statistics")
            time.sleep(TIME_WAIT)

            # 2. Tìm ảnh trong danh sách
            print(f">>> [Step 2] Tìm kiếm ảnh '{TARGET_FILENAME}'...")
            self.test_steps += "4. Tìm ảnh trong danh sách\n"

            items = driver.find_elements(By.CSS_SELECTOR, "#history-list li")
            found = False
            target_item = None

            for item in items:
                if TARGET_FILENAME in item.text:
                    found = True
                    target_item = item
                    break

            if not found:
                raise Exception("Không thấy dữ liệu vừa chèn trong danh sách!")

            print("   ✅ Đã thấy bản ghi.")

            # 3. Xem chi tiết
            self.test_steps += "5. Click xem chi tiết\n"
            target_item.click()
            time.sleep(1)

            # Kiểm tra thông tin
            d_source = driver.find_element(By.ID, "d-source").text
            if d_source != "Direct DB Test":
                raise Exception("Thông tin chi tiết hiển thị sai nguồn")

            print("   ✅ Thông tin chi tiết hiển thị đúng.")

            # 4. Xóa ảnh
            print(">>> [Step 3] Thử xóa bản ghi này...")
            self.test_steps += "6. Bấm nút Xóa và xác nhận\n"

            delete_btn = driver.find_element(By.ID, "btn-delete")
            delete_btn.click()
            time.sleep(0.5)

            driver.switch_to.alert.accept()  # OK Confirm
            time.sleep(1)
            driver.switch_to.alert.accept()  # OK Success
            print("   ✅ Đã thực hiện thao tác xóa.")

            self.test_status = "PASS"
            self.test_actual = "Dữ liệu hiển thị đúng, xóa thành công"

        except Exception as e:
            self.test_status = "FAIL"
            self.test_actual = f"Lỗi: {e}"
            raise e  # Ném lỗi ra để unittest ghi nhận là Fail


if __name__ == "__main__":
    unittest.main()