document.addEventListener('DOMContentLoaded', function() {
    fetchHistory();
});

let historyData = [];

function fetchHistory() {
    fetch('/api/history')
        .then(response => response.json())
        .then(data => {
            historyData = data;
            renderList(data);
        })
        .catch(err => console.error("Lỗi tải lịch sử:", err));
}

function renderList(data) {
    const listEl = document.getElementById('history-list');
    listEl.innerHTML = "";

    if (data.length === 0) {
        listEl.innerHTML = "<li style='text-align:center'>Chưa có dữ liệu</li>";
        return;
    }

    data.forEach((item, index) => {
        const li = document.createElement('li');
        // Hiển thị Tên ảnh và Thời gian ở cột trái
        li.innerHTML = `
            <span class="list-item-title">${item.name}</span>
            <span class="list-item-sub"><i class="fas fa-clock"></i> ${item.timestamp}</span>
        `;

        // Sự kiện Click
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

function showDetail(item) {
    // 1. Hiển thị Ảnh
    const imgEl = document.getElementById('detail-image');
    const emptyState = document.getElementById('empty-state');

    imgEl.src = item.image;
    imgEl.classList.remove('hidden');
    emptyState.style.display = 'none';

    // 2. Hiển thị Thông tin
    document.getElementById('detail-info').classList.remove('hidden');

    document.getElementById('d-name').innerText = item.name;
    document.getElementById('d-time').innerText = item.timestamp;
    document.getElementById('d-source').innerText = item.source;

    document.getElementById('d-office').innerText = item.office || "N/A";
    document.getElementById('d-ip').innerText = item.ip_cam || "N/A";

    // 3. Hiển thị Kết quả nhận diện (Danh sách)
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