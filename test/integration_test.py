import unittest
import os
import sys
import json
import io
import numpy as np
from unittest.mock import patch, MagicMock

# --- CẤU HÌNH IMPORT ---
current_dir = os.path.dirname(os.path.abspath(__file__))
# Thêm đường dẫn thư mục cha để import app và utils
sys.path.append(os.path.join(current_dir, '..'))

from app import app, db, History, User

from utils.excel_reporter import ExcelReporter


class TestIntegration(unittest.TestCase):
    # Khởi tạo bộ báo cáo
    reporter = ExcelReporter(report_folder="AutoTest_Results", report_title="Integration_Test_Report")

    @classmethod
    def tearDownClass(cls):
        cls.reporter.save_report()

    def setUp(self):
        # 1. Cấu hình môi trường Test
        app.config['TESTING'] = True
        app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'  # DB trong RAM
        app.config['WTF_CSRF_ENABLED'] = False

        self.app = app.test_client()

        # 2. Tạo Context và DB
        self.app_context = app.app_context()
        self.app_context.push()

        db.create_all()
        # Tạo user để pass qua login check (nếu cần)
        if not User.query.filter_by(username='admin').first():
            db.session.add(User(username='admin', password='123'))
            db.session.commit()

        # Biến báo cáo
        self.test_steps = ""
        self.test_input = ""
        self.test_expected = "API trả về thành công, DB lưu dữ liệu"
        self.test_actual = ""

    def tearDown(self):
        # Logic ghi log tự động
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
            self.test_actual = "Quy trình tích hợp hoạt động đúng."
        else:
            self.test_actual = f"Lỗi: {error_msg}"

        self.reporter.add_result(
            case_id=method_id, module="Integration", test_name=description,
            steps=self.test_steps, input_data=self.test_input,
            expected=self.test_expected, actual=self.test_actual,
            status=status, priority="High", remarks=error_msg
        )

        db.session.remove()
        db.drop_all()
        self.app_context.pop()

    # --- TEST CASE CHÍNH ---

    # Sử dụng @patch để giả lập các thành phần xử lý ảnh nặng
    @patch('app.model')  # Giả lập AI
    @patch('app.save_image_to_file')  # Giả lập lưu file
    @patch('cv2.imdecode')  # QUAN TRỌNG: Giả lập đọc ảnh
    def test_full_flow_integration(self, mock_cv2, mock_save, mock_ai):
        """Kiểm tra tích hợp: Upload -> AI -> DB -> API History"""
        print(f"\n>>> 🔗 Integration Test Running...")

        # 1. THIẾT LẬP GIẢ LẬP (MOCK)
        # Giả lập hàm cv2.imdecode trả về một bức ảnh đen (ma trận số 0)
        # Điều này giúp vượt qua bước kiểm tra "if img is None" trong app.py
        mock_cv2.return_value = np.zeros((100, 100, 3), dtype=np.uint8)

        # Giả lập AI trả về kết quả rỗng (không cần phát hiện gì cũng được)
        mock_result = MagicMock()
        mock_result.plot.return_value = np.zeros((100, 100, 3), dtype=np.uint8)
        mock_result.boxes = []
        mock_ai.return_value = [mock_result]
        mock_ai.names = {}

        # Giả lập hàm lưu file trả về đường dẫn giả
        mock_save.return_value = "/static/uploads/integration_test.jpg"

        # 2. GỌI API UPLOAD
        self.test_steps = "1. Gửi POST /predict (Mock Image)\n"
        self.test_input = "File: test_integration.jpg (Mock Data)"

        data = {
            'file': (io.BytesIO(b"fake_image_bytes"), 'test_integration.jpg')
        }

        # Gửi request
        response = self.app.post('/predict', data=data, content_type='multipart/form-data')

        # Kiểm tra phản hồi API trước
        self.assertEqual(response.status_code, 200, f"API lỗi: {response.status}")
        json_resp = response.get_json()
        self.assertEqual(json_resp.get('status'), 'success', f"Upload thất bại: {json_resp.get('message')}")
        print("   ✅ API Upload phản hồi thành công.")

        # 3. KIỂM TRA DATABASE (Integration Point 1)
        self.test_steps += "2. Query Database tìm bản ghi\n"

        # Tìm bản ghi có tên file trùng khớp
        history_record = History.query.filter_by(name='test_integration.jpg').first()

        self.assertIsNotNone(history_record, "Lỗi: Không lưu được vào DB")
        self.assertEqual(history_record.source, "Upload")
        print(f"   ✅ Database: Đã tìm thấy bản ghi ID {history_record.id}")

        # 4. KIỂM TRA API HISTORY (Integration Point 2)
        self.test_steps += "3. Gọi GET /api/history kiểm tra dữ liệu trả về"

        history_resp = self.app.get('/api/history')
        json_data = json.loads(history_resp.data)

        found = False
        for item in json_data:
            if item['name'] == 'test_integration.jpg':
                found = True
                break

        self.assertTrue(found, "Lỗi: API History không trả về dữ liệu vừa lưu")
        print("   ✅ API History: Dữ liệu đồng bộ chính xác.")


if __name__ == "__main__":
    unittest.main()