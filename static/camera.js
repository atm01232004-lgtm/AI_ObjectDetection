const video = document.getElementById('video');
const canvas = document.getElementById('canvas');
const scanner = document.getElementById('scanner');
const clockEl = document.getElementById('clock');

// Lấy thẻ danh sách (ul)
const objListEl = document.getElementById('obj-list');
const qtyListEl = document.getElementById('qty-list');

// 1. Đồng hồ (Giữ nguyên)
function updateClock() {
    const now = new Date();
    clockEl.innerText = now.toLocaleTimeString('vi-VN') + " - " + now.toLocaleDateString('vi-VN');
}
setInterval(updateClock, 1000);
updateClock();

// 2. Camera (Giữ nguyên)
async function startCamera() {
    try {
        const stream = await navigator.mediaDevices.getUserMedia({
            video: { facingMode: "environment", width: { ideal: 1920 } }
        });
        video.srcObject = stream;
    } catch (err) { alert("Lỗi Camera: " + err.message); }
}
startCamera();

// 3. Chụp & Hiển thị danh sách (CẬP NHẬT MỚI)
function captureImage() {
    scanner.classList.remove('hidden');

    // Hiển thị trạng thái đang tải
    objListEl.innerHTML = `<li style="color: orange;">Đang quét...</li>`;
    qtyListEl.innerHTML = `<li>...</li>`;

    canvas.width = video.videoWidth;
    canvas.height = video.videoHeight;
    canvas.getContext('2d').drawImage(video, 0, 0);
    const imageData = canvas.toDataURL('image/jpeg');

    fetch('/predict_camera', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ image: imageData })
    })
    .then(response => response.json())
    .then(data => {
        scanner.classList.add('hidden');

        if (data.status === 'success') {
            // Xóa cũ
            objListEl.innerHTML = "";
            qtyListEl.innerHTML = "";

            // Duyệt qua danh sách kết quả trả về (Array)
            data.results.forEach(item => {
                // Thêm Tên vật thể
                const liName = document.createElement("li");
                liName.innerText = item.name;
                objListEl.appendChild(liName);

                // Thêm Số lượng
                const liQty = document.createElement("li");
                liQty.innerText = item.qty;
                qtyListEl.appendChild(liQty);
            });

        } else {
            objListEl.innerHTML = `<li style="color: red;">Lỗi</li>`;
        }
    })
    .catch(error => {
        scanner.classList.add('hidden');
        objListEl.innerHTML = "Mất kết nối";
    });
}