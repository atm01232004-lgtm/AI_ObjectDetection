import unittest
import sys
import os
from datetime import datetime
from app import app, users_db

from utils.excel_reporter import ExcelReporter
# Thư viện Excel
import openpyxl
from openpyxl.styles import Font, PatternFill, Alignment

# --- CẤU HÌNH TÊN THƯ MỤC ---
REPORT_FOLDER = "Result_UnitTest"
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))


class TestAILoginSystem(unittest.TestCase):
    # Biến lưu trữ kết quả dùng chung cho toàn bộ Class
    test_results = []

    # --- PHẦN 1: CẤU HÌNH MÔI TRƯỜNG ---
    reporter = ExcelReporter(report_folder="Result_UnitTest", report_title="Unit_Test_Login")

    def setUp(self):
        app.config['TESTING'] = True
        app.config['WTF_CSRF_ENABLED'] = False
        app.config['SECRET_KEY'] = 'test_key'
        self.client = app.test_client()
        users_db.clear()
        users_db['admin'] = '123'

    def tearDown(self):
        """Ghi nhận kết quả từng test case"""
        # Lấy thông tin lỗi
        method_id = self.id().split('.')[-1]
        description = self._testMethodDoc or "No description"

        outcome = self._outcome.errors
        status = "PASS"
        error_msg = ""

        # Kiểm tra xem có lỗi không
        for test, exc_info in outcome:
            if exc_info:
                status = "FAIL"
                error_msg = str(exc_info[1])

        # Gọi hàm từ module riêng để lưu vào bộ nhớ đệm
        self.reporter.add_result(method_id, description, status, error_msg)

    # --- PHẦN 2: XUẤT EXCEL VÀO FOLDER (QUAN TRỌNG) ---
    @classmethod
    def tearDownClass(cls):
        """Sau khi chạy hết tất cả test -> Xuất file Excel"""
        cls.reporter.save_report()

    # --- PHẦN 3: CÁC TEST CASE (Giữ nguyên) ---

    def test_login_page_loads(self):
        """Kiểm tra tải trang đăng nhập"""
        response = self.client.get('/login')
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'name="username"', response.data)

    def test_home_redirects_when_not_logged_in(self):
        """Chưa đăng nhập mà vào trang chủ thì phải bị đá về login"""
        response = self.client.get('/', follow_redirects=True)
        self.assertIn(b'\xc4\x90\xc4\x83ng Nh\xe1\xba\xadp', response.data)

    def test_register_success(self):
        """Test đăng ký tài khoản mới thành công"""
        response = self.client.post('/login', data=dict(
            username='newuser',
            password='password123',
            action='register'
        ), follow_redirects=True)
        self.assertIn(b'\xc4\x90\xc4\x83ng k\xc3\xbd th\xc3\xa0nh c\xc3\xb4ng', response.data)
        self.assertIn('newuser', users_db)

    def test_register_duplicate(self):
        """Test đăng ký trùng tên admin đã có"""
        response = self.client.post('/login', data=dict(
            username='admin',
            password='newpass',
            action='register'
        ), follow_redirects=True)
        self.assertIn(b'T\xc3\xa0i kho\xe1\xba\xa3n \xc4\x91\xc3\xa3 t\xe1\xbb\x93n t\xe1\xba\xa1i', response.data)

    def test_login_success(self):
        """Test đăng nhập đúng"""
        response = self.client.post('/login', data=dict(username='admin', password='123', action='login'), follow_redirects=True)
        self.assertIn(b'AI Vision Pro', response.data)

    def test_login_failure(self):
        """Test đăng nhập sai"""
        response = self.client.post('/login', data=dict(username='admin', password='wrong', action='login'), follow_redirects=True)
        self.assertIn(b'Sai', response.data)

    def test_logout(self):
        """Test chức năng đăng xuất"""
        self.client.post('/login', data=dict(username='admin', password='123456', action='login'),
                         follow_redirects=True)
        response = self.client.get('/logout', follow_redirects=True)
        self.assertIn(b'\xc4\x90\xc4\x83ng Nh\xe1\xba\xadp', response.data)


if __name__ == '__main__':
    unittest.main()