import os
import openpyxl
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
from openpyxl.utils import get_column_letter
from datetime import datetime


class ExcelReporter:
    def __init__(self, report_folder="Test_Reports", report_title="Test_Run_Result"):
        self.report_folder = report_folder
        self.report_title = report_title
        self.results = []

    def add_result(self, case_id, module, test_name, steps, input_data, expected, actual, status, priority, remarks=""):
        """
        Thêm một dòng kết quả với đầy đủ các trường theo chuẩn Test Case.
        """
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        # Sắp xếp dữ liệu theo thứ tự cột hiển thị
        row_data = [
            timestamp,  # Cột 1: Thời gian chạy
            case_id,  # Cột 2: ID Test Case
            module,  # Cột 3: Module/Feature
            test_name,  # Cột 4: Tên Test Case
            steps,  # Cột 5: Các Bước Thực hiện
            input_data,  # Cột 6: Dữ liệu Test (Input)
            expected,  # Cột 7: Kết quả Mong muốn
            actual,  # Cột 8: Kết quả Thực tế
            status,  # Cột 9: Tình trạng (PASS/FAIL)
            priority,  # Cột 10: Mức độ Ưu tiên
            remarks  # Cột 11: Ghi chú / Chi tiết lỗi
        ]
        self.results.append(row_data)

    def save_report(self):
        """Xuất file Excel ra thư mục với định dạng đẹp"""
        print(f"\n>>> Đang xuất báo cáo vào thư mục: {self.report_folder}...")

        try:
            wb = openpyxl.Workbook()
            ws = wb.active
            ws.title = "Detailed Report"

            # 1. Định nghĩa Header
            headers = [
                "Thời gian", "ID Case", "Module", "Tên Test Case",
                "Các Bước Thực hiện", "Input Data", "Kết quả Mong muốn",
                "Kết quả Thực tế", "Trạng thái", "Độ ưu tiên", "Ghi chú"
            ]
            ws.append(headers)

            # 2. Style Header (Nền xám, Chữ đậm, Căn giữa, Viền)
            header_fill = PatternFill(start_color="4F81BD", end_color="4F81BD",
                                      fill_type="solid")  # Màu xanh nhạt chuyên nghiệp
            header_font = Font(bold=True, color="FFFFFF", size=11)
            thin_border = Border(left=Side(style='thin'), right=Side(style='thin'),
                                 top=Side(style='thin'), bottom=Side(style='thin'))

            for col_num, _ in enumerate(headers, 1):
                cell = ws.cell(row=1, column=col_num)
                cell.fill = header_fill
                cell.font = header_font
                cell.alignment = Alignment(horizontal="center", vertical="center")
                cell.border = thin_border

            # 3. Định nghĩa Font cho Status
            pass_font = Font(color="008000", bold=True)  # Xanh lá
            fail_font = Font(color="FF0000", bold=True)  # Đỏ
            blocked_font = Font(color="FFA500", bold=True)  # Cam

            # 4. Ghi dữ liệu & Format từng dòng
            for row_idx, row_data in enumerate(self.results, 2):  # Bắt đầu từ dòng 2
                for col_idx, value in enumerate(row_data, 1):
                    cell = ws.cell(row=row_idx, column=col_idx, value=value)
                    cell.border = thin_border

                    # Căn chỉnh: Wrap text cho các cột dài (Steps, Expected, Actual, Remarks)
                    # Các cột 5, 7, 8, 11 là các cột nội dung dài
                    if col_idx in [5, 7, 8, 11]:
                        cell.alignment = Alignment(wrap_text=True, vertical="top")
                    else:
                        cell.alignment = Alignment(horizontal="center", vertical="top")

                    # Tô màu cột Status (Cột 9)
                    if col_idx == 9:
                        status_text = str(value).upper()
                        if "PASS" in status_text:
                            cell.font = pass_font
                        elif "FAIL" in status_text:
                            cell.font = fail_font
                        else:
                            cell.font = blocked_font

            # 5. Chỉnh độ rộng cột (Width)
            # Index: 1-Time, 2-ID, 3-Module, 4-Name, 5-Steps, 6-Input, 7-Exp, 8-Act, 9-Status, 10-Prio, 11-Note
            column_widths = [20, 15, 20, 30, 40, 20, 30, 30, 15, 12, 35]

            for i, w in enumerate(column_widths, 1):
                col_letter = get_column_letter(i)
                ws.column_dimensions[col_letter].width = w

            # 6. Tạo thư mục và lưu file
            if not os.path.exists(self.report_folder):
                os.makedirs(self.report_folder)

            timestamp_str = datetime.now().strftime('%Y-%m-%d_%H-%M-%S')
            filename = f"{self.report_title}_{timestamp_str}.xlsx"
            full_path = os.path.join(self.report_folder, filename)

            wb.save(full_path)
            print(f">>> ✅ Đã lưu báo cáo thành công tại: {os.path.abspath(full_path)}")

        except Exception as e:
            print(f">>> ❌ Lỗi xuất Excel: {e}")


# # ==========================================
# # VÍ DỤ CÁCH SỬ DỤNG (DEMO)
# # ==========================================
# if __name__ == "__main__":
#     reporter = ExcelReporter()
#
#     # Thêm Test Case 1: PASS
#     reporter.add_result(
#         case_id="TC-001",
#         module="Đăng nhập",
#         test_name="Đăng nhập đúng thông tin",
#         steps="1. Nhập user\n2. Nhập pass\n3. Click Login",
#         input_data="user: admin / pass: 123",
#         expected="Chuyển đến trang Dashboard",
#         actual="Chuyển đến trang Dashboard",
#         status="PASS",
#         priority="High",
#         remarks=""
#     )
#
#     # Thêm Test Case 2: FAIL
#     reporter.add_result(
#         case_id="TC-002",
#         module="Đăng nhập",
#         test_name="Đăng nhập sai pass",
#         steps="1. Nhập user đúng\n2. Nhập pass sai\n3. Click Login",
#         input_data="user: admin / pass: wrong",
#         expected="Hiện thông báo lỗi đỏ",
#         actual="Không hiện thông báo gì cả",
#         status="FAIL",
#         priority="High",
#         remarks="Bug #405: Hệ thống không phản hồi khi sai pass"
#     )
#
#     # Thêm Test Case 3: BLOCKED
#     reporter.add_result(
#         case_id="TC-003",
#         module="Thanh toán",
#         test_name="Thanh toán qua VISA",
#         steps="1. Chọn VISA\n2. Nhập thẻ",
#         input_data="Thẻ Visa 4222...",
#         expected="Thanh toán thành công",
#         actual="Nút thanh toán bị ẩn",
#         status="BLOCKED",
#         priority="Critical",
#         remarks="Server thanh toán đang bảo trì"
#     )
#
#     reporter.save_report()