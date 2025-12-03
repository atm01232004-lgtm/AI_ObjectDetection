import unittest
import time
import sys
import os
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager

# --- CẤU HÌNH IMPORT ---
current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.append(os.path.join(current_dir, '..'))

from utils.excel_reporter import ExcelReporter

BASE_URL = "http://127.0.0.1:5000"


class TestCompatibility(unittest.TestCase):
    # Khởi tạo Reporter
    reporter = ExcelReporter(report_folder="AutoTest_Results", report_title="Compatibility_Test_Report")

    @classmethod
    def tearDownClass(cls):
        cls.reporter.save_report()

    def setUp(self):
        # Khởi tạo biến báo cáo
        self.test_steps = ""
        self.test_input = ""
        self.test_expected = "Giao diện hiển thị tốt, không vỡ layout"
        self.test_actual = ""

    def tearDown(self):
        # Logic ghi log tự động
        method_id = self.id().split('.')[-1]
        description = self._testMethodDoc or "No description"
        outcome = self._outcome.errors
        status = "PASS"
        error_msg = ""
        for test, exc_info in outcome:
            if exc_info:
                status = "FAIL"
                error_msg = str(exc_info[1])

        if status == "PASS":
            self.test_actual = "Hiển thị tốt trên thiết bị này."
        else:
            self.test_actual = f"Lỗi hiển thị: {error_msg}"

        self.reporter.add_result(
            case_id=method_id, module="Compatibility", test_name=description,
            steps=self.test_steps, input_data=self.test_input,
            expected=self.test_expected, actual=self.test_actual,
            status=status, priority="Medium", remarks=error_msg
        )

    # --- HÀM HỖ TRỢ CHẠY TEST ---
    def run_test_on_browser_config(self, options, device_name):
        self.test_input = f"Device: {device_name}"
        self.test_steps = f"1. Khởi động Chrome ({device_name})\n2. Truy cập /login\n3. Kiểm tra UI"

        print(f"\n>>> 📱 Testing on: {device_name}...")
        driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)

        try:
            driver.get(f"{BASE_URL}/login")
            time.sleep(1)

            if "AI" not in driver.title:
                raise Exception("Sai tiêu đề trang")

            # Kiểm tra nút bấm có hiện không
            btn = driver.find_element("css selector", ".sign-in-container button")
            if btn.is_displayed() and btn.is_enabled():
                print(f"   ✅ {device_name}: OK")
                return True
            else:
                raise Exception("Nút đăng nhập bị ẩn/che khuất")

        except Exception as e:
            print(f"   ❌ {device_name}: Lỗi - {e}")
            raise e  # Ném lỗi ra để tearDown bắt được và ghi Fail
        finally:
            driver.quit()

    # --- CÁC TEST CASE ---
    def test_desktop_chrome(self):
        """Test trên Desktop Chrome chuẩn"""
        options = Options()
        options.add_argument("--start-maximized")
        self.run_test_on_browser_config(options, "Desktop Chrome")

    def test_mobile_emulation(self):
        """Test giả lập iPhone 12 Pro"""
        options = Options()
        mobile_emulation = {"deviceName": "iPhone 12 Pro"}
        options.add_experimental_option("mobileEmulation", mobile_emulation)
        self.run_test_on_browser_config(options, "Mobile (iPhone 12 Pro)")

    def test_headless_mode(self):
        """Test chế độ Headless (Server)"""
        options = Options()
        options.add_argument("--headless")
        options.add_argument("--window-size=1920,1080")
        self.run_test_on_browser_config(options, "Headless Mode")


if __name__ == "__main__":
    unittest.main()