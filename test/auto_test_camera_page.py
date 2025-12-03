import unittest
import time
import sys
import os
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager

# --- CẤU HÌNH ĐƯỜNG DẪN (QUAN TRỌNG) ---
# 1. Lấy đường dẫn thư mục chứa file này (thư mục 'test')
current_dir = os.path.dirname(os.path.abspath(__file__))

# 2. Thêm thư mục 'test' vào hệ thống để Python tìm thấy 'utils'
sys.path.append(current_dir)

# 3. Thêm thư mục gốc dự án (AI_OB_01) để Python tìm thấy 'app.py' nếu cần
sys.path.append(os.path.join(current_dir, '..'))

# --- SỬA LỖI IMPORT TẠI ĐÂY ---
# Thay vì "from test.utils...", hãy bỏ chữ "test." đi
# Vì ta đang đứng trong thư mục 'test' rồi, nên gọi thẳng 'utils' là được.
from utils.excel_reporter import ExcelReporter

# --- CẤU HÌNH ---
BASE_URL = "http://127.0.0.1:5000"
TIME_WAIT = 2.0

class TestCameraPage(unittest.TestCase):
    # Khởi tạo bộ báo cáo
    reporter = ExcelReporter(report_folder="AutoTest_Results", report_title="Camera_Test_Report")

    @classmethod
    def tearDownClass(cls):
        """Xuất file Excel sau khi chạy xong tất cả"""
        cls.reporter.save_report()

    def setUp(self):
        print(f"\n{'=' * 60}")
        print(">>> 🚀 Đang khởi động trình duyệt Chrome...")
        chrome_options = Options()
        self.driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=chrome_options)
        self.driver.maximize_window()

    def tearDown(self):
        print(">>> 🏁 Đóng trình duyệt.")
        self.driver.quit()

    def login(self):
        """Hàm đăng nhập nhanh"""
        self.driver.get(f"{BASE_URL}/login")
        time.sleep(1)
        self.driver.find_element(By.CSS_SELECTOR, ".sign-in-container input[name='username']").send_keys("admin")
        self.driver.find_element(By.CSS_SELECTOR, ".sign-in-container input[name='password']").send_keys("123")
        btn = self.driver.find_element(By.CSS_SELECTOR, ".sign-in-container button")
        self.driver.execute_script("arguments[0].click();", btn)
        time.sleep(2)

    # --- TEST CASE CHÍNH ---
    def test_camera_page_features(self):
        driver = self.driver
        test_id = "TC_CAM_01"
        module = "Camera Page"
        name = "Kiểm tra chức năng trang Camera"

        steps = ""
        input_data = ""
        actual_result = ""
        status = "FAIL"  # Mặc định là Fail

        try:
            # BƯỚC 1: ĐĂNG NHẬP & VÀO CAMERA
            steps += "1. Đăng nhập và vào trang Camera\n"
            self.login()
            driver.find_element(By.ID, "nav-cam-icon").click()
            time.sleep(TIME_WAIT)

            if "/camera" not in driver.current_url:
                raise Exception("Không vào được trang Camera")

            # BƯỚC 2: KIỂM TRA VIDEO & UI
            steps += "2. Kiểm tra Video, Đồng hồ, Thông tin\n"
            video = driver.find_element(By.ID, "video")
            overlay = driver.find_element(By.ID, "overlay-canvas")
            clock = driver.find_element(By.ID, "clock")
            info_area = driver.find_element(By.CLASS_NAME, "info-table-container")

            if not (video.size['width'] > 0 and overlay.is_displayed()):
                raise Exception("Video không hiển thị")

            if clock.text == "--:--":
                raise Exception("Đồng hồ không chạy")

            if "Khu Vực A" not in info_area.text:
                raise Exception("Sai thông tin phòng")

            # BƯỚC 3: TEST CÀI ĐẶT (MODAL)
            steps += "3. Mở Modal Cài đặt\n"
            driver.find_element(By.CSS_SELECTOR, "button[title='Cài đặt Giám sát']").click()
            time.sleep(1)

            # Thêm mục tiêu
            steps += "4. Thêm mục tiêu 'test_mouse'\n"
            test_obj = "test_mouse"
            input_data = f"Obj: {test_obj}, Qty: 5"

            driver.find_element(By.ID, "set-name").send_keys(test_obj)
            driver.find_element(By.ID, "set-qty").send_keys("5")
            driver.find_element(By.CSS_SELECTOR, ".btn-add").click()
            time.sleep(1)

            # Kiểm tra bảng
            table_body = driver.find_element(By.ID, "target-list-body").text
            if test_obj not in table_body:
                raise Exception("Thêm mục tiêu thất bại")

            # Xóa mục tiêu
            steps += "5. Xóa mục tiêu vừa tạo\n"
            del_btns = driver.find_elements(By.CSS_SELECTOR, ".btn-del-target")
            if del_btns:
                del_btns[-1].click()
                time.sleep(1)

            # Đóng Modal
            driver.find_element(By.CSS_SELECTOR, ".modal-header .btn-close").click()
            time.sleep(1)

            # --- KẾT THÚC THÀNH CÔNG ---
            status = "PASS"
            actual_result = "Camera chạy tốt, Modal thêm xóa OK"
            print("✅ Test Camera thành công!")

        except Exception as e:
            status = "FAIL"
            actual_result = f"Lỗi: {str(e)}"
            print(f"❌ Test thất bại: {e}")

        finally:
            # Ghi vào báo cáo Excel
            self.reporter.add_result(
                case_id=test_id,
                module=module,
                test_name=name,
                steps=steps,
                input_data=input_data,
                expected="Camera hiển thị, thêm xóa mục tiêu thành công",
                actual=actual_result,
                status=status,
                priority="High"
            )


if __name__ == "__main__":
    unittest.main()
