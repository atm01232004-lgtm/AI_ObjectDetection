const video = document.getElementById('video');
const canvas = document.getElementById('canvas');
// const scanner = document.getElementById('scanner'); <-- XÓA DÒNG NÀY
const clockEl = document.getElementById('clock');
const objListEl = document.getElementById('obj-list');
const qtyListEl = document.getElementById('qty-list');

// --- 1. KHỞI TẠO SOCKET ---
var socket = io();

// --- 2. ĐỒNG HỒ ---
function updateClock() {
    const now = new Date();
    clockEl.innerText = now.toLocaleTimeString('vi-VN');
}
setInterval(updateClock, 1000);

// --- 3. KHỞI ĐỘNG CAMERA ---
async function startCamera() {
    try {
        const stream = await navigator.mediaDevices.getUserMedia({
            video: { facingMode: "environment", width: { ideal: 1920 } }
        });
        video.srcObject = stream;

        // Camera sẵn sàng thì tự động gửi ảnh luôn
        video.onloadedmetadata = () => {
            startSendingFrames();
        };
    } catch (err) { alert("Lỗi Camera: " + err.message); }
}
startCamera();

// --- 4. GỬI ẢNH LIÊN TỤC ---
function startSendingFrames() {
    // scanner.classList.remove('hidden'); <-- XÓA DÒNG NÀY (Bỏ hiệu ứng quét)

    setInterval(() => {
        if (video.readyState === video.HAVE_ENOUGH_DATA) {
            canvas.width = video.videoWidth;
            canvas.height = video.videoHeight;
            const ctx = canvas.getContext('2d');
            ctx.drawImage(video, 0, 0);

            // Nén ảnh 0.5 để gửi nhanh
            const imageData = canvas.toDataURL('image/jpeg', 0.5);
            socket.emit('send_frame', { image: imageData });
        }
    }, 100); // 100ms gửi 1 lần
}

// --- 5. NHẬN KẾT QUẢ ---
socket.on('update_detections', function(data) {
    objListEl.innerHTML = '';
    qtyListEl.innerHTML = '';

    const translations = {
        'person': 'Con người', 'cell phone': 'Điện thoại', 'laptop': 'Laptop',
        'mouse': 'Chuột', 'keyboard': 'Bàn phím', 'chair': 'Cái ghế',
        'bottle': 'Chai nước', 'cup': 'Cốc'
    };

    if (Object.keys(data).length === 0) {
        objListEl.innerHTML = '<li style="color: #777;">---</li>';
        qtyListEl.innerHTML = '<li>0</li>';
    } else {
        for (var objectName in data) {
            var count = data[objectName];
            var displayName = translations[objectName] || objectName;

            var liName = document.createElement('li');
            liName.innerText = displayName;
            objListEl.appendChild(liName);

            var liQty = document.createElement('li');
            liQty.innerText = count;
            qtyListEl.appendChild(liQty);
        }
    }
});

socket.on('disconnect', function() {
    objListEl.innerHTML = '<li style="color: red;">Mất kết nối!</li>';
});