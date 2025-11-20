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

# --- 1. THƯ VIỆN DATABASE ---
from flask_sqlalchemy import SQLAlchemy

app = Flask(__name__)
app.secret_key = 'ai_vision_secret_key_demo'

# --- 2. CẤU HÌNH DATABASE & THƯ MỤC ẢNH ---
# File database sẽ tên là 'database.db' nằm cùng thư mục app.py
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///database.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
UPLOAD_FOLDER = 'static/uploads'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# Tạo thư mục lưu ảnh nếu chưa có
if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

db = SQLAlchemy(app)
socketio = SocketIO(app, cors_allowed_origins="*", async_mode='threading')


# --- 1.1. CẬP NHẬT DATABASE MODEL ---
class Target(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False) # Tên vật thể (VD: laptop)
    min_qty = db.Column(db.Integer, nullable=False)  # Số lượng tối thiểu cần có

# Tạo lại DB để cập nhật bảng mới (Chỉ chạy dòng này 1 lần hoặc xóa db cũ đi để tạo lại)
with app.app_context():
    db.create_all()

# --- 3. ĐỊNH NGHĨA BẢNG DỮ LIỆU (MODEL) ---

# Bảng Tài Khoản
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(100), unique=True, nullable=False)
    password = db.Column(db.String(100), nullable=False)


# Bảng Lịch sử
class History(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    timestamp = db.Column(db.String(50))
    # Lưu đường dẫn file ảnh (VD: /static/uploads/img_123.jpg)
    image_path = db.Column(db.String(200))
    original_path = db.Column(db.String(200))
    source = db.Column(db.String(50))  # Camera hoặc Upload
    name = db.Column(db.String(100))
    # Lưu kết quả dạng chuỗi JSON vì SQLite không có kiểu List/Array
    results_json = db.Column(db.Text)


# Tạo Database ngay khi chạy code
with app.app_context():
    db.create_all()

# --- CẤU HÌNH AI ---
print(">>> Đang tải model...")
try:
    model = YOLO('best.pt')
except:
    model = YOLO('yolov8n.pt')

last_save_time = 0
SAVE_COOLDOWN = 3


# --- HÀM HỖ TRỢ LƯU ẢNH RA FILE ---
def save_image_to_file(img_cv2, prefix):
    """Lưu ảnh OpenCV ra file .jpg và trả về đường dẫn web"""
    filename = f"{prefix}_{int(time.time())}_{np.random.randint(100, 999)}.jpg"
    filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
    cv2.imwrite(filepath, img_cv2)
    # Trả về đường dẫn để Frontend hiển thị (VD: /static/uploads/abc.jpg)
    return f"/{UPLOAD_FOLDER}/{filename}"


# --- CÁC ROUTE GIAO DIỆN ---
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


# --- XỬ LÝ ĐĂNG NHẬP / ĐĂNG KÝ (DÙNG DB THẬT) ---
@app.route('/login', methods=['GET', 'POST'])
def login_page():
    if 'username' in session: return redirect(url_for('index'))

    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        action = request.form.get('action')

        if action == 'register':
            # Kiểm tra tồn tại
            existing_user = User.query.filter_by(username=username).first()
            if existing_user:
                return render_template('login.html', error="Tài khoản đã tồn tại!")

            # Tạo user mới
            new_user = User(username=username, password=password)
            db.session.add(new_user)
            db.session.commit()
            return render_template('login.html', success="Đăng ký thành công!")

        elif action == 'login':
            # Tìm user trong DB
            user = User.query.filter_by(username=username, password=password).first()
            if user:
                session['username'] = user.username
                return redirect(url_for('index'))
            else:
                return render_template('login.html', error="Sai tài khoản hoặc mật khẩu!")

    return render_template('login.html')


@app.route('/logout')
def logout():
    session.pop('username', None)
    return redirect(url_for('login_page'))


# --- API LỊCH SỬ (LẤY TỪ DB) ---
@app.route('/api/history')
def get_history():
    # Lấy tất cả bản ghi, sắp xếp mới nhất lên đầu
    records = History.query.order_by(History.id.desc()).all()

    data = []
    for r in records:
        data.append({
            'id': r.id,
            'timestamp': r.timestamp,
            'image': r.image_path,  # Đường dẫn ảnh có khung
            'image_original': r.original_path,  # Đường dẫn ảnh gốc
            'source': r.source,
            'name': r.name,
            'results': json.loads(r.results_json)  # Giải mã chuỗi JSON thành List
        })
    return jsonify(data)


@app.route('/api/delete_history', methods=['POST'])
def delete_history():
    try:
        item_id = request.get_json().get('id')
        record = History.query.get(item_id)
        if record:
            # (Tùy chọn) Xóa file ảnh trên ổ cứng để tiết kiệm dung lượng
            # os.remove(record.image_path.lstrip('/')) ...

            db.session.delete(record)
            db.session.commit()
            return jsonify({'status': 'success'})
        return jsonify({'status': 'error', 'message': 'Not found'})
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)})


# --- UPLOAD ẢNH ---
@app.route('/predict', methods=['POST'])
def predict():
    try:
        file = request.files['file']
        file_bytes = np.frombuffer(file.read(), np.uint8)
        img = cv2.imdecode(file_bytes, cv2.IMREAD_COLOR)
        if img is None: return jsonify({'status': 'error'})

        # 1. Lưu ảnh gốc ra file
        path_orig = save_image_to_file(img, "Upload_Orig")

        # 2. AI xử lý
        results = model(img, conf=0.4)
        annotated_img = results[0].plot()

        # 3. Lưu ảnh vẽ khung ra file
        path_ann = save_image_to_file(annotated_img, "Upload_Ann")

        # 4. Đếm số lượng
        detected_counts = {}
        for result in results:
            for box in result.boxes:
                cls = model.names[int(box.cls[0])]
                detected_counts[cls] = detected_counts.get(cls, 0) + 1

        final_results = [{'name': k, 'qty': v} for k, v in detected_counts.items()]
        if not final_results: final_results = [{'name': 'Không phát hiện', 'qty': 0}]

        # 5. LƯU VÀO DB
        new_record = History(
            timestamp=datetime.now().strftime("%d/%m/%Y %H:%M:%S"),
            image_path=path_ann,
            original_path=path_orig,
            source="Upload",
            name=file.filename,
            results_json=json.dumps(final_results)  # Chuyển List thành chuỗi để lưu
        )
        db.session.add(new_record)
        db.session.commit()

        return jsonify({'status': 'success', 'image_with_box': path_ann, 'details': final_results})

    except Exception as e:
        print(e)
        return jsonify({'status': 'error', 'message': str(e)})


# --- CAMERA REAL-TIME ---
@socketio.on('send_frame')
def handle_frame(data):
    global last_save_time
    try:
        # Decode ảnh
        encoded_data = data['image'].split(',')[1]
        nparr = np.frombuffer(base64.b64decode(encoded_data), np.uint8)
        img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)

        # AI
        results = model(img, conf=0.5, verbose=False)
        detected_counts = {}
        for result in results:
            for box in result.boxes:
                cls = model.names[int(box.cls[0])]
                detected_counts[cls] = detected_counts.get(cls, 0) + 1

        emit('update_detections', detected_counts)

        image_data = data['image']
        encoded_data = image_data.split(',')[1]
        nparr = np.frombuffer(base64.b64decode(encoded_data), np.uint8)
        img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
        results = model(img, conf=0.5, verbose=False)

        detected_counts = {}
        for result in results:
            for box in result.boxes:
                cls = model.names[int(box.cls[0])]
                detected_counts[cls] = detected_counts.get(cls, 0) + 1


        # --- LOGIC MỚI: SO SÁNH VỚI MỤC TIÊU (TARGETS) ---
        # Lấy danh sách mục tiêu từ DB
        # Lưu ý: Truy vấn DB trong vòng lặp real-time có thể chậm,
        # thực tế nên cache lại biến này ra biến toàn cục, nhưng để đơn giản ta query luôn.
        targets = Target.query.all()
        is_alert = False

        for t in targets:
            # Nếu số lượng phát hiện < số lượng yêu cầu
            current_qty = detected_counts.get(t.name, 0)
            if current_qty < t.min_qty:
                is_alert = True
                break # Chỉ cần 1 món thiếu là báo động ngay

        # Gửi kết quả kèm trạng thái báo động
        emit('update_detections', {
            'counts': detected_counts,
            'is_alert': is_alert
        })

        # Tự động lưu
        if detected_counts and (time.time() - last_save_time > SAVE_COOLDOWN):
            last_save_time = time.time()

            # Lưu file ảnh
            path_orig = save_image_to_file(img, "Auto_Orig")
            annotated_img = results[0].plot()
            path_ann = save_image_to_file(annotated_img, "Auto_Ann")

            final_results = [{'name': k, 'qty': v} for k, v in detected_counts.items()]

            # Lưu DB
            new_record = History(
                timestamp=datetime.now().strftime("%d/%m/%Y %H:%M:%S"),
                image_path=path_ann,
                original_path=path_orig,
                source="Camera (Auto)",
                name=f"Cam_{int(time.time())}.jpg",
                results_json=json.dumps(final_results)
            )
            db.session.add(new_record)
            db.session.commit()
            print(f">>> [DB SAVE] Đã lưu ID: {new_record.id}")


    except Exception as e:
        print("Socket Error:", e)

# --- API CHO CÀI ĐẶT (SETTINGS) ---
@app.route('/api/targets', methods=['GET', 'POST'])
def manage_targets():
    if request.method == 'GET':
        targets = Target.query.all()
        return jsonify([{'id': t.id, 'name': t.name, 'qty': t.min_qty} for t in targets])

    if request.method == 'POST':
        data = request.get_json()
        # Xóa cũ thay mới hoặc thêm mới tùy logic, ở đây làm đơn giản là thêm/sửa
        name = data.get('name')
        qty = int(data.get('qty'))

        # Kiểm tra xem đã có target tên này chưa
        target = Target.query.filter_by(name=name).first()
        if target:
            target.min_qty = qty  # Cập nhật
        else:
            new_target = Target(name=name, min_qty=qty)
            db.session.add(new_target)

        db.session.commit()
        return jsonify({'status': 'success'})


@app.route('/api/delete_target', methods=['POST'])
def delete_target():
    id = request.get_json().get('id')
    Target.query.filter_by(id=id).delete()
    db.session.commit()
    return jsonify({'status': 'success'})


if __name__ == '__main__':
    socketio.run(app, debug=True, allow_unsafe_werkzeug=True)