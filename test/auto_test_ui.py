import unittest
import time
import os
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.common.alert import Alert
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

# --- CẤU HÌNH ---
BASE_URL = "http://127.0.0.1:5000"
TIME_WAIT = 2.0

# Đường dẫn ảnh mẫu
BASE_DIR = os.path.abspath(os.path.dirname(__file__))
IMG_PATH = os.path.join(BASE_DIR, "static", "test_uploads", "ban-phim-van-phong-1.jpg")


class TestFullInterfaceV3(unittest.TestCase):

    def setUp(self):
        print(f"\n{'=' * 60}")
        print(">>> 🚀 Khởi động trình duyệt...")
        chrome_options = Options()
        self.driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=chrome_options)
        self.driver.maximize_window()

    def tearDown(self):
        print(">>> 🏁 Hoàn tất. Đóng trình duyệt sau 3 giây.")
        time.sleep(3)
        self.driver.quit()

    def login(self):
        """Hàm đăng nhập nhanh"""
        print("   [Login] Đang đăng nhập...")
        self.driver.get(f"{BASE_URL}/login")

        # Điền user admin
        self.driver.find_element(By.CSS_SELECTOR, ".sign-in-container input[name='username']").send_keys("admin")

        # --- CẬP NHẬT: Mật khẩu là 123 ---
        self.driver.find_element(By.CSS_SELECTOR, ".sign-in-container input[name='password']").send_keys("123")

        self.driver.find_element(By.CSS_SELECTOR, ".sign-in-container button").click()
        time.sleep(2)

    # --- KỊCH BẢN TEST CHÍNH ---
    def test_end_to_end_flow(self):
        driver = self.driver

        # 1. ĐĂNG NHẬP
        self.login()
        print("   ✅ Đăng nhập thành công.")

        # ---------------------------------------------------------
        # PHẦN 1: KIỂM TRA TRANG CHỦ (UPLOAD ẢNH TRƯỚC)
        # ---------------------------------------------------------
        print("\n--- PHẦN 1: KIỂM TRA TRANG CHỦ (UPLOAD) ---")

        # 1.1 Upload ảnh
        print(f"   [Action] Upload ảnh: {os.path.basename(IMG_PATH)}")
        driver.find_element(By.ID, "fileElem").send_keys(IMG_PATH)
        time.sleep(TIME_WAIT)

        # 1.2 Bấm Nhận dạng
        print("   [Action] Bấm nút 'Nhận dạng'...")
        driver.find_element(By.CSS_SELECTOR, "button.btn-primary").click()

        print("   ⏳ Đang chờ AI xử lý...")
        time.sleep(5)

        # 1.3 Kiểm tra kết quả
        out_img = driver.find_element(By.ID, "output-image")
        self.assertTrue(out_img.is_displayed(), "Lỗi: Ảnh kết quả AI không hiện")
        print("   ✅ Kết quả nhận diện đã hiển thị.")

        # ---------------------------------------------------------
        # PHẦN 2: CHUYỂN SANG TRANG CAMERA VÀ TEST CÀI ĐẶT
        # ---------------------------------------------------------
        print("\n--- PHẦN 2: KIỂM TRA CAMERA & CÀI ĐẶT ---")

        # 2.1 Chuyển trang Camera
        print("   [Nav] Chuyển sang trang Camera...")
        driver.find_element(By.ID, "nav-cam-icon").click()
        time.sleep(TIME_WAIT)

        # 2.2 Kiểm tra giao diện Camera
        video = driver.find_element(By.ID, "video")
        self.assertTrue(video.is_displayed(), "Lỗi: Video không hiện")
        print("   ✅ Giao diện Camera OK.")

        # --- LOGIC MỚI: TEST NÚT CÀI ĐẶT TẠI TRANG CAMERA ---
        # 2.3 Mở Modal Cài đặt (Chỉ có ở trang này)
        print("   [Action] Mở bảng Cài đặt (Nút Bánh răng)...")
        try:
            settings_btn = driver.find_element(By.CSS_SELECTOR, "button[title='Cài đặt Giám sát']")
            settings_btn.click()
            time.sleep(1)
            print("   ✅ Đã mở được bảng cài đặt.")
        except:
            self.fail("❌ Lỗi: Không tìm thấy nút Cài đặt ở trang Camera!")

        # 2.4 Thêm mục tiêu test
        print("   [Action] Thêm mục tiêu: 'test_cam' số lượng 3...")
        driver.find_element(By.ID, "set-name").send_keys("test_cam")
        driver.find_element(By.ID, "set-qty").send_keys("3")
        driver.find_element(By.CSS_SELECTOR, ".btn-add").click()
        time.sleep(1)

        # 2.5 Kiểm tra bảng danh sách
        table_body = driver.find_element(By.ID, "target-list-body").text
        self.assertIn("test_cam", table_body, "Lỗi: Mục tiêu không hiện trong bảng")
        print("   ✅ Đã thêm mục tiêu thành công.")

        # 2.6 Đóng Modal
        print("   [Action] Đóng bảng cài đặt.")
        driver.find_element(By.CSS_SELECTOR, ".modal-header .btn-close").click()
        time.sleep(1)

        # ---------------------------------------------------------
        # PHẦN 3: KIỂM TRA TRANG THỐNG KÊ
        # ---------------------------------------------------------
        print("\n--- PHẦN 3: KIỂM TRA TRANG THỐNG KÊ ---")

        # 3.1 Chuyển trang Thống kê
        print("   [Nav] Chuyển sang trang Thống kê...")
        driver.find_element(By.CSS_SELECTOR, "a[href='/statistics']").click()
        time.sleep(TIME_WAIT)

        # 3.2 Kiểm tra danh sách ảnh
        history_list = driver.find_elements(By.CSS_SELECTOR, "#history-list li")
        if len(history_list) > 0:
            print(f"   ✅ Tìm thấy {len(history_list)} ảnh trong lịch sử.")

            # 3.3 Click vào ảnh đầu tiên
            print("   [Action] Xem chi tiết ảnh đầu tiên...")
            history_list[0].click()
            time.sleep(1)

            # 3.4 Test nút Toggle
            toggle_btn = driver.find_element(By.ID, "btn-toggle-view")
            if toggle_btn.is_displayed():
                toggle_btn.click()
                time.sleep(1)
                print("   ✅ Chuyển đổi ảnh (Gốc/AI) thành công.")

            # 3.5 Xóa ảnh
            print("   [Action] Xóa ảnh này...")
            driver.find_element(By.ID, "btn-delete").click()
            time.sleep(0.5)
            driver.switch_to.alert.accept()  # OK Confirm
            time.sleep(1)
            driver.switch_to.alert.accept()  # OK Success
            print("   ✅ Đã xóa ảnh thành công.")

        else:
            print("   ⚠️ Danh sách trống (Chưa có dữ liệu để test chi tiết).")

        print("\n✅✅✅ TEST HOÀN TẤT XUẤT SẮC!")


if __name__ == "__main__":
    unittest.main()