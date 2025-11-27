import unittest
import json
import io
import os
from unittest.mock import patch, MagicMock
from app import app, db, User, Target, History


class AIAppTestCase(unittest.TestCase):

    # --- 1. THIẾT LẬP MÔI TRƯỜNG TEST ---
    def setUp(self):
        """Chạy trước mỗi bài test"""
        print(f"\n{'=' * 60}")
        print(f"🚀 START: Đang chạy test case [{self._testMethodName}]...")

        app.config['TESTING'] = True
        app.config['WTF_CSRF_ENABLED'] = False
        app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
        app.config['UPLOAD_FOLDER'] = 'static/test_uploads'

        # Đảm bảo thư mục upload tồn tại
        if not os.path.exists(app.config['UPLOAD_FOLDER']):
            os.makedirs(app.config['UPLOAD_FOLDER'])

        self.app = app.test_client()
        self.app_context = app.app_context()
        self.app_context.push()

        db.create_all()
        user = User(username='admin', password='123')
        db.session.add(user)
        db.session.commit()
        print("   [Info] Đã khởi tạo Database ảo và User mẫu.")

    def tearDown(self):
        """Chạy sau khi test xong"""
        db.session.remove()
        db.drop_all()
        self.app_context.pop()
        print(f"🏁 END: Hoàn thành test case [{self._testMethodName}].")

    # =================================================================
    # NHÓM 1: KIỂM THỬ XÁC THỰC (LOGIN/LOGOUT)
    # =================================================================

    def test_login_success(self):
        """Test đăng nhập đúng tài khoản"""
        print("   [Step 1] Gửi yêu cầu đăng nhập với user='admin', pass='123'...")
        response = self.app.post('/login', data=dict(
            username='admin',
            password='123',
            action='login'
        ), follow_redirects=True)

        print("   [Step 2] Kiểm tra phản hồi từ server...")
        self.assertIn(b'AI Vision Pro', response.data)
        print("   ✅ KẾT QUẢ: Đăng nhập thành công, đã thấy trang chủ.")

    def test_login_fail(self):
        """Test đăng nhập sai mật khẩu"""
        print("   [Step 1] Gửi yêu cầu đăng nhập với mật khẩu sai...")
        response = self.app.post('/login', data=dict(
            username='admin',
            password='wrongpass',
            action='login'
        ), follow_redirects=True)

        print("   [Step 2] Kiểm tra thông báo lỗi...")
        self.assertIn(b'Sai', response.data)
        print("   ✅ KẾT QUẢ: Hệ thống đã chặn đăng nhập sai.")

    def test_register_new_user(self):
        """Test đăng ký tài khoản mới"""
        print("   [Step 1] Đăng ký user mới tên 'newuser'...")
        response = self.app.post('/login', data=dict(
            username='newuser',
            password='456',
            action='register'
        ), follow_redirects=True)

        print("   [Step 2] Kiểm tra Database xem user đã được tạo chưa...")
        user = User.query.filter_by(username='newuser').first()
        self.assertIsNotNone(user)
        self.assertIn(b'th\xc3\xa0nh c\xc3\xb4ng', response.data)
        print("   ✅ KẾT QUẢ: Đăng ký thành công, user đã có trong DB.")

    def test_protected_routes(self):
        """Test bảo mật trang chủ"""
        print("   [Step 1] Đăng xuất khỏi hệ thống...")
        self.app.get('/logout', follow_redirects=True)

        print("   [Step 2] Cố tình truy cập trang chủ '/' mà không đăng nhập...")
        response = self.app.get('/', follow_redirects=True)

        print("   [Step 3] Kiểm tra xem có bị chuyển về trang Login không...")
        self.assertIn(b'name="username"', response.data)
        print("   ✅ KẾT QUẢ: Bảo mật tốt, đã bị chuyển hướng về Login.")

    # =================================================================
    # NHÓM 2: KIỂM THỬ API CÀI ĐẶT (TARGETS)
    # =================================================================

    def test_add_target(self):
        """Test thêm mục tiêu giám sát"""
        print("   [Step 1] Gửi JSON thêm mục tiêu 'laptop', số lượng=2...")
        response = self.app.post('/api/targets',
                                 data=json.dumps({'name': 'laptop', 'qty': 2}),
                                 content_type='application/json')

        self.assertEqual(response.status_code, 200)

        print("   [Step 2] Truy vấn Database bảng Target...")
        target = Target.query.filter_by(name='laptop').first()
        self.assertIsNotNone(target)
        self.assertEqual(target.min_qty, 2)
        print("   ✅ KẾT QUẢ: API hoạt động đúng, dữ liệu đã lưu.")

    def test_delete_target(self):
        """Test xóa mục tiêu"""
        print("   [Step 1] Tạo sẵn mục tiêu 'phone' trong DB...")
        t = Target(name='phone', min_qty=1)
        db.session.add(t)
        db.session.commit()

        print("   [Step 2] Gọi API xóa mục tiêu này...")
        self.app.post('/api/delete_target',
                      data=json.dumps({'id': t.id}),
                      content_type='application/json')

        print("   [Step 3] Kiểm tra lại DB xem còn không...")
        check = Target.query.filter_by(name='phone').first()
        self.assertIsNone(check)
        print("   ✅ KẾT QUẢ: Đã xóa thành công khỏi DB.")

    # =================================================================
    # NHÓM 3: KIỂM THỬ API UPLOAD & AI (MOCKING AI)
    # =================================================================

    @patch('app.model')
    @patch('app.save_image_to_file')
    def test_upload_predict(self, mock_save_file, mock_ai_model):
        """Test upload ảnh THẬT và nhận diện"""
        print("   [Info] Đang giả lập (Mock) Model AI và File System...")

        # 1. Cấu hình AI giả
        mock_result = MagicMock()
        mock_result.plot.return_value = [[0, 0, 0]]
        mock_box = MagicMock()
        mock_box.cls = [0]
        mock_result.boxes = [mock_box]

        mock_ai_model.return_value = [mock_result]
        mock_ai_model.names = {0: 'person'}
        mock_save_file.return_value = "/static/uploads/result_fake.jpg"

        # 2. LẤY ẢNH THẬT TỪ THƯ MỤC static/test_uploads
        # Lấy đường dẫn gốc của dự án
        base_dir = os.path.abspath(os.path.dirname(__file__))
        image_name = "ban-phim-van-phong-1.jpg"
        image_path = os.path.join(base_dir, "static", "test_uploads", image_name)

        # Kiểm tra xem ảnh có tồn tại không
        if not os.path.exists(image_path):
            print(f"   ❌ LỖI: Không tìm thấy ảnh test tại: {image_path}")
            # Nếu không có ảnh thật, ta tạo tạm một file giả để test không bị crash
            with open(image_path, 'wb') as f:
                f.write(b'fake_image_content')
            print("   ⚠️ Đã tạo tạm file ảnh giả để test tiếp tục.")

        print(f"   [Step 1] Đọc file ảnh từ đĩa: {image_name}")

        # Mở file ảnh thật và gửi lên
        with open(image_path, 'rb') as img_file:
            data = {
                'file': (img_file, image_name)
            }
            print("   [Step 2] Gửi Request POST tới API '/predict'...")
            response = self.app.post('/predict', data=data, content_type='multipart/form-data')
            json_data = response.get_json()

        print("   [Step 3] Kiểm tra kết quả trả về từ AI...")
        self.assertEqual(json_data['status'], 'success')
        # Vì ta đang Mock AI nên kết quả trả về vẫn là 'person' (do ta cài đặt ở trên)
        # Dù ảnh thật là bàn phím nhưng AI giả vẫn bảo là người -> Đây là Unit Test logic code, không phải test độ chính xác model
        self.assertEqual(json_data['details'][0]['name'], 'person')
        print(f"      -> Code xử lý thành công, AI giả trả về: {json_data['details'][0]['name']}")

        print("   [Step 4] Kiểm tra Database History...")
        history = History.query.first()
        self.assertIsNotNone(history)
        self.assertEqual(history.source, 'Upload')
        self.assertEqual(history.name, image_name)  # Kiểm tra tên file lưu có đúng không
        print("   ✅ KẾT QUẢ: Upload ảnh thật thành công, Logic xử lý đúng.")

    # =================================================================
    # NHÓM 4: KIỂM THỬ SOCKETIO (CAMERA REAL-TIME)
    # =================================================================

    @patch('app.model')
    def test_socket_camera_process(self, mock_ai_model):
        """Test xử lý luồng camera qua Socket"""
        print("   [Info] Khởi tạo SocketIO Test Client...")
        from app import socketio

        # Cấu hình AI giả
        mock_result = MagicMock()
        mock_box = MagicMock()
        mock_box.cls = [0]
        mock_result.boxes = [mock_box]
        mock_ai_model.return_value = [mock_result]
        mock_ai_model.names = {0: 'person'}

        socket_client = socketio.test_client(app)

        print("   [Step 1] Giả lập gửi 1 khung hình (Base64) qua Socket...")
        fake_base64_img = "data:image/jpeg;base64,SUQzBAAAAAAAI1RTU0UAAAAPAAADTGF2ZjU4LjI5LjEwMAAAAAAAAAAAAAAA"

        with patch('cv2.imdecode') as mock_decode:
            mock_decode.return_value = [[0]]
            socket_client.emit('send_frame', {'image': fake_base64_img})

        print("   [Step 2] Lắng nghe phản hồi 'update_detections' từ Server...")
        received = socket_client.get_received()

        event_found = False
        for message in received:
            if message['name'] == 'update_detections':
                data = message['args'][0]
                print(f"      -> Server trả về: {data['counts']}")
                self.assertEqual(data['counts']['person'], 1)
                event_found = True
                break

        self.assertTrue(event_found, "Lỗi: Server không phản hồi sự kiện!")
        print("   ✅ KẾT QUẢ: Luồng xử lý Camera Real-time hoạt động tốt.")


if __name__ == '__main__':
    unittest.main()