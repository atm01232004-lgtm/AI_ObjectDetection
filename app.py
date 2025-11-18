from flask import Flask, render_template, request, jsonify, redirect, url_for, session
from flask_socketio import SocketIO, emit
import base64
import numpy as np
import cv2
from ultralytics import YOLO
from datetime import datetime
import time

app = Flask(__name__)
app.secret_key = 'ai_vision_secret_key_demo'

# --- CẤU HÌNH SOCKET.IO ---
# async_mode='threading' giúp chạy mượt trên Windows/PyCharm
socketio = SocketIO(app, cors_allowed_origins="*", async_mode='threading')

# --- CẤU HÌNH AI ---
print(">>> Đang tải model best.pt...")
try:
    model = YOLO('best.pt')
    print(">>> Model custom đã sẵn sàng!")
except Exception as e:
    print(f">>> LỖI: Không tìm thấy 'best.pt'. Đang dùng 'yolov8n.pt'. Lỗi: {e}")
    model = YOLO('yolov8n.pt')

# --- BIẾN TOÀN CỤC ---
history_db = []
users_db = {'admin': '123456'}
last_save_time = 0
SAVE_COOLDOWN = 3  # Thời gian chờ giữa các lần tự động lưu (giây)


# --- CÁC ROUTE GIAO DIỆN (UI) ---

@app.route('/')
def index():
    if 'username' not in session:
        return redirect(url_for('login_page'))
    return render_template('index.html', username=session['username'])


@app.route('/login', methods=['GET', 'POST'])
def login_page():
    if 'username' in session:
        return redirect(url_for('index'))
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        action = request.form.get('action')

        if action == 'register':
            users_db[username] = password
            return render_template('login.html', success="Đăng ký thành công!")
        elif action == 'login':
            if username in users_db and users_db[username] == password:
                session['username'] = username
                return redirect(url_for('index'))
            else:
                return render_template('login.html', error="Sai tài khoản/mật khẩu!")
    return render_template('login.html')


@app.route('/camera')
def camera_page():
    if 'username' not in session:
        return redirect(url_for('login_page'))
    return render_template('camera.html')


@app.route('/statistics')
def statistics_page():
    if 'username' not in session:
        return redirect(url_for('login_page'))
    return render_template('statistics.html')


@app.route('/logout')
def logout():
    session.pop('username', None)
    return redirect(url_for('login_page'))


# --- CÁC ROUTE API (XỬ LÝ DỮ LIỆU) ---

@app.route('/api/history')
def get_history():
    # Trả về danh sách đảo ngược (Mới nhất lên đầu)
    return jsonify(history_db[::-1])


@app.route('/api/delete_history', methods=['POST'])
def delete_history():
    try:
        data = request.get_json()
        item_id = data.get('id')
        global history_db
        history_db = [item for item in history_db if item['id'] != item_id]
        return jsonify({'status': 'success'})
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)})


# --- CHỨC NĂNG 1: UPLOAD ẢNH (HTTP POST) ---
@app.route('/predict', methods=['POST'])
def predict():
    try:
        if 'file' not in request.files:
            return jsonify({'status': 'error', 'message': 'Chưa chọn file'})

        file = request.files['file']

        # Đọc ảnh
        file_bytes = np.frombuffer(file.read(), np.uint8)
        img = cv2.imdecode(file_bytes, cv2.IMREAD_COLOR)
        if img is None:
            return jsonify({'status': 'error', 'message': 'File lỗi'})

        # 1. TẠO ẢNH GỐC (Để xem lại)
        img_original = img.copy()
        _, buffer_orig = cv2.imencode('.jpg', img_original)
        base64_original = "data:image/jpeg;base64," + base64.b64encode(buffer_orig).decode('utf-8')

        # 2. CHẠY AI VÀ TẠO ẢNH VẼ KHUNG
        results = model(img, conf=0.4)
        annotated_img = results[0].plot()

        _, buffer_ann = cv2.imencode('.jpg', annotated_img)
        base64_annotated = "data:image/jpeg;base64," + base64.b64encode(buffer_ann).decode('utf-8')

        # 3. Đếm số lượng
        detected_counts = {}
        for result in results:
            for box in result.boxes:
                class_name = model.names[int(box.cls[0])]
                detected_counts[class_name] = detected_counts.get(class_name, 0) + 1

        final_results = [{'name': k, 'qty': v} for k, v in detected_counts.items()]
        if not final_results: final_results = [{'name': 'Không phát hiện', 'qty': 0}]

        # 4. LƯU VÀO LỊCH SỬ
        record = {
            'id': int(datetime.now().timestamp()),
            'timestamp': datetime.now().strftime("%d/%m/%Y %H:%M:%S"),
            'image': base64_annotated,  # Ảnh có khung
            'image_original': base64_original,  # Ảnh gốc
            'source': 'Upload',
            'name': file.filename,
            'ip_cam': 'N/A',
            'office': 'N/A',
            'results': final_results
        }
        history_db.append(record)

        return jsonify({
            'status': 'success',
            'image_with_box': base64_annotated,
            'details': final_results
        })

    except Exception as e:
        print("Lỗi Upload:", e)
        return jsonify({'status': 'error', 'message': str(e)})


# --- CHỨC NĂNG 2: CAMERA REAL-TIME (SOCKET.IO) ---
@socketio.on('send_frame')
def handle_frame(data):
    global last_save_time

    try:
        # Giải mã ảnh từ Client
        image_data = data['image']
        encoded_data = image_data.split(',')[1]
        nparr = np.frombuffer(base64.b64decode(encoded_data), np.uint8)
        img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)

        # Chạy AI
        results = model(img, conf=0.5, verbose=False)

        # Đếm số lượng để gửi về giao diện ngay lập tức
        detected_counts = {}
        for result in results:
            for box in result.boxes:
                class_name = model.names[int(box.cls[0])]
                detected_counts[class_name] = detected_counts.get(class_name, 0) + 1

        emit('update_detections', detected_counts)

        # --- LOGIC TỰ ĐỘNG LƯU ---
        # Chỉ lưu khi: Có vật thể VÀ đã qua thời gian Cooldown (3s)
        if detected_counts and (time.time() - last_save_time > SAVE_COOLDOWN):
            last_save_time = time.time()

            # 1. TẠO ẢNH GỐC (QUAN TRỌNG: Sửa lỗi thiếu ảnh gốc)
            # img đang là ảnh sạch, lưu nó lại ngay
            _, buffer_orig = cv2.imencode('.jpg', img)
            base64_original = "data:image/jpeg;base64," + base64.b64encode(buffer_orig).decode('utf-8')

            # 2. TẠO ẢNH VẼ KHUNG
            annotated_img = results[0].plot()
            _, buffer_ann = cv2.imencode('.jpg', annotated_img)
            base64_annotated = "data:image/jpeg;base64," + base64.b64encode(buffer_ann).decode('utf-8')

            # 3. Tạo danh sách kết quả
            final_results = [{'name': k, 'qty': v} for k, v in detected_counts.items()]

            # 4. Lưu vào Lịch sử
            record = {
                'id': int(time.time()),
                'timestamp': datetime.now().strftime("%d/%m/%Y %H:%M:%S"),
                'image': base64_annotated,  # Ảnh có khung
                'image_original': base64_original,  # Ảnh gốc (Đã thêm mới)
                'source': 'Camera (Auto)',
                'name': f"AutoCap_{datetime.now().strftime('%H%M%S')}.jpg",
                'ip_cam': '192.168.1.105',
                'office': 'Khu Vực A - Kho 01',
                'results': final_results
            }
            history_db.append(record)
            print(f">>> [AUTO SAVE] Đã lưu: {record['name']}")

    except Exception as e:
        print("Socket Error:", e)


# --- CHẠY SERVER ---
if __name__ == '__main__':
    # Dùng socketio.run để đảm bảo WebSocket hoạt động tốt nhất
    socketio.run(app, debug=True, allow_unsafe_werkzeug=True)