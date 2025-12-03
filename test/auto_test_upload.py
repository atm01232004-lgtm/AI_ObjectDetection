import unittest
import time
import sys
import os
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager

# --- CẤU HÌNH ĐƯỜNG DẪN IMPORT ---
current_dir = os.path.dirname(os.path.abspath(__file__))
# Thêm thư mục cha để import utils
sys.path.append(os.path.join(current_dir, '..'))

from utils.excel_reporter import ExcelReporter


# --- CẤU HÌNH TEST ---
BASE_URL = "http://127.0.0.1:5000"
TIME_WAIT = 3.0

# Đường dẫn ảnh
BASE_DIR = os.path.abspath(os.path.join(current_dir, '..'))  # Lùi ra thư mục gốc dự án
IMG_FOLDER = os.path.join(BASE_DIR, "static", "test_uploads")

# Danh sách ảnh
IMAGE_LIST = [
    "ban-phim-van-phong-1.jpg",
    "mau-ban-ghe-van-phong-hien-dai-1.jpg",
    "Untitled.png",
    "Man-hinh-van-phong-1.jpg",
    "152.png"
]


class TestBatchUpload(unittest.TestCase):
    # Khởi tạo bộ báo cáo Excel
    reporter = ExcelReporter(report_folder="AutoTest_Results", report_title="Auto_Upload_Report")

    @classmethod
    def tearDownClass(cls):
        """Xuất file Excel sau khi chạy xong toàn bộ danh sách"""
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

    def login_helper(self):
        """Đăng nhập nhanh"""
        driver = self.driver
        driver.get(f"{BASE_URL}/login")
        time.sleep(1)

        # Điền user/pass
        driver.find_element(By.CSS_SELECTOR, ".sign-in-container input[name='username']").send_keys("admin")
        driver.find_element(By.CSS_SELECTOR, ".sign-in-container input[name='password']").send_keys("123")

        # Click nút đăng nhập
        btn = driver.find_element(By.CSS_SELECTOR, ".sign-in-container button")
        driver.execute_script("arguments[0].click();", btn)
        time.sleep(2)

    def test_batch_upload_flow(self):
        driver = self.driver

        # 1. Đăng nhập
        try:
            self.login_helper()
            if "AI" not in driver.title:
                raise Exception("Đăng nhập thất bại")
        except Exception as e:
            self.fail(f"Không thể đăng nhập để bắt đầu test: {e}")

        print("   ✅ Đăng nhập thành công. Bắt đầu vòng lặp...")

        # 2. Vòng lặp qua từng ảnh
        for index, img_name in enumerate(IMAGE_LIST, 1):
            print(f"\n--- 📸 ẢNH {index}: {img_name} ---")

            # Khởi tạo biến ghi log cho từng ảnh
            case_id = f"IMG_{index:02d}"
            status = "FAIL"
            actual_result = ""
            error_msg = ""

            full_path = os.path.join(IMG_FOLDER, img_name)

            try:
                # A. Kiểm tra file tồn tại
                if not os.path.exists(full_path):
                    actual_result = "File không tồn tại trên ổ cứng"
                    print(f"   ❌ {actual_result}")
                    # Ghi log lỗi rồi bỏ qua ảnh này
                    self.reporter.add_result(case_id, "Upload Feature", f"Test ảnh: {img_name}",
                                             "Upload -> Predict -> Clear", img_name,
                                             "Nhận diện thành công", actual_result, "FAIL", "High", "File Missing")
                    continue

                # B. Upload ảnh
                # Dùng JS để hiện input file (tránh lỗi ElementNotInteractable)
                file_input = driver.find_element(By.ID, "fileElem")
                driver.execute_script("arguments[0].style.display = 'block';", file_input)
                file_input.send_keys(full_path)
                time.sleep(TIME_WAIT)

                # C. Bấm Nhận dạng
                predict_btn = driver.find_element(By.CSS_SELECTOR, "button.btn-primary")
                predict_btn.click()
                print("   ⏳ Đang chờ AI...")

                # Chờ kết quả (Tăng thời gian nếu ảnh nặng)
                time.sleep(5)

                # D. Lấy kết quả
                output_text_el = driver.find_element(By.ID, "output-text")
                result_text = output_text_el.text.replace("\n", ", ")

                # Kiểm tra xem có kết quả không
                if "Đang xử lý" in result_text or result_text.strip() == "":
                    status = "FAIL"
                    actual_result = "AI không trả về kết quả hoặc bị treo"
                else:
                    status = "PASS"
                    actual_result = f"AI trả về: {result_text}"

                print(f"   ℹ️ {actual_result}")

                # E. Xóa ảnh (Reset)
                try:
                    close_btn = driver.find_element(By.CSS_SELECTOR, ".btn-close-img")
                    driver.execute_script("arguments[0].click();", close_btn)
                    print("   ✅ Đã xóa ảnh cũ.")
                except:
                    print("   ⚠️ Không tìm thấy nút X để xóa ảnh.")

                time.sleep(1)

            except Exception as e:
                status = "FAIL"
                actual_result = f"Lỗi Exception: {str(e)}"
                error_msg = str(e)
                print(f"   ❌ Lỗi: {e}")

            # GHI VÀO BÁO CÁO (Mỗi ảnh 1 dòng)
            self.reporter.add_result(
                case_id=case_id,
                module="Upload & Detect",
                test_name=f"Test nhận diện ảnh: {img_name}",
                steps="1. Chọn ảnh\n2. Bấm nhận dạng\n3. Lấy kết quả\n4. Xóa ảnh",
                input_data=img_name,
                expected="Hiển thị danh sách vật thể",
                actual=actual_result,
                status=status,
                priority="High",
                remarks=error_msg
            )

        print("\n✅✅✅ ĐÃ HOÀN TẤT VÀ LƯU FILE EXCEL!")


if __name__ == "__main__":
    unittest.main()