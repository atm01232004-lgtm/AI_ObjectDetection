import unittest
import time
import os
from datetime import datetime
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
import openpyxl
from openpyxl.styles import Font, PatternFill, Alignment

# --- CẤU HÌNH ---
BASE_URL = "http://127.0.0.1:5000"
TIME_WAIT = 2.0
REPORT_FOLDER = "AutoTest_Results"
REPORT_FILE = "Ket_qua_AutoTest_Login.xlsx"


class TestLoginFlow(unittest.TestCase):
    # Dùng biến class để lưu log chung cho tất cả các test case
    test_logs = []

    @classmethod
    def setUpClass(cls):
        """Chạy 1 lần duy nhất khi bắt đầu file test"""
        if not os.path.exists(REPORT_FOLDER):
            os.makedirs(REPORT_FOLDER)

    @classmethod
    def tearDownClass(cls):
        """Chạy 1 lần duy nhất khi kết thúc file test -> Xuất Excel"""
        print(f"\n>>> Đang xuất báo cáo tổng hợp ra file Excel: {REPORT_FILE}")
        cls.export_report_to_excel()

    def setUp(self):
        print(f"\n{'=' * 60}")
        print(f"🚀 BẮT ĐẦU TEST CASE: [{self._testMethodName}]")
        chrome_options = Options()
        # chrome_options.add_argument("--headless")
        self.driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=chrome_options)
        self.driver.maximize_window()

    def tearDown(self):
        print(f"🏁 KẾT THÚC TEST CASE: [{self._testMethodName}]")
        time.sleep(1)
        self.driver.quit()

    def log_step(self, step_name, details, status, error_msg=""):
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        TestLoginFlow.test_logs.append([timestamp, step_name, details, status, error_msg])

        # --- SỬA ĐOẠN NÀY ---
        icon = "❓"
        if status == "PASS":
            icon = "✅"
        elif status == "FAIL":
            icon = "❌"
        elif status == "INFO":
            icon = "ℹ️"  # Icon thông tin màu xanh dương

        print(f"   [{timestamp}] {icon} {step_name}: {status}")

    @classmethod
    def export_report_to_excel(cls):
        try:
            wb = openpyxl.Workbook()
            ws = wb.active
            ws.title = "Login Test Report"

            headers = ["Thời gian", "Tên bước", "Chi tiết", "Trạng thái", "Ghi chú / Lỗi"]
            ws.append(headers)

            header_fill = PatternFill(start_color="CCCCCC", end_color="CCCCCC", fill_type="solid")
            header_font = Font(bold=True)
            for col in range(1, 6):
                cell = ws.cell(row=1, column=col)
                cell.fill = header_fill
                cell.font = header_font
                cell.alignment = Alignment(horizontal="center")

            pass_font = Font(color="008000", bold=True)
            fail_font = Font(color="FF0000", bold=True)

            for row_data in cls.test_logs:
                ws.append(row_data)
                current_row = ws.max_row
                status_cell = ws.cell(row=current_row, column=4)
                if status_cell.value == "PASS":
                    status_cell.font = pass_font
                elif status_cell.value == "FAIL":
                    status_cell.font = fail_font

            # Chỉnh độ rộng cột
            widths = [20, 25, 40, 10, 30]
            for i, w in enumerate(widths, 1):
                col_letter = openpyxl.utils.get_column_letter(i)
                ws.column_dimensions[col_letter].width = w

            # Tạo tên file có ngày giờ để không bị ghi đè
            filename = f"LoginReport_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
            full_path = os.path.join(REPORT_FOLDER, filename)
            wb.save(full_path)
            print(f">>> Đã lưu file: {full_path}")

        except Exception as e:
            print(f"Lỗi xuất Excel: {e}")

    # =========================================================================
    # TEST CASE 1: ĐĂNG KÝ VÀ ĐĂNG NHẬP THÀNH CÔNG (HAPPY PATH)
    # =========================================================================
    def test_1_happy_path(self):
        driver = self.driver
        try:
            self.log_step("Test Case 1", "Chạy kịch bản đăng ký/đăng nhập chuẩn", "INFO")

            # 1. Vào trang Login
            driver.get(f"{BASE_URL}/login")
            time.sleep(TIME_WAIT)

            # 2. Sang Đăng Ký
            driver.find_element(By.ID, "signUp").click()
            time.sleep(TIME_WAIT)

            # 3. Đăng Ký User Mới
            test_user = f"user_{int(time.time())}"
            test_pass = "123456"

            driver.find_element(By.CSS_SELECTOR, ".sign-up-container input[name='username']").send_keys(test_user)
            driver.find_element(By.CSS_SELECTOR, ".sign-up-container input[name='password']").send_keys(test_pass)
            driver.find_element(By.CSS_SELECTOR, ".sign-up-container button").click()

            self.log_step("Đăng Ký", f"Tạo user: {test_user}", "PASS")
            time.sleep(TIME_WAIT)

            # 4. Đăng Nhập
            # Lưu ý: Code trước đó đã có logic tự chuyển về tab đăng nhập nếu thành công
            u_in = driver.find_element(By.CSS_SELECTOR, ".sign-in-container input[name='username']")
            p_in = driver.find_element(By.CSS_SELECTOR, ".sign-in-container input[name='password']")
            b_in = driver.find_element(By.CSS_SELECTOR, ".sign-in-container button")

            u_in.clear()
            u_in.send_keys(test_user)
            p_in.send_keys(test_pass)
            b_in.click()

            self.log_step("Đăng Nhập", "Submit form đăng nhập", "PASS")
            time.sleep(TIME_WAIT)

            # 5. Kiểm tra Dashboard
            if "AI" in driver.title:
                self.log_step("Kết Quả", f"Vào trang chủ thành công (Title: {driver.title})", "PASS")
            else:
                self.log_step("Kết Quả", f"Sai trang: {driver.title}", "FAIL")

        except Exception as e:
            self.log_step("LỖI EXCEPTION", "Lỗi trong Test Case 1", "FAIL", str(e))

    # =========================================================================
    # TEST CASE 2: ĐĂNG NHẬP SAI MẬT KHẨU (NEGATIVE TEST)
    # =========================================================================
    def test_2_wrong_password(self):
        driver = self.driver
        try:
            self.log_step("Test Case 2", "Test đăng nhập sai mật khẩu", "INFO")
            driver.get(f"{BASE_URL}/login")
            time.sleep(TIME_WAIT)

            # Dùng user admin mặc định (nếu có), hoặc user bất kỳ
            driver.find_element(By.CSS_SELECTOR, ".sign-in-container input[name='username']").send_keys("admin")
            driver.find_element(By.CSS_SELECTOR, ".sign-in-container input[name='password']").send_keys("matkhausai123")
            driver.find_element(By.CSS_SELECTOR, ".sign-in-container button").click()

            time.sleep(TIME_WAIT)

            # Kiểm tra xem có thông báo lỗi không
            page_source = driver.page_source
            if "Sai tài khoản hoặc mật khẩu" in page_source:
                self.log_step("Kiểm tra Lỗi", "Hệ thống báo lỗi chính xác", "PASS")
            else:
                self.log_step("Kiểm tra Lỗi", "Hệ thống không báo lỗi sai mật khẩu", "FAIL")

        except Exception as e:
            self.log_step("LỖI EXCEPTION", "Lỗi trong Test Case 2", "FAIL", str(e))

    # =========================================================================
    # TEST CASE 3: ĐĂNG KÝ TRÙNG TÊN (NEGATIVE TEST)
    # =========================================================================
    def test_3_duplicate_register(self):
        driver = self.driver
        try:
            self.log_step("Test Case 3", "Test đăng ký trùng tài khoản", "INFO")
            driver.get(f"{BASE_URL}/login")
            time.sleep(1)
            driver.find_element(By.ID, "signUp").click()
            time.sleep(1)

            # Dùng tên 'admin' vì thường user này đã có sẵn
            existing_user = "admin"

            driver.find_element(By.CSS_SELECTOR, ".sign-up-container input[name='username']").send_keys(existing_user)
            driver.find_element(By.CSS_SELECTOR, ".sign-up-container input[name='password']").send_keys("123")
            driver.find_element(By.CSS_SELECTOR, ".sign-up-container button").click()

            time.sleep(TIME_WAIT)

            # Kiểm tra thông báo lỗi
            if "Tài khoản đã tồn tại" in driver.page_source:
                self.log_step("Kiểm tra Trùng", "Hệ thống chặn đăng ký trùng", "PASS")
            else:
                self.log_step("Kiểm tra Trùng", "Hệ thống cho phép trùng hoặc không báo lỗi", "FAIL")

        except Exception as e:
            self.log_step("LỖI EXCEPTION", "Lỗi trong Test Case 3", "FAIL", str(e))


if __name__ == "__main__":
    unittest.main()