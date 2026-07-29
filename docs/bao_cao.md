# Báo cáo: Nhận biết thịt tươi bằng thị giác máy tính

## 1. Bài toán

Bài toán là xây dựng hệ thống nhận biết mức độ tươi của thịt bò từ ảnh RGB. Đầu vào là ảnh chụp miếng thịt trong điều kiện ánh sáng thông thường; đầu ra là nhãn **`fresh` (tươi)** hoặc **`spoiled` (hỏng/ôi)**. Đây là bài toán **phân loại nhị phân**, khớp với nhãn của bộ dữ liệu thật được sử dụng (LocBeef: `fresh`/`rotten`).

Việc nhận biết thịt tươi quan trọng vì chất lượng thực phẩm ảnh hưởng trực tiếp đến sức khỏe người tiêu dùng, giúp giảm lãng phí thực phẩm và hỗ trợ kiểm tra nhanh tại siêu thị, bếp ăn, kho bảo quản. So với kiểm tra hóa sinh hoặc vi sinh, phương pháp thị giác máy tính có ưu điểm không phá hủy mẫu, chi phí thấp, dễ triển khai bằng camera.

## 2. Dữ liệu

Sử dụng bộ **LocBeef — Beef Quality Image Dataset** (Kaggle, tác giả `mexwell`): **3.268 ảnh** thịt bò địa phương vùng Aceh, chia sẵn hai lớp `fresh` và `rotten`, đã có sẵn phân chia train/test:

| Tập | fresh | rotten | Tổng |
|:--|--:|--:|--:|
| Train | 1.144 | 1.144 | 2.288 |
| Test | 490 | 490 | 980 |
| **Tổng** | **1.634** | **1.634** | **3.268** |

Nhãn `rotten` của dataset được ánh xạ sang `spoiled` để thống nhất với giao diện ứng dụng. Vì kho ảnh gốc lớn (~5,5 GB), quá trình huấn luyện đọc ảnh **trực tiếp từ file nén (in-memory)** mà không giải nén ra ổ đĩa (`scripts/train_locbeef_from_zip.py`).

## 3. Phương pháp

Hướng tiếp cận là **học máy cổ điển với đặc trưng ảnh thủ công** — nhẹ, chạy được trên CPU và dễ giải thích.

### 3.1 Tiền xử lý và tách vùng thịt

1. Đọc ảnh, resize về **224 × 224** để chuẩn hóa đầu vào.
2. Cân bằng sáng cục bộ bằng **CLAHE** trên kênh L của không gian màu Lab, giảm ảnh hưởng chiếu sáng không đều.
3. **Tách vùng thịt (meat-region masking):** loại bỏ pixel nền quá sáng/trắng (khay, đĩa) và pixel quá tối, dùng phép hình thái học open/close để làm sạch mask. Đặc trưng màu chỉ tính trên vùng thịt, tránh học nhầm màu nền.

### 3.2 Đặc trưng (vector 174 chiều)

| Nhóm đặc trưng | Chi tiết | Số chiều |
|:--|:--|--:|
| Histogram HSV | H (32 bins, 0–179), S (16), V (16) | 64 |
| Histogram Lab | L (16), a (16), b (16) | 48 |
| Thống kê màu | mean, std, phần trăm vị 10/50/90 trên 6 kênh HSV+Lab | 30 |
| Texture LBP | Local Binary Pattern, 32 bins | 32 |
| **Tổng** | | **174** |

Đặc trưng màu (HSV/Lab) phù hợp vì thịt tươi có màu đỏ/hồng rõ, thịt hỏng ngả nâu/xám/xỉn; LBP mô tả vân và độ thô mịn bề mặt vốn thay đổi khi thịt mất nước và oxy hóa.

### 3.3 Mô hình

Mô hình chính là **RandomForest** (300 cây, `class_weight="balanced"`). Mã nguồn cũng hỗ trợ SVM kernel RBF như một lựa chọn thay thế (`src/train.py --model svm`). Đánh giá bằng accuracy, precision, recall, F1-score và confusion matrix.

## 4. Kết quả

Đánh giá trên **test set gốc của LocBeef (980 ảnh)**:

| Chỉ số | fresh | spoiled |
|:--|--:|--:|
| Precision | 1.00 | 0.96 |
| Recall | 0.96 | 1.00 |
| F1-score | 0.98 | 0.98 |

- **Accuracy: 97.9%** (959/980 ảnh đúng, 21 lỗi).
- Ma trận nhầm lẫn: 20 ảnh `fresh` bị đoán nhầm thành `spoiled`; không có ảnh `spoiled` nào bị đoán nhầm thành `fresh`. Mô hình nghiêng về phía "an toàn" (thiên về báo hỏng), phù hợp bài toán an toàn thực phẩm.

Xem `outputs/locbeef_rf_v1/confusion_matrix.png` và `classification_report.txt`.

## 5. Ứng dụng web demo

Repo kèm ứng dụng **Flask** (`app.py`): người dùng tải ảnh lên trình duyệt, hệ thống trả về nhãn tươi/hỏng kèm xác suất từng lớp. Ứng dụng có fallback giải mã ảnh **AVIF/HEIC** bằng Pillow (định dạng ảnh điện thoại/web mà OpenCV không đọc được). Chạy: `python app.py` rồi mở `http://127.0.0.1:5000`.

## 6. Thảo luận và nhận xét

**Ưu điểm:** pipeline đơn giản, chạy nhanh trên CPU, không cần GPU, giải thích được dựa trên màu sắc/texture; đạt độ chính xác cao trên đúng phân phối dữ liệu huấn luyện.

**Hạn chế và các điểm cần trung thực:**

- **Cách chia train/test:** dùng phân chia có sẵn của dataset. Nếu nhiều ảnh chụp *cùng một miếng thịt* nằm ở cả train lẫn test, độ chính xác 97,9% có thể *lạc quan hơn* so với thực tế trên mẫu hoàn toàn mới. Đây là giới hạn cần lưu ý khi diễn giải con số.
- **Lệch phân phối (domain shift):** mô hình được huấn luyện trên ảnh bò Aceh chụp trong điều kiện tương đối đồng nhất. Khi thử với ảnh thịt lấy ngẫu nhiên trên web (khác camera, ánh sáng, loại thịt), độ tin cậy giảm rõ và có trường hợp phân loại sai. Mô hình mạnh trên ảnh *giống dữ liệu huấn luyện*, không nên xem là bộ phân loại tổng quát cho mọi loại thịt.
- **Ghi nhận trong quá trình phát triển:** một lớp "hybrid" phân tích màu miền (CIELAB/HSV) từng được thêm vào để hậu xử lý dự đoán. Tuy nhiên khi **đánh giá định lượng trên test set thật**, lớp này làm accuracy tụt xuống **50%** (các ngưỡng màu được chỉnh tay theo ảnh stock sáng đẹp, không khớp màu bò thật nên ép hầu hết ảnh về "hỏng"). Vì vậy lớp hybrid đã bị **loại bỏ**, hệ thống dùng trực tiếp dự đoán của RandomForest. Đây là ví dụ cho thấy tầm quan trọng của việc đánh giá trên dữ liệu thật thay vì tin vào heuristic cảm tính.

**Hướng cải thiện:** kiểm soát rò rỉ dữ liệu bằng cách chia theo *từng mẫu vật*; tăng đa dạng dữ liệu (nhiều loại thịt, điều kiện chụp); dùng transfer learning (MobileNetV3/EfficientNet-B0) để tổng quát tốt hơn; thêm cơ chế từ chối dự đoán khi ảnh nằm ngoài phân phối hoặc độ tin cậy thấp.

**Kết luận:** nhận biết thịt tươi bằng ảnh là bài toán có ý nghĩa thực tế và giải được bằng pipeline thị giác máy tính gọn nhẹ. Baseline màu + texture + tách vùng thịt + RandomForest đạt 97,9% trên bộ LocBeef. Hệ thống là công cụ **hỗ trợ sàng lọc**, không thay thế kiểm nghiệm vi sinh hoặc đánh giá an toàn thực phẩm chính thức.

## Tài liệu tham khảo

1. LocBeef — Beef Quality Image Dataset (local Aceh beef, fresh/rotten). Kaggle. https://www.kaggle.com/datasets/mexwell/locbeef-beef-quality-image-dataset
2. Bramantyo, H. A., Faridi, M. A., Chen, R., Harris, C., & Sun, Y. (2026). Deep Learning-Based Meat Freshness Detection with Segmentation and OOD-Aware Classification. arXiv:2603.00368.
3. Hidalgo, M. M., Lima, R. C., De Nadai Fernandes, E. A., Bacchi, M. A., & Sarriés, G. A. (2025). Leveraging pre-trained computer vision models for accurate classification of meat freshness. Food Chemistry, 495(Pt 3), 146430.
4. Ojala, T., Pietikäinen, M., & Mäenpää, T. (2002). Multiresolution gray-scale and rotation invariant texture classification with local binary patterns. IEEE TPAMI, 24(7), 971–987.
