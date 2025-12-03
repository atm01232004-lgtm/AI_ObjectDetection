import unittest
import time
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

# --- CẤU HÌNH ---
BASE_URL = "http://127.0.0.1:5000"
TIME_WAIT = 2.5  # Tốc độ chậm để quan sát


class TestCameraPage(unittest.TestCase):

    def setUp(self):
        print(f"\n{'=' * 60}")
        print(">>> 🚀 Khởi động trình duyệt...")
        chrome_options = Options()
        # Cho phép dùng Camera giả (Fake) để không bị trình duyệt chặn hỏi quyền
        chrome_options.add_argument("--use-fake-ui-for-media-stream")
        chrome_options.add_argument("--use-fake-device-for-media-stream")

        self.driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=chrome_options)
        self.driver.maximize_window()

    def tearDown(self):
        print(">>> 🏁 Test xong. Đóng trình duyệt sau 5 giây.")
        time.sleep(5)
        self.driver.quit()

    def login(self):
        """Đăng nhập nhanh để vào hệ thống"""
        print("   [Login] Đang đăng nhập...")
        self.driver.get(f"{BASE_URL}/login")
        time.sleep(1)

        # Điền thông tin
        self.driver.find_element(By.CSS_SELECTOR, ".sign-in-container input[name='username']").send_keys("admin")
        self.driver.find_element(By.CSS_SELECTOR, ".sign-in-container input[name='password']").send_keys("123")

        # Click nút đăng nhập bằng JS để tránh lỗi bị che
        login_btn = self.driver.find_element(By.CSS_SELECTOR, ".sign-in-container button")
        self.driver.execute_script("arguments[0].click();", login_btn)
        time.sleep(2)

    # --- KỊCH BẢN TEST CHÍNH ---
    def test_camera_page_features(self):
        driver = self.driver

        # 1. Đăng nhập
        self.login()

        # 2. Chuyển sang trang Camera
        print(">>> [Step 1] Chuyển hướng sang trang Camera...")
        # Tìm icon camera trên menu
        nav_cam = driver.find_element(By.ID, "nav-cam-icon")
        nav_cam.click()
        time.sleep(TIME_WAIT)

        # Kiểm tra URL
        self.assertIn("/camera", driver.current_url)
        print("   ✅ Đã vào đúng đường dẫn /camera.")

        # 3. Kiểm tra các thành phần giao diện chính
        print(">>> [Step 2] Kiểm tra hiển thị Video và Thông tin...")

        # A. Video & Canvas
        video = driver.find_element(By.ID, "video")
        overlay = driver.find_element(By.ID, "overlay-canvas")

        # Kiểm tra kích thước video > 0 để chắc chắn nó đang chạy
        if video.size['width'] > 0 and overlay.is_displayed():
            print("   ✅ Video và Lớp phủ (Overlay) đang hoạt động.")
        else:
            self.fail("❌ Lỗi: Video camera không hiển thị!")

        # B. Đồng hồ
        clock = driver.find_element(By.ID, "clock")
        print(f"   ✅ Đồng hồ đang chạy: {clock.text}")

        # C. Bảng thông tin (Kiểm tra xem có hiện đúng IP/Phòng không)
        info_area = driver.find_element(By.CLASS_NAME, "info-table-container")
        self.assertIn("Khu Vực A", info_area.text)
        print("   ✅ Thông tin phòng/IP hiển thị đúng.")

        time.sleep(TIME_WAIT)

        # 4. TEST CHỨC NĂNG CÀI ĐẶT (QUAN TRỌNG)
        print(">>> [Step 3] Test chức năng Cài Đặt (Modal)...")

        # A. Mở Modal
        settings_btn = driver.find_element(By.CSS_SELECTOR, "button[onclick='openSettingsModal()']")
        settings_btn.click()
        print("   -> Đã bấm nút mở Cài đặt.")
        time.sleep(1)

        # Kiểm tra Modal có hiện không
        modal = driver.find_element(By.ID, "settings-modal")
        # Class 'hidden' phải bị gỡ bỏ
        self.assertTrue("hidden" not in modal.get_attribute("class"), "Lỗi: Modal không hiện ra!")

        # B. Thêm mục tiêu mới
        test_item_name = "test_mouse"
        print(f"   -> Thêm mục tiêu: {test_item_name} (SL: 10)")

        driver.find_element(By.ID, "set-name").send_keys(test_item_name)
        time.sleep(0.5)
        driver.find_element(By.ID, "set-qty").send_keys("10")
        time.sleep(0.5)

        # Bấm nút cộng
        driver.find_element(By.CSS_SELECTOR, ".btn-add").click()
        time.sleep(1)  # Chờ lưu DB và render lại bảng

        # C. Kiểm tra xem đã vào bảng chưa
        table_body = driver.find_element(By.ID, "target-list-body").text
        if test_item_name in table_body:
            print("   ✅ Đã thêm thành công mục tiêu vào danh sách.")
        else:
            self.fail("❌ Lỗi: Thêm mục tiêu thất bại, không thấy trong bảng.")

        time.sleep(TIME_WAIT)

        # D. Xóa mục tiêu vừa thêm (Dọn dẹp)
        print("   -> Đang xóa mục tiêu vừa tạo...")
        # Tìm nút xóa (thùng rác) cuối cùng trong bảng (là cái vừa thêm)
        del_btns = driver.find_elements(By.CSS_SELECTOR, ".btn-del-target")
        if del_btns:
            del_btns[-1].click()  # Click cái cuối cùng
            time.sleep(1)

            # Kiểm tra lại xem mất chưa
            table_body_after = driver.find_element(By.ID, "target-list-body").text
            if test_item_name not in table_body_after:
                print("   ✅ Đã xóa mục tiêu thành công.")
            else:
                print("   ⚠️ Cảnh báo: Mục tiêu vẫn còn trong bảng sau khi xóa.")

        time.sleep(TIME_WAIT)

        # E. Đóng Modal
        print("   -> Đóng bảng cài đặt.")
        driver.find_element(By.CSS_SELECTOR, ".modal-header .btn-close").click()
        time.sleep(1)

        # Kiểm tra modal đã ẩn chưa
        self.assertTrue("hidden" in modal.get_attribute("class"), "Lỗi: Modal chưa đóng!")
        print("   ✅ Modal đã đóng.")

        print("\n✅✅✅ TEST TRANG CAMERA HOÀN TẤT!")


if __name__ == "__main__":
    unittest.main()