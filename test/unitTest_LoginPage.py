import unittest
import sys
import os
import time  # <--- THÊM THƯ VIỆN NÀY
from app import app, users_db
from utils.excel_reporter import ExcelReporter

# --- CẤU HÌNH ĐƯỜNG DẪN ---
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))


class TestAILoginSystem(unittest.TestCase):
    reporter = ExcelReporter(report_folder="Result_UnitTest", report_title="Unit_Test_Login")

    def setUp(self):
        """Thiết lập môi trường"""
        app.config['TESTING'] = True
        app.config['WTF_CSRF_ENABLED'] = False
        app.config['SECRET_KEY'] = 'test_key'
        self.client = app.test_client()

        # Cố gắng xóa DB lần nữa để chắc chắn
        users_db.clear()
        users_db['admin'] = '123'

    def tearDown(self):
        """Ghi nhận kết quả"""
        method_id = self.id().split('.')[-1]
        description = self._testMethodDoc or "No description"
        outcome = self._outcome.errors
        status = "PASS"
        error_msg = ""
        for test, exc_info in outcome:
            if exc_info:
                status = "FAIL"
                error_msg = str(exc_info[1])
        self.reporter.add_result(method_id, description, status, error_msg)

    @classmethod
    def tearDownClass(cls):
        cls.reporter.save_report()

    # --- CÁC TEST CASE ---

    def test_login_page_loads(self):
        response = self.client.get('/login')
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'name="username"', response.data)

    def test_home_redirects_when_not_logged_in(self):
        response = self.client.get('/', follow_redirects=True)
        self.assertIn("Đăng Nhập".encode('utf-8'), response.data)

    def test_register_success(self):
        """Test đăng ký tài khoản mới thành công (Kiểm tra bằng cách đăng nhập thử)"""

        # 1. Tạo thông tin user mới
        unique_username = f"testuser_{int(time.time())}"
        unique_password = "password123"

        # 2. Gửi request ĐĂNG KÝ
        response_reg = self.client.post('/login', data=dict(
            username=unique_username,
            password=unique_password,
            action='register'
        ), follow_redirects=True)

        # Kiểm tra giao diện báo thành công (HTML)
        # Lưu ý: Đảm bảo dòng chữ này khớp với app.py của bạn
        self.assertIn("Đăng ký thành công".encode('utf-8'), response_reg.data)

        # 3. Gửi request ĐĂNG NHẬP bằng tài khoản vừa tạo (Thay vì check biến users_db)
        # Nếu đăng nhập được, chứng tỏ user đã được lưu vào DB chuẩn
        response_login = self.client.post('/login', data=dict(
            username=unique_username,
            password=unique_password,
            action='login'
        ), follow_redirects=True)

        # 4. Kiểm tra kết quả: Đăng nhập thành công sẽ thấy tên App hoặc nút logout
        # Giả sử khi đăng nhập thành công sẽ thấy chữ "AI Vision Pro" hoặc trang dashboard
        self.assertIn(b'AI Vision Pro', response_login.data)

    def test_register_duplicate(self):
        """Test đăng ký trùng tên admin"""
        response = self.client.post('/login', data=dict(
            username='admin',
            password='newpass',
            action='register'
        ), follow_redirects=True)
        self.assertIn("Tài khoản đã tồn tại".encode('utf-8'), response.data)

    def test_login_success(self):
        response = self.client.post('/login', data=dict(username='admin', password='123', action='login'),
                                    follow_redirects=True)
        self.assertIn(b'AI Vision Pro', response.data)

    def test_login_failure(self):
        response = self.client.post('/login', data=dict(username='admin', password='wrong', action='login'),
                                    follow_redirects=True)
        self.assertIn("Sai".encode('utf-8'), response.data)

    def test_logout(self):
        # Đăng nhập trước
        self.client.post('/login', data=dict(username='admin', password='123', action='login'), follow_redirects=True)
        # Đăng xuất
        response = self.client.get('/logout', follow_redirects=True)
        self.assertIn("Đăng Nhập".encode('utf-8'), response.data)


if __name__ == '__main__':
    unittest.main()