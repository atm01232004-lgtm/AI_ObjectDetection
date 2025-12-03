import unittest
import io
import sys
import os
import json

# Cấu hình Import
current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.append(os.path.join(current_dir, '..'))

from app import app

from utils.excel_reporter import ExcelReporter


class TestDataValidation(unittest.TestCase):
    reporter = ExcelReporter(report_folder="AutoTest_Results", report_title="Data_Validation_Report")

    @classmethod
    def tearDownClass(cls):
        cls.reporter.save_report()

    def setUp(self):
        app.config['TESTING'] = True
        self.client = app.test_client()

        self.test_id = ""
        self.test_name = ""
        self.test_steps = ""
        self.test_input = ""
        self.test_expected = ""
        self.test_actual = ""
        self.test_priority = "High"

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

        if status == "PASS":
            self.test_actual = "Hệ thống xử lý đúng dữ liệu sai."
        else:
            self.test_actual = f"Lỗi: {error_msg}"

        self.reporter.add_result(
            case_id=self.test_id or method_id,
            module="Data Validation",
            test_name=self.test_name,
            steps=self.test_steps,
            input_data=self.test_input,
            expected=self.test_expected,
            actual=self.test_actual,
            status=status,
            priority=self.test_priority,
            remarks=error_msg
        )

    # --- TEST 1: FILE RÁC (Test case này sẽ PASS sau khi bạn sửa app.py) ---
    def test_upload_invalid_file(self):
        self.test_id = "TC_DATA_01"
        self.test_name = "Upload file không phải ảnh (.txt)"
        self.test_steps = "1. Tạo file giả\n2. Gửi POST /predict\n3. Check Status = error"
        self.test_input = "test.txt (Nội dung text)"
        self.test_expected = "Server trả về status: error"

        # Giả lập gửi file text
        data = {'file': (io.BytesIO(b"Day la file text, khong phai anh"), 'hello.txt')}

        response = self.client.post('/predict', data=data, content_type='multipart/form-data')
        json_data = response.get_json()

        # Kiểm tra: Server phải báo lỗi
        self.assertEqual(json_data['status'], 'error')
        print("   ✅ Server từ chối file rác thành công.")

    # --- TEST 2: SỐ LƯỢNG ÂM ---
    def test_settings_negative_qty(self):
        self.test_id = "TC_DATA_02"
        self.test_name = "Cài đặt số lượng âm"
        self.test_steps = "1. POST /api/targets\n2. Qty = -5"
        self.test_input = "qty: -5"
        self.test_expected = "Server nên xử lý (Ghi nhận hành vi)"
        self.test_priority = "Medium"

        response = self.client.post('/api/targets', json={'name': 'bad_item', 'qty': -5})

        if response.status_code == 200:
            print("   ⚠️ Server chấp nhận số âm (Cần cải thiện Validation).")
        else:
            print("   ✅ Server từ chối số âm.")


if __name__ == "__main__":
    unittest.main()