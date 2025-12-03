import unittest
import time
import requests
import os
import sys

# --- CẤU HÌNH IMPORT ---
current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.append(os.path.join(current_dir, '..'))

from utils.excel_reporter import ExcelReporter


BASE_URL = "http://127.0.0.1:5000"
API_URL = f"{BASE_URL}/predict"
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
IMG_PATH = os.path.join(BASE_DIR, "..", "static", "test_uploads", "ban-phim-van-phong-1.jpg")


class TestPerformance(unittest.TestCase):
    reporter = ExcelReporter(report_folder="AutoTest_Results", report_title="Performance_Test_Report")

    @classmethod
    def tearDownClass(cls):
        cls.reporter.save_report()

    def setUp(self):
        self.test_steps = ""
        self.test_input = "API: /predict"
        self.test_expected = "Thời gian phản hồi < 5s"
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

        self.reporter.add_result(
            case_id=method_id, module="Performance", test_name=description,
            steps=self.test_steps, input_data=self.test_input,
            expected=self.test_expected, actual=self.test_actual,
            status=status, priority="High", remarks=error_msg
        )

    def test_api_response_time(self):
        """Kiểm tra thời gian phản hồi API Upload"""
        self.test_steps = "1. Đọc ảnh test\n2. Gửi POST request\n3. Đo thời gian"

        if not os.path.exists(IMG_PATH):
            raise FileNotFoundError("Không tìm thấy ảnh test")

        with open(IMG_PATH, 'rb') as img:
            start_time = time.time()
            response = requests.post(API_URL, files={'file': img})
            end_time = time.time()

        duration = end_time - start_time
        print(f"\n>>> ⏱️ Thời gian xử lý: {duration:.4f} giây")

        self.test_actual = f"Phản hồi trong {duration:.2f} giây"

        self.assertEqual(response.status_code, 200)
        self.assertLess(duration, 5.0, "API quá chậm (> 5s)")

    def test_load_capacity(self):
        """Stress Test: Gửi 10 request liên tiếp"""
        self.test_steps = "Gửi 10 request liên tục tới API /predict"
        self.test_input = "10 concurrent requests"

        success_count = 0
        total_time = 0
        REQUEST_COUNT = 10

        with open(IMG_PATH, 'rb') as img:
            file_data = img.read()

        print("\n>>> 🔥 Stress Test bắt đầu...")
        for i in range(REQUEST_COUNT):
            start = time.time()
            response = requests.post(API_URL, files={'file': ('test.jpg', file_data)})
            duration = time.time() - start

            if response.status_code == 200:
                success_count += 1
            total_time += duration

        avg_time = total_time / REQUEST_COUNT
        self.test_actual = f"Thành công: {success_count}/{REQUEST_COUNT}. TB: {avg_time:.2f}s"

        self.assertEqual(success_count, REQUEST_COUNT, "Server bị lỗi khi chịu tải cao")


if __name__ == "__main__":
    unittest.main()