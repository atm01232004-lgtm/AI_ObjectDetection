from flask import Flask, render_template, request, jsonify, redirect, url_for, session
import base64
import numpy as np
import cv2
from ultralytics import YOLO
from datetime import datetime


app = Flask(__name__)
app.secret_key = 'ai_vision_secret_key_demo'

# --- CẤU HÌNH AI ---
# Tải model YOLOv8 bản Nano (nhẹ nhất).
# Lần đầu chạy nó sẽ tự tải file 'yolov8n.pt' về máy bạn (khoảng 6MB).
print(">>> Đang tải model AI...")
model = YOLO('yolov8n.pt')
print(">>> Model đã sẵn sàng!")

# Database giả
users_db = {'admin': '123456'}


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


@app.route('/logout')
def logout():
    session.pop('username', None)
    return redirect(url_for('login_page'))


# --- API NHẬN DIỆN THẬT SỰ VỚI YOLO ---

# --- KHO LƯU TRỮ LỊCH SỬ (Tạm thời lưu trong RAM) ---
history_db = []

@app.route('/statistics')
def statistics_page():
    if 'username' not in session:
        return redirect(url_for('login_page'))
    return render_template('statistics.html')


# API lấy danh sách lịch sử
@app.route('/api/history')
def get_history():
    # Trả về danh sách đảo ngược (mới nhất lên đầu)
    return jsonify(history_db[::-1])


# --- CẬP NHẬT API UPLOAD ẢNH (predict) ---
@app.route('/predict', methods=['POST'])
def predict():
    # ... (Code nhận file cũ) ...
    file = request.files['file']

    # Chuyển file thành Base64 để lưu vào history
    img_bytes = file.read()
    file.seek(0)  # Reset con trỏ file để AI đọc lại
    base64_img = "data:image/jpeg;base64," + base64.b64encode(img_bytes).decode('utf-8')

    # ... (Code AI nhận diện cũ của bạn) ...
    # Giả sử results lấy được từ AI là:
    # results = [{'name': 'Ghế', 'qty': 1}]

    # --- LƯU VÀO HISTORY ---
    record = {
        'id': len(history_db) + 1,
        'timestamp': datetime.now().strftime("%d/%m/%Y %H:%M:%S"),
        'image': base64_img,
        'source': 'Upload',
        'name': file.filename,
        'ip_cam': 'N/A',
        'office': 'N/A',
        'results': [{'name': 'Ghế (Demo)', 'qty': 1}]  # Thay bằng biến results thật của bạn
    }
    history_db.append(record)

    return jsonify({'status': 'success', 'result': 'Đã lưu'})


# --- CẬP NHẬT API CAMERA (predict_camera) ---
@app.route('/predict_camera', methods=['POST'])
def predict_camera():
    try:
        data = request.get_json()
        image_data = data['image']  # Ảnh Base64

        # ... (Code AI xử lý ảnh cũ) ...
        # Giả sử final_results là kết quả AI trả về

        # --- LƯU VÀO HISTORY ---
        # Giả lập kết quả nếu chưa chạy AI thật
        if 'final_results' not in locals():
            final_results = [{'name': 'Người', 'qty': 1}]

        record = {
            'id': len(history_db) + 1,
            'timestamp': datetime.now().strftime("%d/%m/%Y %H:%M:%S"),
            'image': image_data,
            'source': 'Camera',
            'name': f"Snapshot_{len(history_db) + 1}.jpg",
            'ip_cam': '192.168.1.105',  # IP giả định hoặc lấy từ config
            'office': 'Khu Vực A - Kho 01',
            'results': final_results
        }
        history_db.append(record)

        return jsonify({'status': 'success', 'results': final_results})
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)})


if __name__ == '__main__':
    app.run(debug=True)