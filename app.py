import os
import json
import time
import base64
import cv2
import numpy as np
from datetime import datetime
from flask import Flask, render_template, request, jsonify, redirect, url_for, session
from flask_socketio import SocketIO, emit
from ultralytics import YOLO
from flask_sqlalchemy import SQLAlchemy
import torch

app = Flask(__name__)
app.secret_key = 'ai_vision_secret_key_demo'

# --- 1. CẤU HÌNH DATABASE & THƯ MỤC ẢNH ---
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///database.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
UPLOAD_FOLDER = 'static/uploads'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

db = SQLAlchemy(app)
# async_mode='threading' giúp chạy mượt trên Windows
socketio = SocketIO(app, cors_allowed_origins="*", async_mode='threading')


# --- 2. ĐỊNH NGHĨA MODEL ---
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(100), unique=True, nullable=False)
    password = db.Column(db.String(100), nullable=False)


class History(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    timestamp = db.Column(db.String(50))
    image_path = db.Column(db.String(200))
    original_path = db.Column(db.String(200))
    source = db.Column(db.String(50))
    name = db.Column(db.String(100))
    results_json = db.Column(db.Text)


class Target(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    min_qty = db.Column(db.Integer, nullable=False)


with app.app_context():
    db.create_all()

# --- 3. CẤU HÌNH AI ---
device = 'cuda' if torch.cuda.is_available() else 'cpu'
print(f">>> Đang chạy trên thiết bị: {device.upper()}")

# Lấy đường dẫn tuyệt đối để tránh lỗi không tìm thấy file
BASE_DIR = os.path.abspath(os.path.dirname(__file__))
model_path = os.path.join(BASE_DIR, 'best.pt')

try:
    model = YOLO(model_path)
    model.to(device)
    print(">>> Model custom đã sẵn sàng!")
except:
    print(">>> Không tìm thấy best.pt, dùng yolov8n.pt")
    model = YOLO('yolov8n.pt')
    model.to(device)

# --- BIẾN TOÀN CỤC ---
history_db = []
users_db = {'admin': '123456'}

# 1. Biến lưu trạng thái lần trước để so sánh sự thay đổi
last_detected_state = {}

# 2. Thời gian lưu lần cuối
last_save_time = 0

# 3. CẤU HÌNH THÔNG MINH
MIN_COOLDOWN = 3
PERIODIC_INTERVAL = 3600

# --- 4. HÀM HỖ TRỢ ---
def save_image_to_file(img_cv2, prefix):
    filename = f"{prefix}_{int(time.time())}_{np.random.randint(100, 999)}.jpg"
    filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
    cv2.imwrite(filepath, img_cv2)
    return f"/{UPLOAD_FOLDER}/{filename}"


# --- 5. ROUTES ---
@app.route('/')
def index():
    if 'username' not in session: return redirect(url_for('login_page'))
    return render_template('index.html', username=session['username'])


@app.route('/camera')
def camera_page():
    if 'username' not in session: return redirect(url_for('login_page'))
    return render_template('camera.html', username=session['username'])


@app.route('/statistics')
def statistics_page():
    if 'username' not in session: return redirect(url_for('login_page'))
    return render_template('statistics.html', username=session['username'])


@app.route('/login', methods=['GET', 'POST'])
def login_page():
    if 'username' in session: return redirect(url_for('index'))
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        action = request.form.get('action')

        if action == 'register':
            if User.query.filter_by(username=username).first():
                return render_template('login.html', error="Tài khoản đã tồn tại!")
            new_user = User(username=username, password=password)
            db.session.add(new_user)
            db.session.commit()
            return render_template('login.html', success="Đăng ký thành công!")

        elif action == 'login':
            user = User.query.filter_by(username=username, password=password).first()
            if user:
                session['username'] = user.username
                return redirect(url_for('index'))
            else:
                return render_template('login.html', error="Sai tài khoản/mật khẩu!")
    return render_template('login.html')


@app.route('/logout')
def logout():
    session.pop('username', None)
    return redirect(url_for('login_page'))


# --- API ---
@app.route('/api/history')
def get_history():
    records = History.query.order_by(History.id.desc()).all()
    data = []
    for r in records:
        data.append({
            'id': r.id,
            'timestamp': r.timestamp,
            'image': r.image_path,
            'image_original': r.original_path,
            'source': r.source,
            'name': r.name,
            'results': json.loads(r.results_json)
        })
    return jsonify(data)


@app.route('/api/delete_history', methods=['POST'])
def delete_history():
    try:
        item_id = request.get_json().get('id')
        record = History.query.get(item_id)
        if record:
            db.session.delete(record)
            db.session.commit()
            return jsonify({'status': 'success'})
        return jsonify({'status': 'error'})
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)})


@app.route('/api/targets', methods=['GET', 'POST'])
def manage_targets():
    if request.method == 'GET':
        targets = Target.query.all()
        return jsonify([{'id': t.id, 'name': t.name, 'qty': t.min_qty} for t in targets])
    if request.method == 'POST':
        data = request.get_json()
        name = data.get('name')
        qty = int(data.get('qty'))
        target = Target.query.filter_by(name=name).first()
        if target:
            target.min_qty = qty
        else:
            db.session.add(Target(name=name, min_qty=qty))
        db.session.commit()
        return jsonify({'status': 'success'})


@app.route('/api/delete_target', methods=['POST'])
def delete_target():
    id = request.get_json().get('id')
    Target.query.filter_by(id=id).delete()
    db.session.commit()
    return jsonify({'status': 'success'})


@app.route('/predict', methods=['POST'])
def predict():
    try:
        file = request.files['file']
        file_bytes = np.frombuffer(file.read(), np.uint8)
        img = cv2.imdecode(file_bytes, cv2.IMREAD_COLOR)

        path_orig = save_image_to_file(img, "Upload_Orig")
        results = model(img, conf=0.4)
        annotated_img = results[0].plot()
        path_ann = save_image_to_file(annotated_img, "Upload_Ann")

        detected_counts = {}
        for result in results:
            for box in result.boxes:
                cls = model.names[int(box.cls[0])]
                detected_counts[cls] = detected_counts.get(cls, 0) + 1

        final_results = [{'name': k, 'qty': v} for k, v in detected_counts.items()]
        if not final_results: final_results = [{'name': 'Không phát hiện', 'qty': 0}]

        new_record = History(
            timestamp=datetime.now().strftime("%d/%m/%Y %H:%M:%S"),
            image_path=path_ann,
            original_path=path_orig,
            source="Upload",
            name=file.filename,
            results_json=json.dumps(final_results)
        )
        db.session.add(new_record)
        db.session.commit()

        return jsonify({'status': 'success', 'image_with_box': path_ann, 'details': final_results})
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)})


# --- SOCKET IO ---
@socketio.on('send_frame')
def handle_frame(data):
    global last_save_time,last_detected_state
    try:
        # 1. Giải mã ảnh
        image_data = data['image']
        encoded_data = image_data.split(',')[1]
        nparr = np.frombuffer(base64.b64decode(encoded_data), np.uint8)
        img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)

        # 2. Chạy AI
        results = model(img, conf=0.5, verbose=False)

        # 3. Xử lý dữ liệu (Đếm + Lấy tọa độ khung)
        detected_counts = {}
        boxes_data = []  # Danh sách chứa tọa độ để gửi về Client

        for result in results:
            for box in result.boxes:
                # A. Lấy tên class để đếm
                class_id = int(box.cls[0])
                class_name = model.names[class_id]
                detected_counts[class_name] = detected_counts.get(class_name, 0) + 1

                # B. Lấy tọa độ khung [x1, y1, x2, y2]
                # box.xyxy[0] trả về tensor, cần chuyển sang list python
                coords = box.xyxy[0].tolist()

                boxes_data.append({
                    'coords': coords,  # [x1, y1, x2, y2]
                    'label': f"{class_name} ({box.conf[0]:.2f})"  # VD: person 0.95
                })

        # 4. Kiểm tra cảnh báo (Logic cũ)
        targets = Target.query.all()
        is_alert = False
        for t in targets:
            if detected_counts.get(t.name, 0) < t.min_qty:
                is_alert = True
                break

        # 5. GỬI VỀ CLIENT (Gửi kèm boxes_data)
        emit('update_detections', {
            'counts': detected_counts,
            'is_alert': is_alert,
            'boxes': boxes_data  # <--- DỮ LIỆU MỚI: Tọa độ khung
        })

        # 6. Tự động lưu
        # Lấy thời gian hiện tại
        now = time.time()

        # Điều kiện 1: Có sự thay đổi về vật thể (Thêm vào hoặc Mất đi)
        # So sánh dictionary hiện tại với lần trước
        has_changed = (detected_counts != last_detected_state)

        # Điều kiện 2: Đã quá lâu chưa chụp (Định kỳ 1 tiếng)
        is_periodic_time = (now - last_save_time > PERIODIC_INTERVAL)

        # Điều kiện 3: Phải qua thời gian hồi chiêu (3s) để tránh chụp liên thanh khi AI không ổn định
        is_cooldown_passed = (now - last_save_time > MIN_COOLDOWN)

        # ==> QUYẾT ĐỊNH CUỐI CÙNG
        if (has_changed or is_periodic_time) and is_cooldown_passed:
            # Cập nhật trạng thái mới để so sánh cho lần sau
            last_detected_state = detected_counts.copy()
            last_save_time = now

            # --- TIẾN HÀNH LƯU (Code cũ) ---
            path_orig = save_image_to_file(img, "Smart_Orig")
            annotated_img = results[0].plot()
            path_ann = save_image_to_file(annotated_img, "Smart_Ann")

            final_results = [{'name': k, 'qty': v} for k, v in detected_counts.items()]

            # Xác định lý do lưu để in ra log (Debug)
            reason = "THAY ĐỔI" if has_changed else "ĐỊNH KỲ"

            new_record = History(
                timestamp=datetime.now().strftime("%d/%m/%Y %H:%M:%S"),
                image_path=path_ann,
                original_path=path_orig,
                source=f"Camera ({reason})",  # Ghi rõ nguồn là do thay đổi hay định kỳ
                name=f"Cam_{int(now)}.jpg",
                results_json=json.dumps(final_results)
            )
            db.session.add(new_record)
            db.session.commit()
            print(f">>> [SMART SAVE] Đã lưu ảnh. Lý do: {reason}. ID: {new_record.id}")

    except Exception as e:
        print("Socket Error:", e)


if __name__ == '__main__':
    socketio.run(app, debug=True, allow_unsafe_werkzeug=True)