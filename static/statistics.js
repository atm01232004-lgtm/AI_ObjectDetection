document.addEventListener('DOMContentLoaded', function() {
    fetchHistory();
});

// --- KHAI BÁO BIẾN TOÀN CỤC (QUAN TRỌNG) ---
let historyData = [];
let currentItemId = null;       // ID ảnh đang xem
let currentAnnotatedSrc = "";   // Link ảnh có khung (Kết quả AI)
let currentOriginalSrc = "";    // Link ảnh gốc (Sạch)
let isShowingOriginal = false;  // Trạng thái đang xem ảnh nào

// 1. TẢI DỮ LIỆU TỪ SERVER
function fetchHistory() {
    fetch('/api/history')
        .then(response => response.json())
        .then(data => {
            historyData = data;
            renderList(data);
        })
        .catch(err => console.error("Lỗi tải lịch sử:", err));
}

// 2. VẼ DANH SÁCH BÊN TRÁI
function renderList(data) {
    const listEl = document.getElementById('history-list');
    listEl.innerHTML = "";

    if (data.length === 0) {
        listEl.innerHTML = "<li style='text-align:center; padding:20px; color:#777'>Chưa có dữ liệu</li>";
        return;
    }

    data.forEach((item) => {
        const li = document.createElement('li');
        li.innerHTML = `
            <span class="list-item-title">${item.name}</span>
            <span class="list-item-sub"><i class="fas fa-clock"></i> ${item.timestamp}</span>
        `;

        li.onclick = () => {
            // Xóa class active cũ
            document.querySelectorAll('#history-list li').forEach(el => el.classList.remove('active'));
            // Thêm active cho dòng đang chọn
            li.classList.add('active');
            // Hiển thị chi tiết
            showDetail(item);
        };

        listEl.appendChild(li);
    });
}

// 3. HIỂN THỊ CHI TIẾT (Đoạn code bạn gửi nằm ở đây)
function showDetail(item) {
    const imgEl = document.getElementById('detail-image');
    const emptyState = document.getElementById('empty-state');
    const btnToggle = document.getElementById('btn-toggle-view');

    // --- A. Xử lý Logic Ảnh ---
    // Lưu dữ liệu vào biến toàn cục để dùng cho nút Toggle
    currentAnnotatedSrc = item.image;

    // Nếu dữ liệu cũ chưa có image_original thì dùng tạm ảnh hiện tại (fallback)
    currentOriginalSrc = item.image_original || item.image;

    // Reset về trạng thái mặc định (Xem kết quả AI)
    isShowingOriginal = false;
    imgEl.src = currentAnnotatedSrc;
    updateToggleButton();

    // --- B. Hiển thị Giao diện ---
    imgEl.classList.remove('hidden');
    emptyState.style.display = 'none';

    // Chỉ hiện nút chuyển đổi nếu có ảnh gốc thực sự (hoặc luôn hiện cũng được)
    btnToggle.classList.remove('hidden');

    document.getElementById('detail-info').classList.remove('hidden');
    document.getElementById('btn-delete').classList.remove('hidden');

    // --- C. Điền thông tin ---
    currentItemId = item.id;
    document.getElementById('d-name').innerText = item.name;
    document.getElementById('d-time').innerText = item.timestamp;
    document.getElementById('d-source').innerText = item.source;
    document.getElementById('d-office').innerText = item.office || "N/A";
    document.getElementById('d-ip').innerText = item.ip_cam || "N/A";

    // --- D. Điền danh sách vật thể ---
    const resUl = document.getElementById('d-results');
    resUl.innerHTML = "";
    if (item.results && item.results.length > 0) {
        item.results.forEach(res => {
            const li = document.createElement('li');
            li.innerHTML = `<i class="fas fa-check"></i> ${res.name}: <span style="color:white">${res.qty}</span>`;
            resUl.appendChild(li);
        });
    } else {
        resUl.innerHTML = "<li>Không tìm thấy vật thể</li>";
    }
}

// 4. HÀM XỬ LÝ NÚT BẤM CHUYỂN ẢNH
function toggleImageView() {
    const imgEl = document.getElementById('detail-image');

    isShowingOriginal = !isShowingOriginal; // Đảo ngược trạng thái

    if (isShowingOriginal) {
        imgEl.src = currentOriginalSrc;
    } else {
        imgEl.src = currentAnnotatedSrc;
    }

    updateToggleButton();
}

function updateToggleButton() {
    const btn = document.getElementById('btn-toggle-view');
    const span = btn.querySelector('span');
    const icon = btn.querySelector('i');

    if (isShowingOriginal) {
        span.innerText = "Xem kết quả AI";
        icon.className = "fas fa-project-diagram";
        btn.classList.add('active'); // Đổi màu nút cho nổi bật
    } else {
        span.innerText = "Xem ảnh gốc";
        icon.className = "fas fa-eye";
        btn.classList.remove('active');
    }
}

// 5. HÀM XÓA ẢNH
function deleteCurrentItem() {
    if (!currentItemId) return;

    if (!confirm("Bạn có chắc muốn xóa ảnh này không?")) return;

    fetch('/api/delete_history', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ id: currentItemId })
    })
    .then(res => res.json())
    .then(data => {
        if (data.status === 'success') {
            alert("Đã xóa thành công!");
            // Reset giao diện về trạng thái trống
            document.getElementById('detail-image').classList.add('hidden');
            document.getElementById('detail-info').classList.add('hidden');
            document.getElementById('btn-delete').classList.add('hidden');
            document.getElementById('btn-toggle-view').classList.add('hidden'); // Ẩn nút toggle
            document.getElementById('empty-state').style.display = 'block';

            // Tải lại danh sách bên trái
            fetchHistory();
        } else {
            alert("Lỗi: " + data.message);
        }
    });
}