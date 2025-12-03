import unittest
import json
import sys
import os
import time
from unittest.mock import patch, MagicMock

# --- IMPORT MODULE TỪ APP ---
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.join(current_dir, '..')
sys.path.append(parent_dir)

from app import app, db, User, Target, History, socketio
from utils.excel_reporter import ExcelReporter

# --- CHUỖI ẢNH GIẢ LẬP HỢP LỆ (1x1 Pixel) ---
# Dùng chuỗi này thay cho "AA" để tránh lỗi Incorrect Padding
VALID_FAKE_IMG = "data:image/jpeg;base64,R0lGODlhAQABAIAAAAAAAP///yH5BAEAAAAALAAAAAABAAEAAAIBRAA7"


class TestCameraBackendFunctions(unittest.TestCase):
    reporter = ExcelReporter(report_folder="Result_UnitTest", report_title="Unit_Test_Camera_Logic")

    def setUp(self):
        """Thiết lập môi trường giả lập"""
        app.config['TESTING'] = True
        app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
        app.config['UPLOAD_FOLDER'] = 'static/test_uploads'

        self.app = app.test_client()
        self.socket_client = socketio.test_client(app)

        self.app_context = app.app_context()
        self.app_context.push()

        db.create_all()
        if not User.query.filter_by(username='admin').first():
            db.session.add(User(username='admin', password='123'))
            db.session.commit()

        import app as app_module
        app_module.last_save_time = 0
        app_module.last_detected_state = {}

    def tearDown(self):
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

        db.session.remove()
        db.drop_all()
        self.app_context.pop()

    @classmethod
    def tearDownClass(cls):
        cls.reporter.save_report()

    # --- NHÓM 1: TEST API (Giữ nguyên vì đã chạy đúng) ---
    def test_api_add_target(self):
        """Test API: Thêm mục tiêu giám sát"""
        response = self.app.post('/api/targets', json={'name': 'laptop', 'qty': 2})
        self.assertEqual(response.status_code, 200)
        target = Target.query.filter_by(name='laptop').first()
        self.assertIsNotNone(target)

    def test_api_update_target(self):
        """Test API: Cập nhật mục tiêu"""
        db.session.add(Target(name='mouse', min_qty=1))
        db.session.commit()
        self.app.post('/api/targets', json={'name': 'mouse', 'qty': 5})
        target = Target.query.filter_by(name='mouse').first()
        self.assertEqual(target.min_qty, 5)

    # --- NHÓM 2: TEST SOCKET (ĐÃ SỬA LỖI ẢNH) ---

    @patch('app.model')
    @patch('cv2.imdecode')
    def test_socket_alert_logic(self, mock_cv2, mock_ai):
        """Test Socket: Logic Cảnh báo (Alert) khi thiếu đồ"""
        print(f"\n🚀 [Test] Kiểm tra logic Báo động...")

        db.session.add(Target(name='laptop', min_qty=3))
        db.session.commit()

        mock_result = MagicMock()
        mock_result.plot.return_value = [[0]]
        box1 = MagicMock();
        box1.cls = [1]
        mock_result.boxes = [box1]
        mock_ai.return_value = [mock_result]
        mock_ai.names = {1: 'laptop'}
        mock_cv2.return_value = [[0]]

        # SỬA: Dùng VALID_FAKE_IMG
        self.socket_client.emit('send_frame', {'image': VALID_FAKE_IMG})

        received = self.socket_client.get_received()

        # Kiểm tra xem có nhận được phản hồi không
        if not received:
            self.fail("❌ Lỗi: Server không phản hồi (Có thể do decode ảnh thất bại)")

        data = received[0]['args'][0]
        self.assertTrue(data['is_alert'])
        print("   ✅ Hệ thống báo động đúng.")

    @patch('app.model')
    @patch('app.save_image_to_file')
    @patch('cv2.imdecode')
    def test_socket_auto_save_on_change(self, mock_cv2, mock_save_file, mock_ai):
        """Test Socket: Tự động lưu khi có sự thay đổi"""
        print(f"\n🚀 [Test] Kiểm tra lưu khi có thay đổi...")

        mock_result = MagicMock()
        mock_result.plot.return_value = [[0]]
        mock_result.boxes = [MagicMock(cls=[2])]
        mock_ai.return_value = [mock_result]
        mock_ai.names = {2: 'cat'}
        mock_cv2.return_value = [[0]]
        mock_save_file.return_value = "/path/img.jpg"

        # SỬA: Dùng VALID_FAKE_IMG
        self.socket_client.emit('send_frame', {'image': VALID_FAKE_IMG})

        history = History.query.all()
        self.assertEqual(len(history), 1)
        self.assertEqual(history[0].source, 'Camera (THAY ĐỔI)')
        print("   ✅ Đã lưu lần 1 do thay đổi trạng thái.")

    @patch('app.model')
    @patch('app.save_image_to_file')
    @patch('cv2.imdecode')
    def test_socket_skip_save_no_change(self, mock_cv2, mock_save_file, mock_ai):
        """Test Socket: KHÔNG lưu khi không có gì thay đổi"""
        print(f"\n🚀 [Test] Kiểm tra bỏ qua lưu khi giống hệt...")

        import app as app_module
        app_module.last_detected_state = {'dog': 1}
        app_module.last_save_time = time.time()

        mock_result = MagicMock()
        mock_result.plot.return_value = [[0]]
        mock_result.boxes = [MagicMock(cls=[5])]
        mock_ai.return_value = [mock_result]
        mock_ai.names = {5: 'dog'}
        mock_cv2.return_value = [[0]]

        # SỬA: Dùng VALID_FAKE_IMG
        self.socket_client.emit('send_frame', {'image': VALID_FAKE_IMG})

        history = History.query.all()
        self.assertEqual(len(history), 0)
        print("   ✅ Không lưu vì dữ liệu giống hệt.")

    @patch('app.model')
    @patch('app.save_image_to_file')
    @patch('cv2.imdecode')
    def test_socket_periodic_save(self, mock_cv2, mock_save_file, mock_ai):
        """Test Socket: Lưu định kỳ (Periodic) dù không thay đổi"""
        print(f"\n🚀 [Test] Kiểm tra lưu định kỳ (1 tiếng/lần)...")

        import app as app_module
        app_module.last_detected_state = {'dog': 1}
        app_module.last_save_time = time.time() - 7200

        mock_result = MagicMock()
        mock_result.plot.return_value = [[0]]
        mock_result.boxes = [MagicMock(cls=[5])]
        mock_ai.return_value = [mock_result]
        mock_ai.names = {5: 'dog'}
        mock_cv2.return_value = [[0]]
        mock_save_file.return_value = "/path/img.jpg"

        # SỬA: Dùng VALID_FAKE_IMG
        self.socket_client.emit('send_frame', {'image': VALID_FAKE_IMG})

        history = History.query.first()
        self.assertIsNotNone(history)
        self.assertEqual(history.source, 'Camera (ĐỊNH KỲ)')
        print("   ✅ Đã lưu bản ghi định kỳ.")


if __name__ == '__main__':
    unittest.main()