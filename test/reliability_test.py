import unittest
import time
import sys
import os
from unittest.mock import patch, MagicMock

# --- CẤU HÌNH IMPORT ---
current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.append(os.path.join(current_dir, '..'))

from app import app, socketio

from utils.excel_reporter import ExcelReporter

# Ảnh giả hợp lệ (1x1 pixel)
VALID_FAKE_IMG = "data:image/jpeg;base64,R0lGODlhAQABAIAAAAAAAP///yH5BAEAAAAALAAAAAABAAEAAAIBRAA7"


class TestReliability(unittest.TestCase):
    # Khởi tạo Reporter
    reporter = ExcelReporter(report_folder="AutoTest_Results", report_title="Reliability_Test_Report")

    @classmethod
    def tearDownClass(cls):
        cls.reporter.save_report()

    def setUp(self):
        app.config['TESTING'] = True
        self.client = socketio.test_client(app)

        # Khởi tạo biến báo cáo
        self.test_id = ""
        self.test_name = ""
        self.test_steps = ""
        self.test_input = ""
        self.test_expected = ""
        self.test_actual = ""
        self.test_priority = "High"

    def tearDown(self):
        # Tự động bắt lỗi
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
            self.test_actual = "Hệ thống ổn định, không bị ngắt kết nối."
        else:
            self.test_actual = f"Thất bại: {error_msg}"

        # Ghi vào Excel
        self.reporter.add_result(
            case_id=self.test_id or method_id,
            module="Reliability (Stability)",
            test_name=self.test_name or description,
            steps=self.test_steps,
            input_data=self.test_input,
            expected=self.test_expected,
            actual=self.test_actual,
            status=status,
            priority=self.test_priority,
            remarks=error_msg
        )

    # --- TEST CASE: STRESS TEST SOCKET ---
    @patch('app.model')
    @patch('cv2.imdecode')
    def test_continuous_camera_stream(self, mock_cv2, mock_ai):
        """Stress Test: Gửi 100 khung hình liên tục"""
        self.test_id = "TC_REL_01"
        self.test_name = "Kiểm tra độ ổn định khi tải cao (Socket)"
        self.test_steps = "1. Kết nối Socket\n2. Gửi 100 frames liên tục\n3. Kiểm tra kết nối"
        self.test_input = "100 Frames Base64 (Mock)"
        self.test_expected = "Server xử lý hết, không ngắt kết nối"
        self.test_priority = "Critical"

        # Mock AI trả về rỗng để test tốc độ server
        mock_result = MagicMock()
        mock_result.plot.return_value = [[0]]
        mock_result.boxes = []
        mock_ai.return_value = [mock_result]
        mock_cv2.return_value = [[0]]

        print("\n>>> 🔥 Bắt đầu Stress Test (100 Frames)...")
        start_time = time.time()

        for i in range(100):
            self.client.emit('send_frame', {'image': VALID_FAKE_IMG})
            # Đọc phản hồi để tránh tràn bộ đệm
            self.client.get_received()

        duration = time.time() - start_time
        print(f"   ✅ Đã gửi xong 100 frames trong {duration:.2f}s.")

        # Kiểm tra kết nối
        self.assertTrue(self.client.is_connected(), "Lỗi: Server ngắt kết nối sau khi chịu tải!")


if __name__ == "__main__":
    unittest.main()