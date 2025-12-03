import unittest
import sys
import os
import time

# --- CẤU HÌNH ĐƯỜNG DẪN IMPORT ---
current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.append(os.path.join(current_dir, '..'))

from app import app, db, User

from utils.excel_reporter import ExcelReporter



class TestAILoginSystem(unittest.TestCase):
    reporter = ExcelReporter(report_folder="AutoTest_Results", report_title="Unit_Test_Login_Result")

    def setUp(self):
        """Thiết lập môi trường"""
        app.config['TESTING'] = True
        app.config['WTF_CSRF_ENABLED'] = False
        app.config['SECRET_KEY'] = 'test_secret_key'
        app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'

        self.client = app.test_client()
        self.app_context = app.app_context()
        self.app_context.push()

        db.session.remove()
        db.drop_all()
        db.create_all()

        if not User.query.filter_by(username='admin').first():
            db.session.add(User(username='admin', password='123'))
            db.session.commit()

        # Khai báo biến báo cáo mặc định
        self.test_steps = ""
        self.test_input = ""
        self.test_expected = ""
        self.test_actual = ""

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

        if status == "PASS":
            self.test_actual = "Hệ thống phản hồi đúng như mong đợi."
        else:
            self.test_actual = f"Lỗi: {error_msg}"

        self.reporter.add_result(
            case_id=method_id,
            module="Login Module",
            test_name=description,
            steps=self.test_steps,
            input_data=self.test_input,
            expected=self.test_expected,
            actual=self.test_actual,
            status=status,
            priority="High",
            remarks=error_msg
        )

        db.session.remove()
        db.drop_all()
        self.app_context.pop()

    @classmethod
    def tearDownClass(cls):
        cls.reporter.save_report()

    # =================================================================
    # CÁC TEST CASE ĐÃ ĐƯỢC CHỈNH SỬA LOGIC BÁO CÁO
    # =================================================================

    def test_login_page_loads(self):
        """Kiểm tra tải trang đăng nhập"""
        self.test_steps = "1. Gửi request GET tới /login\n2. Kiểm tra mã phản hồi\n3. Kiểm tra nội dung HTML"
        self.test_input = "URL: /login"
        self.test_expected = "Trang web tải thành công (Code 200), có ô nhập liệu"

        response = self.client.get('/login')
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'name="username"', response.data)

    def test_home_redirects_when_not_logged_in(self):
        """Kiểm tra bảo mật trang chủ (Redirect)"""
        self.test_steps = "1. Gửi request GET tới / (chưa login)\n2. Kiểm tra chuyển hướng"
        self.test_input = "URL: /"
        self.test_expected = "Bị chuyển hướng về trang Login"

        response = self.client.get('/', follow_redirects=True)
        self.assertIn(b'name="username"', response.data)

    def test_register_success(self):
        """Test đăng ký tài khoản mới thành công"""
        unique_user = f"user_{int(time.time())}"
        self.test_steps = "1. Gửi POST /login (action=register)\n2. Kiểm tra thông báo\n3. Kiểm tra Database"
        self.test_input = f"User: {unique_user}, Pass: 123"
        self.test_expected = "Thông báo 'Đăng ký thành công', User được lưu vào DB"

        response = self.client.post('/login', data=dict(
            username=unique_user,
            password='123',
            action='register'
        ), follow_redirects=True)

        html = response.data.decode('utf-8')
        self.assertIn("Đăng ký thành công", html)

        with app.app_context():
            user = User.query.filter_by(username=unique_user).first()
            self.assertIsNotNone(user)

    def test_register_duplicate(self):
        """Test đăng ký trùng tên admin"""
        self.test_steps = "1. Tạo user 'admin' (đã có)\n2. Gửi POST đăng ký 'admin'\n3. Kiểm tra lỗi"
        self.test_input = "User: admin (Duplicate)"
        self.test_expected = "Hiển thị lỗi 'Tài khoản đã tồn tại'"

        response = self.client.post('/login', data=dict(
            username='admin',
            password='newpass',
            action='register'
        ), follow_redirects=True)

        html = response.data.decode('utf-8')
        self.assertIn("Tài khoản đã tồn tại", html)

    def test_login_success(self):
        """Test đăng nhập đúng"""
        self.test_steps = "1. Gửi POST /login (action=login)\n2. Kiểm tra chuyển hướng"
        self.test_input = "User: admin, Pass: 123"
        self.test_expected = "Chuyển hướng vào trang chủ (AI Vision Pro)"

        response = self.client.post('/login', data=dict(
            username='admin',
            password='123',
            action='login'
        ), follow_redirects=True)

        self.assertIn(b'AI Vision Pro', response.data)

    def test_login_failure(self):
        """Test đăng nhập sai mật khẩu"""
        self.test_steps = "1. Gửi POST /login với pass sai\n2. Kiểm tra thông báo lỗi"
        self.test_input = "User: admin, Pass: wrongpass"
        self.test_expected = "Hiển thị lỗi 'Sai tài khoản hoặc mật khẩu'"

        response = self.client.post('/login', data=dict(
            username='admin',
            password='wrongpass',
            action='login'
        ), follow_redirects=True)

        html = response.data.decode('utf-8')
        self.assertIn("Sai tài khoản", html)

    def test_logout(self):
        """Test chức năng đăng xuất"""
        self.test_steps = "1. Đăng nhập\n2. Gọi GET /logout\n3. Kiểm tra chuyển hướng"
        self.test_input = "Action: Logout"
        self.test_expected = "Phiên đăng nhập bị hủy, quay về Login"

        # Login trước
        self.client.post('/login', data=dict(username='admin', password='123', action='login'), follow_redirects=True)

        # Logout
        response = self.client.get('/logout', follow_redirects=True)
        self.assertIn(b'name="username"', response.data)


if __name__ == '__main__':
    unittest.main()