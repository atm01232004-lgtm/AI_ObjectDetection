from ultralytics import YOLO

# Tải một mô hình YOLOv8 đã được huấn luyện trước (pretrained)
model = YOLO('yolov8n.pt')


# Huấn luyện mô hình với dữ liệu của chúng ta
def train_model():
    print("Bắt đầu quá trình huấn luyện...")
    results = model.train(
        data='office_data.yaml',
        epochs=50,
        imgsz=640,
        batch=16,
        name='yolov8n_office_v1',

        # Dòng này chính là thứ bạn cần!
        # '0' có nghĩa là "sử dụng GPU đầu tiên (CUDA device 0)"
        device=0
    )

    print("Hoàn tất huấn luyện!")
    print(f"Kết quả được lưu tại: {results.save_dir}")


if __name__ == '__main__':
    train_model()