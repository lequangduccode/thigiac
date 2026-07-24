# Báo cáo: Nhận biết thịt tươi bằng thị giác máy tính

## 1. Bài toán

Bài toán là xây dựng hệ thống nhận biết mức độ tươi của thịt từ ảnh RGB. Đầu vào là ảnh chụp miếng thịt trong điều kiện ánh sáng thông thường; đầu ra là nhãn `fresh`, `half_fresh` hoặc `spoiled`. Nếu chỉ cần bài toán nhị phân, hệ thống có thể gom thành hai lớp `fresh` và `spoiled`.

Việc nhận biết thịt tươi quan trọng vì chất lượng thực phẩm ảnh hưởng trực tiếp đến sức khỏe người tiêu dùng, giảm lãng phí thực phẩm và hỗ trợ kiểm tra nhanh trong siêu thị, bếp ăn, kho bảo quản. So với kiểm tra hóa sinh hoặc vi sinh, phương pháp thị giác máy tính có ưu điểm không phá hủy mẫu, chi phí thấp, dễ triển khai bằng camera.

## 2. Phương pháp

Hướng tiếp cận chính trong project là học máy với đặc trưng ảnh thủ công. Ảnh được resize về 224 x 224, cân bằng sáng bằng CLAHE trên kênh L của không gian màu Lab, sau đó trích xuất đặc trưng màu sắc và texture.

Đặc trưng màu gồm histogram HSV, histogram Lab và các thống kê trung bình, độ lệch chuẩn, phần trăm vị 10/50/90 trên từng kênh. Đây là nhóm đặc trưng phù hợp vì thịt tươi thường có màu đỏ/hồng sáng hơn, trong khi thịt kém tươi có xu hướng xỉn màu, nâu, xanh xám hoặc bề mặt tối hơn.

Đặc trưng texture dùng Local Binary Pattern (LBP) để mô tả độ thô, mịn, vân cơ, đốm bề mặt. Khi thịt giảm độ tươi, bề mặt thường thay đổi do mất nước, oxy hóa và vi sinh vật, vì vậy texture hỗ trợ phân biệt khi màu sắc bị ảnh hưởng bởi ánh sáng.

Sau khi có vector đặc trưng, project huấn luyện SVM kernel RBF hoặc RandomForest. Dữ liệu được chia train/test theo tỉ lệ 80/20 có stratify. Các chỉ số đánh giá gồm accuracy, precision, recall, F1-score và confusion matrix.

Với hướng học sâu, có thể dùng transfer learning từ MobileNetV3, EfficientNet-B0, ResNet-50 hoặc Swin Transformer. Các nghiên cứu gần đây cho thấy mô hình học sâu trích xuất đặc trưng từ ảnh RGB có thể đạt kết quả cao trong phân loại độ tươi thịt; tuy nhiên với bài tập nhỏ, baseline SVM dễ chạy, dễ giải thích và không cần GPU.

## 3. Thử nghiệm

Dataset khuyến nghị là các bộ ảnh thịt tươi/thịt hỏng trên Kaggle như Meat Quality Assessment Dataset hoặc Meat Freshness Image Dataset. Cấu trúc thư mục dùng trong code:

```text
data/meat_dataset/
  fresh/
  half_fresh/
  spoiled/
```

Quy trình thử nghiệm:

1. Thu thập hoặc tải ảnh, loại ảnh mờ/nhiễu nặng, đưa về cấu trúc thư mục theo nhãn.
2. Chạy `python src/train.py --data data/meat_dataset --model svm --output-dir outputs/meat_svm`.
3. Ghi lại accuracy, precision, recall, F1-score trong `metrics.json`.
4. Quan sát `confusion_matrix.png` để biết lớp nào hay bị nhầm.
5. Dự đoán ảnh mới bằng `python src/predict.py --model outputs/meat_svm/model.joblib --image path/to/image.jpg`.

Trong repo có thêm dataset minh họa sinh tự động để kiểm thử pipeline khi chưa có dataset thật. Dataset này không dùng làm kết luận khoa học, chỉ chứng minh code đọc ảnh, trích xuất đặc trưng, huấn luyện, lưu mô hình và dự đoán hoạt động đúng.

## 4. Thảo luận và nhận xét

Ưu điểm của phương pháp là đơn giản, dễ triển khai, chạy nhanh trên CPU và giải thích được dựa trên màu sắc/texture. Đây là lựa chọn phù hợp cho bài tập môn học hoặc prototype kiểm tra nhanh.

Hạn chế chính là độ chính xác phụ thuộc nhiều vào ánh sáng, nền ảnh, góc chụp, loại thịt và cách gán nhãn. Nếu ảnh có bao bì bóng, phản chiếu hoặc nền phức tạp, mô hình có thể học nhầm đặc trưng nền thay vì đặc trưng thịt.

Hướng cải thiện gồm: tách vùng thịt bằng segmentation trước khi phân loại, tăng dữ liệu với xoay/crop/thay đổi sáng, dùng transfer learning với MobileNet/EfficientNet, thêm cơ chế từ chối dự đoán khi ảnh ngoài phân phối hoặc độ tin cậy thấp.

Kết luận: Nhận biết thịt tươi bằng ảnh là bài toán có ý nghĩa thực tế và có thể giải bằng pipeline thị giác máy tính tương đối gọn. Baseline màu + texture + SVM là nền tảng tốt; nếu có dataset lớn và đa dạng, học sâu kết hợp segmentation sẽ cho khả năng tổng quát tốt hơn.

## Tài liệu tham khảo

1. Bramantyo, H. A., Faridi, M. A., Chen, R., Harris, C., & Sun, Y. (2026). Deep Learning-Based Meat Freshness Detection with Segmentation and OOD-Aware Classification. arXiv:2603.00368.
2. Hidalgo, M. M., Lima, R. C., De Nadai Fernandes, E. A., Bacchi, M. A., & Sarriés, G. A. (2025). Leveraging pre-trained computer vision models for accurate classification of meat freshness. Food Chemistry, 495(Pt 3), 146430.
3. Kaggle. Meat Quality Assessment Dataset.
4. Kaggle. Meat Freshness Image Dataset.

