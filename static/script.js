// --- 1. HÀM XEM TRƯỚC ẢNH (Preview) ---
// Hàm này chạy ngay khi bạn chọn file từ máy tính
// 1. Xử lý khi chọn file
function handleFiles(files) {
    const file = files[0];

    // Lấy các phần tử cần thiết
    const preview = document.getElementById('image-preview');
    const wrapper = document.getElementById('image-view-wrapper');
    const label = document.getElementById('upload-label');

    // Kiểm tra xem HTML có đủ ID chưa, nếu thiếu thì báo lỗi
    if (!preview || !wrapper || !label) {
        console.error("LỖI: Thiếu ID trong HTML! Kiểm tra lại: image-preview, image-view-wrapper, upload-label");
        return;
    }

    if (file) {
        const reader = new FileReader();
        reader.onload = function(e) {
            // Gán ảnh
            preview.src = e.target.result;

            // Ẩn nhãn "Tải lên", Hiện khung ảnh
            label.classList.add('hidden');
            wrapper.classList.remove('hidden');

            // Xóa kết quả cũ bên phải (nếu có)
            if(typeof resetRightPanel === "function") {
                resetRightPanel();
            }
        }
        reader.readAsDataURL(file);
    }
}

// 2. Nút Xóa Ảnh (Nút X)
function removeImage() {
    document.getElementById('fileElem').value = ""; // Reset input

    // Ẩn khung ảnh, Hiện nhãn "Tải lên"
    document.getElementById('image-view-wrapper').classList.add('hidden');
    document.getElementById('upload-label').classList.remove('hidden');
    document.getElementById('image-preview').src = "";

    if(typeof resetRightPanel === "function") {
        resetRightPanel();
    }
}

// 3. Nút Đổi ảnh (Kích hoạt input file)
function triggerChangeImage() {
    document.getElementById('fileElem').click();
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