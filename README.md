# Nhận biết thịt tươi bằng thị giác máy tính

Project bài tập môn Thị giác máy tính: phân loại ảnh thịt thành các nhóm như `fresh`, `half_fresh`, `spoiled` dựa trên đặc trưng màu sắc và texture.

## Nội dung

- `src/features.py`: trích xuất đặc trưng HSV, Lab, thống kê màu và LBP.
- `src/train.py`: huấn luyện SVM hoặc RandomForest, lưu mô hình và biểu đồ đánh giá.
- `src/predict.py`: dự đoán một ảnh mới.
- `scripts/make_demo_dataset.py`: tạo dataset minh họa để kiểm tra pipeline khi chưa tải dataset thật.
- `reports/bao_cao_nhan_biet_thit_tuoi.docx`: báo cáo Word theo khung trong ảnh đề bài.

## Cấu trúc dữ liệu

Đặt ảnh thật vào thư mục:

```text
data/meat_dataset/
  fresh/
    image_001.jpg
  half_fresh/
    image_002.jpg
  spoiled/
    image_003.jpg
```

Nếu chỉ làm bài phân loại nhị phân thì dùng hai thư mục `fresh/` và `spoiled/`.

## Chạy nhanh với dataset minh họa

```bash
python scripts/make_demo_dataset.py --output data/demo_meat --images-per-class 45
python src/train.py --data data/demo_meat --model svm --output-dir outputs/demo
python src/predict.py --model outputs/demo/model.joblib --image data/demo_meat/fresh/fresh_000.png
```

Dataset minh họa chỉ dùng để kiểm thử code. Khi nộp kết quả chính thức, nên thay bằng dataset ảnh thịt thật như Kaggle Meat Quality Assessment hoặc Meat Freshness Image Dataset.

## Phương pháp

Pipeline chính:

1. Đọc ảnh RGB/BGR và resize về 224 x 224.
2. Cân bằng sáng cục bộ bằng CLAHE trên kênh L của Lab.
3. Trích xuất histogram HSV, histogram Lab, thống kê màu và Local Binary Pattern.
4. Chuẩn hóa đặc trưng, huấn luyện SVM hoặc RandomForest.
5. Đánh giá bằng accuracy, precision, recall, F1-score và confusion matrix.

## Gợi ý dùng dataset thật

Tải dataset từ Kaggle, giải nén vào `data/meat_dataset`, sau đó chạy:

```bash
python src/train.py --data data/meat_dataset --model svm --output-dir outputs/meat_svm
python src/train.py --data data/meat_dataset --model random_forest --output-dir outputs/meat_rf
```

Sau khi có mô hình:

```bash
python src/predict.py --model outputs/meat_svm/model.joblib --image path/to/meat.jpg
```

## Ghi chú an toàn

Hệ thống này là công cụ hỗ trợ sàng lọc bằng ảnh, không thay thế kiểm nghiệm vi sinh hoặc đánh giá an toàn thực phẩm chính thức.

