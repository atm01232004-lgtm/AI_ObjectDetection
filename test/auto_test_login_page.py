import unittest
import time
import sys
import os
from datetime import datetime
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager

# --- CẤU HÌNH ĐƯỜNG DẪN IMPORT ---
current_dir = os.path.dirname(os.path.abspath(__file__))
# Thêm thư mục 'test' vào sys.path để Python tìm thấy 'utils'
sys.path.append(current_dir)

# Import module báo cáo dùng chung (Tránh lặp code)
from utils.excel_reporter import ExcelReporter

# --- CẤU HÌNH TEST ---
BASE_URL = "http://127.0.0.1:5000"
TIME_WAIT = 2.0


class TestLoginFlow(unittest.TestCase):
    # 1. KHỞI TẠO BỘ BÁO CÁO (DÙNG CHUNG CHO CẢ CLASS)
    reporter = ExcelReporter(report_folder="AutoTest_Results", report_title="Login_Test_Report")

    @classmethod
    def tearDownClass(cls):
        """Chạy 1 lần duy nhất khi kết thúc file test -> Xuất Excel"""
        cls.reporter.save_report()

    def setUp(self):
        print(f"\n{'=' * 60}")
        print(f"🚀 BẮT ĐẦU TEST CASE: [{self._testMethodName}]")
        chrome_options = Options()
        self.driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=chrome_options)
        self.driver.maximize_window()

    def tearDown(self):
        print(f"🏁 KẾT THÚC TEST CASE: [{self._testMethodName}]")
        time.sleep(1)
        self.driver.quit()

    # =========================================================================
    # TEST CASE 1: HAPPY PATH (ĐĂNG KÝ -> ĐĂNG NHẬP)
    # =========================================================================
    def test_1_happy_path(self):
        driver = self.driver
        test_id = "TC_LOGIN_01"
        module = "Login Page"
        name = "Kiểm tra luồng đăng ký và đăng nhập chuẩn"
        steps = ""
        input_data = ""
        actual_result = ""
        status = "FAIL"

        try:
            steps += "1. Truy cập trang Login\n"
            driver.get(f"{BASE_URL}/login")
            time.sleep(TIME_WAIT)

            # Sang Đăng Ký
            steps += "2. Chuyển sang form Đăng Ký\n"
            driver.find_element(By.ID, "signUp").click()
            time.sleep(TIME_WAIT)

            # Đăng Ký
            steps += "3. Điền thông tin đăng ký\n"
            test_user = f"user_{int(time.time())}"
            test_pass = "123456"
            input_data = f"User: {test_user}, Pass: {test_pass}"

            driver.find_element(By.CSS_SELECTOR, ".sign-up-container input[name='username']").send_keys(test_user)
            driver.find_element(By.CSS_SELECTOR, ".sign-up-container input[name='password']").send_keys(test_pass)
            driver.find_element(By.CSS_SELECTOR, ".sign-up-container button").click()
            time.sleep(TIME_WAIT)

            # Đăng Nhập
            steps += "4. Đăng nhập với tài khoản vừa tạo\n"
            u_in = driver.find_element(By.CSS_SELECTOR, ".sign-in-container input[name='username']")
            p_in = driver.find_element(By.CSS_SELECTOR, ".sign-in-container input[name='password']")
            b_in = driver.find_element(By.CSS_SELECTOR, ".sign-in-container button")

            u_in.clear()
            u_in.send_keys(test_user)
            p_in.send_keys(test_pass)
            # Dùng JS Click để chắc chắn
            driver.execute_script("arguments[0].click();", b_in)

            time.sleep(TIME_WAIT)

            # Kiểm tra Dashboard
            if "AI" in driver.title:
                status = "PASS"
                actual_result = f"Đăng nhập thành công, tiêu đề: {driver.title}"
                print("   ✅ Vào trang chủ thành công.")
            else:
                actual_result = f"Sai trang, tiêu đề: {driver.title}"
                print("   ❌ Không vào được trang chủ.")

        except Exception as e:
            actual_result = f"Lỗi Exception: {str(e)}"
            print(f"   ❌ Lỗi: {e}")

        finally:
            # Ghi vào Excel bằng module chung
            self.reporter.add_result(
                case_id=test_id, module=module, test_name=name,
                steps=steps, input_data=input_data,
                expected="Đăng nhập thành công vào Dashboard",
                actual=actual_result, status=status, priority="High"
            )

    # =========================================================================
    # TEST CASE 2: ĐĂNG NHẬP SAI MẬT KHẨU
    # =========================================================================
    def test_2_wrong_password(self):
        driver = self.driver
        test_id = "TC_LOGIN_02"
        module = "Login Page"
        name = "Kiểm tra báo lỗi khi sai mật khẩu"
        steps = "1. Truy cập trang login\n2. Nhập sai pass\n3. Bấm login"
        input_data = "User: admin, Pass: sai_pass"
        actual_result = ""
        status = "FAIL"

        try:
            driver.get(f"{BASE_URL}/login")
            time.sleep(TIME_WAIT)

            driver.find_element(By.CSS_SELECTOR, ".sign-in-container input[name='username']").send_keys("admin")
            driver.find_element(By.CSS_SELECTOR, ".sign-in-container input[name='password']").send_keys("matkhausai123")

            btn = driver.find_element(By.CSS_SELECTOR, ".sign-in-container button")
            driver.execute_script("arguments[0].click();", btn)

            time.sleep(TIME_WAIT)

            if "Sai tài khoản hoặc mật khẩu" in driver.page_source:
                status = "PASS"
                actual_result = "Hệ thống hiển thị thông báo lỗi chính xác"
                print("   ✅ Báo lỗi đúng.")
            else:
                actual_result = "Không thấy thông báo lỗi"
                print("   ❌ Không báo lỗi.")

        except Exception as e:
            actual_result = f"Lỗi: {e}"

        finally:
            self.reporter.add_result(
                case_id=test_id, module=module, test_name=name,
                steps=steps, input_data=input_data,
                expected="Hiển thị thông báo sai mật khẩu",
                actual=actual_result, status=status, priority="Medium"
            )

    # =========================================================================
    # TEST CASE 3: ĐĂNG KÝ TRÙNG TÊN
    # =========================================================================
    def test_3_duplicate_register(self):
        driver = self.driver
        test_id = "TC_LOGIN_03"
        module = "Login Page"
        name = "Kiểm tra chặn đăng ký trùng tên"
        steps = "1. Mở form đăng ký\n2. Nhập tên 'admin'\n3. Submit"
        input_data = "User: admin"
        actual_result = ""
        status = "FAIL"

        try:
            driver.get(f"{BASE_URL}/login")
            time.sleep(1)
            driver.find_element(By.ID, "signUp").click()
            time.sleep(1)

            driver.find_element(By.CSS_SELECTOR, ".sign-up-container input[name='username']").send_keys("admin")
            driver.find_element(By.CSS_SELECTOR, ".sign-up-container input[name='password']").send_keys("123")
            driver.find_element(By.CSS_SELECTOR, ".sign-up-container button").click()

            time.sleep(TIME_WAIT)

            if "Tài khoản đã tồn tại" in driver.page_source:
                status = "PASS"
                actual_result = "Hệ thống báo lỗi tài khoản tồn tại"
                print("   ✅ Chặn trùng thành công.")
            else:
                actual_result = "Không báo lỗi trùng"
                print("   ❌ Cho phép trùng hoặc lỗi khác.")

        except Exception as e:
            actual_result = f"Lỗi: {e}"

        finally:
            self.reporter.add_result(
                case_id=test_id, module=module, test_name=name,
                steps=steps, input_data=input_data,
                expected="Hiển thị lỗi tài khoản tồn tại",
                actual=actual_result, status=status, priority="Medium"
            )


if __name__ == "__main__":
    unittest.main()