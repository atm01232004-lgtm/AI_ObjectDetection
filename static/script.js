function handleFiles(files) {
    const preview = document.getElementById('image-preview');
    const container = document.getElementById('preview-container');
    const file = files[0];

    if (file) {
        const reader = new FileReader();
        reader.onload = function(e) {
            preview.src = e.target.result;
            preview.style.display = 'block';
            container.style.display = 'none'; // Ẩn icon dấu cộng
        }
        reader.readAsDataURL(file);
    }
}

function startRecognition() {
    const loader = document.getElementById('loader');
    const resultText = document.getElementById('result-text');
    const placeholder = document.querySelector('.placeholder-text');
    const fileInput = document.getElementById('fileElem');

    if (!fileInput.files.length) {
        alert("Vui lòng chọn ảnh trước!");
        return;
    }

    // UI Update
    placeholder.classList.add('hidden');
    resultText.classList.add('hidden');
    loader.classList.remove('hidden');

    // Gửi request tới Python (Giả lập)
    let formData = new FormData();
    formData.append("file", fileInput.files[0]);

    fetch('/predict', {
        method: "POST",
        body: formData
    })
    .then(response => response.json())
    .then(data => {
        loader.classList.add('hidden');
        resultText.innerHTML = `<i class="fas fa-check-circle" style="color: #10b981;"></i> ${data.result}`;
        resultText.classList.remove('hidden');
    })
    .catch(error => {
        loader.classList.add('hidden');
        alert("Có lỗi xảy ra!");
    });
}

function resetApp() {
    document.getElementById('image-preview').style.display = 'none';
    document.getElementById('preview-container').style.display = 'flex';
    document.getElementById('fileElem').value = "";
    document.querySelector('.placeholder-text').classList.remove('hidden');
    document.getElementById('result-text').classList.add('hidden');
}