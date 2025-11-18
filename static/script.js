// --- 1. HÀM XEM TRƯỚC ẢNH (Preview) ---
// Hàm này chạy ngay khi bạn chọn file từ máy tính
function handleFiles(files) {
    const preview = document.getElementById('image-preview');
    const container = document.getElementById('preview-container');
    const file = files[0];

    if (file) {
        const reader = new FileReader();

        // Khi đọc file xong thì gắn vào thẻ img
        reader.onload = function(e) {
            preview.src = e.target.result;
            preview.style.display = 'block'; // Hiện ảnh

            // Ẩn cái icon dấu cộng và chữ "Tải ảnh lên" đi
            if (container) container.style.display = 'none';

            // Reset lại khung kết quả nếu đang hiện kết quả cũ
            const resultBox = document.getElementById('result-box');
            if(resultBox.querySelector('.result-image-container')) {
                // Nếu đang hiện kết quả cũ, reset về trạng thái chờ
                 document.getElementById('output-image').style.display = 'none';
                 document.getElementById('output-text').innerHTML = '<div style="text-align:center; color:#aaa;">Sẵn sàng nhận diện</div>';
            }
        }
        reader.readAsDataURL(file);
    }
}

// --- 2. HÀM GỬI ẢNH LÊN SERVER (Upload) ---
// Hàm này chạy khi bạn bấm nút "Nhận dạng"
function startRecognition() {
    const loader = document.getElementById('loader');
    const resultBox = document.getElementById('result-box');
    const fileInput = document.getElementById('fileElem');

    // Kiểm tra xem có file chưa
    if (!fileInput.files.length) {
        alert("Vui lòng chọn ảnh trước!");
        return;
    }

    // A. Reset giao diện kết quả (Hiện loader)
    resultBox.innerHTML = `
        <div class="result-image-container">
            <div class="loader" id="loader"></div>
            <img id="output-image" src="" style="display:none; max-width:100%; max-height:100%;">
        </div>
        <div class="result-text-container" id="output-text">
            <div style="text-align:center; color:#aaa; margin-top:10px">Đang xử lý...</div>
        </div>
    `;

    // B. Gửi dữ liệu
    let formData = new FormData();
    formData.append("file", fileInput.files[0]);

    fetch('/predict', {
        method: "POST",
        body: formData
    })
    .then(response => response.json())
    .then(data => {
        // Ẩn loader
        const loaderEl = document.getElementById('loader');
        if(loaderEl) loaderEl.style.display = 'none';

        if (data.status === 'success') {
            // C. Hiển thị ảnh có khung (Kết quả từ AI)
            const outImg = document.getElementById('output-image');
            outImg.src = data.image_with_box;
            outImg.style.display = 'block';

            // D. Hiển thị danh sách kết quả
            const outText = document.getElementById('output-text');
            let htmlList = "";

            if(data.details && data.details.length > 0){
                 data.details.forEach(item => {
                    htmlList += `
                        <div class="result-list-item">
                            <span>${item.name}</span>
                            <b>x${item.qty}</b>
                        </div>
                    `;
                });
            } else {
                htmlList = "<div style='text-align:center; color:#ccc'>Không nhận diện được gì</div>";
            }

            outText.innerHTML = htmlList;
        } else {
            // Báo lỗi từ server
            document.getElementById('output-text').innerHTML = `<div style="color:red; text-align:center;">Lỗi: ${data.message}</div>`;
        }
    })
    .catch(error => {
        console.error(error);
        const loaderEl = document.getElementById('loader');
        if(loaderEl) loaderEl.style.display = 'none';
        alert("Lỗi kết nối tới Server!");
    });
}