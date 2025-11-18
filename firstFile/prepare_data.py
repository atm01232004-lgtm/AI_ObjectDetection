import os
import shutil
import random
from pathlib import Path

# --- CẤU HÌNH CỦA BẠN ---
SOURCE_DIR = Path('D:/AI_DO_Image01/downloaded_images')
TARGET_DIR = Path('D:/AI_DO_Image01/datasets')

# (Tên thư mục -> ID MỚI của chúng ta)
CLASSES_TO_PROCESS = {
    'chair': 0,
    'dining table': 1,
    'laptop': 2
}

# (ID Kaggle -> ID MỚI của chúng ta)
SOURCE_CLASS_MAP = {
    '0': '0',  # Kaggle '0' (chair) -> Mới '0' (chair)
    '1': '1',  # Kaggle '1' (dining table) -> Mới '1' (dining table)
    '3': '2'   # Kaggle '3' (laptop) -> Mới '2' (laptop)
}

VAL_SPLIT_RATIO = 0.2 
# --- KẾT THÚC CẤU HÌNH ---

def create_yolo_structure(base_path):
    (base_path / 'train' / 'images').mkdir(parents=True, exist_ok=True)
    (base_path / 'train' / 'labels').mkdir(parents=True, exist_ok=True)
    (base_path / 'val' / 'images').mkdir(parents=True, exist_ok=True)
    (base_path / 'val' / 'labels').mkdir(parents=True, exist_ok=True)
    print(f"Đã tạo cấu trúc thư mục tại: {base_path}")

def remap_label_file(src_label_path, dest_label_path):
    if not src_label_path.exists():
        return False
        
    with open(src_label_path, 'r') as f_in:
        new_lines = []
        lines = f_in.readlines()
        for line in lines:
            parts = line.strip().split()
            if not parts: continue
            original_class_id = parts[0]
            
            if original_class_id in SOURCE_CLASS_MAP:
                new_class_id = SOURCE_CLASS_MAP[original_class_id]
                new_line = f"{new_class_id} {' '.join(parts[1:])}\n"
                new_lines.append(new_line)
        
    if new_lines:
        with open(dest_label_path, 'w') as f_out:
            f_out.writelines(new_lines)
        return True
    return False

def process_data():
    if TARGET_DIR.exists():
        print(f"Đang xóa thư mục cũ: {TARGET_DIR}")
        shutil.rmtree(TARGET_DIR)
        
    create_yolo_structure(TARGET_DIR)
    
    total_images = 0
    train_count = 0
    val_count = 0
    
    for class_name, new_class_id in CLASSES_TO_PROCESS.items():
        class_path = SOURCE_DIR / class_name 
        if not class_path.exists():
            print(f"!!! CẢNH BÁO: Không tìm thấy thư mục: {class_path}. Bỏ qua...")
            continue
            
        print(f"\nĐang xử lý lớp: '{class_name}'...")
        images = list(class_path.glob('*.jpg')) 
        if not images:
            print(f"  [Cảnh báo] Không tìm thấy ảnh .jpg nào trong {class_path}")
            continue
            
        random.shuffle(images)
        
        for img_path in images:
            label_name = img_path.with_suffix('.txt').name
            src_label_path = class_path / label_name 
            
            if random.random() < VAL_SPLIT_RATIO:
                split = 'val'
                val_count_increment = 1
                train_count_increment = 0
            else:
                split = 'train'
                val_count_increment = 0
                train_count_increment = 1
            
            dest_label_path = TARGET_DIR / split / 'labels' / label_name
            label_processed = remap_label_file(src_label_path, dest_label_path)
            
            if label_processed:
                dest_img_path = TARGET_DIR / split / 'images' / img_path.name
                shutil.copy(img_path, dest_img_path)
                total_images += 1
                val_count += val_count_increment
                train_count += train_count_increment

    print("\n--- HOÀN TẤT ---")
    print(f"Tổng số ảnh đã xử lý (có nhãn hợp lệ): {total_images}")
    print(f"Ảnh huấn luyện (train): {train_count}")
    print(f"Ảnh xác thực (val): {val_count}")
    print(f"Dữ liệu đã sẵn sàng tại thư mục: {TARGET_DIR}")

if __name__ == '__main__':
    process_data()