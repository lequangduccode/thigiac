# Nhận biết thịt tươi bằng thị giác máy tính

Project bài tập môn Thị giác máy tính: **phân loại nhị phân** ảnh thịt bò thành `fresh` (tươi) hoặc `spoiled` (hỏng) dựa trên đặc trưng màu sắc + texture và tách vùng thịt, kèm **ứng dụng web** để tải ảnh lên và xem kết quả.

Mô hình được huấn luyện trên bộ dữ liệu thật **LocBeef** (3.268 ảnh) và đạt **97.9% accuracy** trên test set gốc của bộ dữ liệu.

## Bắt đầu nhanh (web demo)

Model đã được train sẵn và đóng gói trong repo, clone về là chạy được ngay:

```bash
pip install -r requirements.txt
python app.py
```

Mở trình duyệt tại `http://127.0.0.1:5000`, kéo/thả ảnh miếng thịt → xem nhãn tươi/hỏng kèm xác suất từng lớp.

## Nội dung repo

| Đường dẫn | Vai trò |
|:--|:--|
| `app.py` | Web app Flask: upload ảnh → dự đoán (có fallback giải mã AVIF/HEIC bằng Pillow). |
| `templates/index.html` | Giao diện web (kéo-thả, preview, thanh xác suất). |
| `src/features.py` | Tách vùng thịt + trích đặc trưng HSV/Lab/thống kê màu/LBP (vector 174 chiều). |
| `src/train.py` | Huấn luyện SVM hoặc RandomForest từ thư mục ảnh, lưu model + confusion matrix. |
| `src/predict.py` | Dự đoán một ảnh từ dòng lệnh. |
| `scripts/train_locbeef_from_zip.py` | Train từ file zip LocBeef **không cần giải nén** (đọc in-memory). |
| `scripts/eval_locbeef_from_zip.py` | Đánh giá model trên test set LocBeef, xuất confusion matrix + report. |
| `scripts/build_report.py` | Sinh báo cáo Word (`reports/bao_cao_nhan_biet_thit_tuoi.docx`). |
| `outputs/locbeef_rf_v1/` | Model đã train + metrics + confusion matrix. |

## Mô hình & dữ liệu

- **Dataset:** [LocBeef - Beef Quality Image Dataset](https://www.kaggle.com/datasets/mexwell/locbeef-beef-quality-image-dataset) (Kaggle) — 3.268 ảnh thịt bò Aceh, 2 lớp `fresh`/`rotten` (`rotten` ánh xạ sang `spoiled`). Chia sẵn train/test: 2.288 / 980.
- **Đặc trưng (174 chiều):** histogram HSV (64) + histogram Lab (48) + thống kê màu (30) + LBP texture (32), chỉ tính trên vùng thịt sau khi loại nền.
- **Mô hình:** RandomForest (300 cây, `class_weight="balanced"`). Model ship trong repo được train trên toàn bộ 3.268 ảnh; con số 97.9% đo trên phần held-out 980 ảnh.

## Pipeline

1. Đọc ảnh, resize về 224 × 224.
2. Cân bằng sáng cục bộ bằng CLAHE trên kênh L của Lab.
3. **Tách vùng thịt** (loại nền trắng/sáng và vùng quá tối) bằng ngưỡng HSV + hình thái học.
4. Trích đặc trưng màu (HSV, Lab, thống kê) + texture (LBP) trên vùng thịt.
5. Phân loại bằng RandomForest; đánh giá bằng accuracy, precision, recall, F1, confusion matrix.

## Train lại từ đầu

**Từ file zip LocBeef (khuyến nghị, không tốn dung lượng giải nén):**

```bash
# Đánh giá bằng train/test split có sẵn (ra con số accuracy)
python scripts/train_locbeef_from_zip.py --zip "duong/dan/archive.zip"

# Đánh giá chi tiết + confusion matrix trên test set
python scripts/eval_locbeef_from_zip.py --zip "duong/dan/archive.zip"

# Train model cuối cùng trên TOÀN BỘ 3268 ảnh để ship
python scripts/train_locbeef_from_zip.py --zip "duong/dan/archive.zip" --all
```

**Từ thư mục ảnh bất kỳ** (mỗi lớp một thư mục con `fresh/`, `spoiled/`):

```bash
python src/train.py --data data/meat_dataset --model random_forest --output-dir outputs/meat_rf
python src/predict.py --model outputs/meat_rf/model.joblib --image path/to/meat.jpg
```

## Báo cáo

Báo cáo chi tiết ở `docs/bao_cao.md` (Markdown) và `reports/bao_cao_nhan_biet_thit_tuoi.docx` (Word). Sinh lại file Word:

```bash
python scripts/build_report.py
```

## Ghi chú an toàn

Hệ thống là công cụ **hỗ trợ sàng lọc** bằng ảnh, không thay thế kiểm nghiệm vi sinh hoặc đánh giá an toàn thực phẩm chính thức. Mô hình mạnh trên ảnh giống phân phối dữ liệu huấn luyện (bò Aceh); với ảnh khác điều kiện chụp, độ tin cậy có thể giảm.
