// --- KHỞI TẠO SOCKET TOÀN CỤC ---
// Kiểm tra xem socket đã có chưa, nếu chưa thì tạo
if (typeof socket === 'undefined') {
    var socket = io();
}

const globalVideo = document.getElementById('global-video');
const globalCanvas = document.getElementById('global-canvas');
const navCamIcon = document.getElementById('nav-cam-icon');
const clockEl = document.getElementById('clock');
const objListEl = document.getElementById('obj-list');
const qtyListEl = document.getElementById('qty-list');

// --- 1. ĐỒNG HỒ ---
function updateClock() {
    const now = new Date();
    // Lấy ngày: 18/11/2025
    const dateString = now.toLocaleDateString('vi-VN');
    // Lấy giờ: 20:47:54
    const timeString = now.toLocaleTimeString('vi-VN');

    // Nối lại: 18/11/2025 - 20:47:54
    clockEl.innerText = `${dateString} - ${timeString}`;
}
setInterval(updateClock, 1000);

// --- 2. TỰ ĐỘNG CHẠY CAMERA NỀN (BACKGROUND) ---
async function initGlobalCamera() {
    try {
        const stream = await navigator.mediaDevices.getUserMedia({
            video: { facingMode: "environment", width: { ideal: 1280 } }
        });
        globalVideo.srcObject = stream;

        // Bắt đầu gửi ảnh khi video sẵn sàng
        globalVideo.onloadedmetadata = () => {
            setInterval(sendGlobalFrame, 500); // Gửi 2 khung hình/giây (để đỡ lag khi chạy nền)
        };

        // Nếu đang ở trang Camera.html, ta gán stream này cho video chính luôn
        // để tránh bật 2 lần camera gây lỗi
        const mainPageVideo = document.getElementById('video');
        if (mainPageVideo) {
            mainPageVideo.srcObject = stream;
        }

    } catch (err) {
        console.error("Không thể bật Camera nền:", err);
    }
}

function sendGlobalFrame() {
    if (globalVideo.readyState === globalVideo.HAVE_ENOUGH_DATA) {
        globalCanvas.width = globalVideo.videoWidth;
        globalCanvas.height = globalVideo.videoHeight;
        const ctx = globalCanvas.getContext('2d');
        ctx.drawImage(globalVideo, 0, 0);

        const imageData = globalCanvas.toDataURL('image/jpeg', 0.5);
        socket.emit('send_frame', { image: imageData });
    }
}

// Chạy ngay lập tức
initGlobalCamera();

// --- 3. LẮNG NGHE CẢNH BÁO TỪ SERVER ---
socket.on('update_detections', function(data) {
    // Data trả về dạng: { counts: {...}, is_alert: true/false }

    if (data.is_alert) {
        // Nếu thiếu đồ -> Nhấp nháy đỏ icon Camera trên menu
        navCamIcon.classList.add('alert-active');
    } else {
        // Nếu đủ -> Bình thường
        navCamIcon.classList.remove('alert-active');
    }

    // Nếu đang ở trang Camera (có bảng hiển thị), cập nhật bảng như cũ
    if (typeof updateUI === 'function') {
        updateUI(data.counts);
    }
});


// --- 3. QUẢN LÝ CÀI ĐẶT (MODAL) ---
function openSettingsModal() {
    document.getElementById('settings-modal').classList.remove('hidden');
    loadTargets();
}

function closeSettingsModal() {
    document.getElementById('settings-modal').classList.add('hidden');
}

function loadTargets() {
    fetch('/api/targets')
        .then(res => res.json())
        .then(data => {
            const tbody = document.getElementById('target-list-body');
            tbody.innerHTML = "";
            data.forEach(t => {
                tbody.innerHTML += `
                    <tr>
                        <td>${t.name}</td>
                        <td>Wait >= ${t.qty}</td>
                        <td><button class="btn-del-target" onclick="deleteTarget(${t.id})"><i class="fas fa-trash"></i></button></td>
                    </tr>
                `;
            });
        });
}

function addTarget() {
    const name = document.getElementById('set-name').value;
    const qty = document.getElementById('set-qty').value;

    if(!name || !qty) return alert("Nhập đủ thông tin!");

    fetch('/api/targets', {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({name: name, qty: qty})
    }).then(() => {
        document.getElementById('set-name').value = "";
        document.getElementById('set-qty').value = "";
        loadTargets();
    });
}

function deleteTarget(id) {
    fetch('/api/delete_target', {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({id: id})
    }).then(() => loadTargets());
}

// Hàm hỗ trợ cập nhật UI trang Camera (để tương thích code cũ)
// Chỉ chạy khi đang ở trang camera.html
function updateUI(counts) {
    const objListEl = document.getElementById('obj-list');
    const qtyListEl = document.getElementById('qty-list');
    if (!objListEl) return; // Không phải trang camera thì thoát

    objListEl.innerHTML = '';
    qtyListEl.innerHTML = '';

    if (Object.keys(counts).length === 0) {
        objListEl.innerHTML = '<li>---</li>';
        qtyListEl.innerHTML = '<li>0</li>';
    } else {
        for (const [name, qty] of Object.entries(counts)) {
            const liName = document.createElement('li'); liName.innerText = name;
            objListEl.appendChild(liName);
            const liQty = document.createElement('li'); liQty.innerText = qty;
            qtyListEl.appendChild(liQty);
        }
    }
}

// --- LOGIC VẼ KHUNG LÊN VIDEO (CANVAS OVERLAY) ---

const overlayCanvas = document.getElementById('overlay-canvas');
const mainVideo = document.getElementById('video'); // Video ở trang camera.html

// Hàm vẽ khung
function drawBoxes(boxes) {
    if (!overlayCanvas || !mainVideo) return; // Nếu không ở trang camera thì thôi

    const ctx = overlayCanvas.getContext('2d');

    // 1. Đồng bộ kích thước Canvas với Video thật
    // Video có thể bị CSS co giãn, ta cần lấy kích thước hiển thị thực tế
    overlayCanvas.width = mainVideo.videoWidth;
    overlayCanvas.height = mainVideo.videoHeight;

    // Xóa khung cũ đi
    ctx.clearRect(0, 0, overlayCanvas.width, overlayCanvas.height);

    // 2. Vẽ các khung mới
    boxes.forEach(box => {
        const [x1, y1, x2, y2] = box.coords;
        const label = box.label;

        // Vẽ hình chữ nhật
        ctx.beginPath();
        ctx.lineWidth = 4;
        ctx.strokeStyle = "#00e676"; // Màu xanh lá neon (Rất nổi)
        ctx.rect(x1, y1, (x2 - x1), (y2 - y1));
        ctx.stroke();

        // Vẽ nền chữ
        ctx.fillStyle = "#00e676";
        ctx.font = "bold 20px Arial";
        const textWidth = ctx.measureText(label).width;
        ctx.fillRect(x1, y1 - 25, textWidth + 10, 25);

        // Vẽ chữ
        ctx.fillStyle = "#000000"; // Chữ đen
        ctx.fillText(label, x1 + 5, y1 - 5);
    });
}

// CẬP NHẬT SOCKET LẮNG NGHE
socket.on('update_detections', function(data) {
    // 1. Logic cảnh báo (Giữ nguyên)
    if (typeof navCamIcon !== 'undefined') {
        if (data.is_alert) navCamIcon.classList.add('alert-active');
        else navCamIcon.classList.remove('alert-active');
    }

    // 2. Logic cập nhật bảng số lượng (Giữ nguyên)
    if (typeof updateUI === 'function') {
        updateUI(data.counts);
    }

    // 3. LOGIC MỚI: GỌI HÀM VẼ KHUNG
    if (data.boxes) {
        drawBoxes(data.boxes);
    }
});