from __future__ import annotations

from pathlib import Path

from docx import Document
from docx.enum.section import WD_SECTION
from docx.enum.table import WD_CELL_VERTICAL_ALIGNMENT
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.shared import Inches, Pt, RGBColor


ROOT = Path(__file__).resolve().parents[1]
REPORT_PATH = ROOT / "reports" / "bao_cao_nhan_biet_thit_tuoi.docx"
CONFUSION_MATRIX = ROOT / "outputs" / "locbeef_rf_v1" / "confusion_matrix.png"


def set_font(run, name: str = "Calibri", size: int | None = None, bold: bool | None = None) -> None:
    run.font.name = name
    run._element.rPr.rFonts.set(qn("w:ascii"), name)
    run._element.rPr.rFonts.set(qn("w:hAnsi"), name)
    if size:
        run.font.size = Pt(size)
    if bold is not None:
        run.bold = bold


def set_cell_shading(cell, fill: str) -> None:
    tc_pr = cell._tc.get_or_add_tcPr()
    shading = OxmlElement("w:shd")
    shading.set(qn("w:fill"), fill)
    tc_pr.append(shading)


def set_cell_width(cell, width_dxa: int) -> None:
    tc_pr = cell._tc.get_or_add_tcPr()
    width = tc_pr.find(qn("w:tcW"))
    if width is None:
        width = OxmlElement("w:tcW")
        tc_pr.append(width)
    width.set(qn("w:w"), str(width_dxa))
    width.set(qn("w:type"), "dxa")


def add_heading(doc: Document, text: str, level: int = 1):
    paragraph = doc.add_heading(text, level=level)
    for run in paragraph.runs:
        set_font(run, size=16 if level == 1 else 13, bold=True)
        run.font.color.rgb = RGBColor(46, 116, 181) if level < 3 else RGBColor(31, 77, 120)
    return paragraph


def add_paragraph(doc: Document, text: str = "", bold_prefix: str | None = None):
    paragraph = doc.add_paragraph()
    paragraph.paragraph_format.space_after = Pt(6)
    paragraph.paragraph_format.line_spacing = 1.1
    if bold_prefix and text.startswith(bold_prefix):
        run = paragraph.add_run(bold_prefix)
        set_font(run, size=11, bold=True)
        run = paragraph.add_run(text[len(bold_prefix) :])
        set_font(run, size=11)
    else:
        run = paragraph.add_run(text)
        set_font(run, size=11)
    return paragraph


def add_bullet(doc: Document, text: str):
    paragraph = doc.add_paragraph(style="List Bullet")
    paragraph.paragraph_format.space_after = Pt(4)
    run = paragraph.add_run(text)
    set_font(run, size=11)
    return paragraph


def add_number(doc: Document, text: str):
    paragraph = doc.add_paragraph(style="List Number")
    paragraph.paragraph_format.space_after = Pt(4)
    run = paragraph.add_run(text)
    set_font(run, size=11)
    return paragraph


def add_table(doc: Document, headers: list[str], rows: list[list[str]], widths: list[int]):
    table = doc.add_table(rows=1, cols=len(headers))
    table.style = "Table Grid"
    table.autofit = False
    for index, header in enumerate(headers):
        cell = table.rows[0].cells[index]
        cell.vertical_alignment = WD_CELL_VERTICAL_ALIGNMENT.CENTER
        set_cell_shading(cell, "F2F4F7")
        set_cell_width(cell, widths[index])
        run = cell.paragraphs[0].add_run(header)
        set_font(run, size=10, bold=True)
    for row in rows:
        cells = table.add_row().cells
        for index, value in enumerate(row):
            set_cell_width(cells[index], widths[index])
            cells[index].vertical_alignment = WD_CELL_VERTICAL_ALIGNMENT.CENTER
            paragraph = cells[index].paragraphs[0]
            paragraph.paragraph_format.space_after = Pt(0)
            run = paragraph.add_run(value)
            set_font(run, size=10)
    doc.add_paragraph()
    return table


def build() -> None:
    REPORT_PATH.parent.mkdir(parents=True, exist_ok=True)
    doc = Document()
    section = doc.sections[0]
    section.page_width = Inches(8.5)
    section.page_height = Inches(11)
    section.top_margin = Inches(1)
    section.bottom_margin = Inches(1)
    section.left_margin = Inches(1)
    section.right_margin = Inches(1)

    styles = doc.styles
    normal = styles["Normal"]
    normal.font.name = "Calibri"
    normal._element.rPr.rFonts.set(qn("w:ascii"), "Calibri")
    normal._element.rPr.rFonts.set(qn("w:hAnsi"), "Calibri")
    normal.font.size = Pt(11)

    title = doc.add_paragraph()
    title.alignment = WD_ALIGN_PARAGRAPH.CENTER
    title.paragraph_format.space_after = Pt(3)
    run = title.add_run("Nhận biết thịt tươi bằng thị giác máy tính")
    set_font(run, size=20, bold=True)
    run.font.color.rgb = RGBColor(11, 37, 69)

    subtitle = doc.add_paragraph()
    subtitle.alignment = WD_ALIGN_PARAGRAPH.CENTER
    subtitle.paragraph_format.space_after = Pt(12)
    run = subtitle.add_run("Báo cáo bài tập môn Thị giác máy tính")
    set_font(run, size=12)
    run.font.color.rgb = RGBColor(85, 85, 85)

    add_paragraph(
        doc,
        "Báo cáo trình bày bài toán nhận biết độ tươi của thịt bò từ ảnh, phương pháp học máy với đặc trưng màu + texture và tách vùng thịt, kết quả thực nghiệm trên bộ dữ liệu thật LocBeef, ứng dụng web demo, cùng các nhận xét và hạn chế.",
    )

    add_heading(doc, "1. Bài toán", 1)
    add_paragraph(
        doc,
        "Bài toán là phân loại nhị phân ảnh thịt bò theo độ tươi. Đầu vào là ảnh RGB chụp miếng thịt trong ánh sáng thông thường; đầu ra là nhãn fresh (tươi) hoặc spoiled (hỏng/ôi). Nhãn này khớp với bộ dữ liệu thật LocBeef (fresh/rotten).",
    )
    add_paragraph(
        doc,
        "Ý nghĩa: nhận biết nhanh chất lượng thịt giúp hỗ trợ kiểm soát an toàn thực phẩm, giảm rủi ro cho người tiêu dùng, giảm lãng phí và hỗ trợ các điểm bán lẻ hoặc kho bảo quản kiểm tra sơ bộ bằng camera.",
        bold_prefix="Ý nghĩa:",
    )
    add_bullet(doc, "Tính chất thị giác quan trọng: màu đỏ/hồng của thịt tươi, màu xỉn/nâu/xám của thịt kém tươi, độ bóng bề mặt và vân cơ.")
    add_bullet(doc, "Khó khăn: ánh sáng thay đổi, nền ảnh phức tạp, khác biệt giữa các loại thịt và điều kiện chụp.")

    add_heading(doc, "2. Dữ liệu", 1)
    add_paragraph(
        doc,
        "Sử dụng bộ LocBeef - Beef Quality Image Dataset (Kaggle, tác giả mexwell): 3.268 ảnh thịt bò địa phương vùng Aceh, hai lớp fresh và rotten, đã chia sẵn train/test. Nhãn rotten được ánh xạ sang spoiled để thống nhất với ứng dụng.",
    )
    add_table(
        doc,
        ["Tập", "fresh", "rotten", "Tổng"],
        [
            ["Train", "1.144", "1.144", "2.288"],
            ["Test", "490", "490", "980"],
            ["Tổng", "1.634", "1.634", "3.268"],
        ],
        [2400, 2320, 2320, 2320],
    )
    add_paragraph(
        doc,
        "Vì kho ảnh gốc lớn (khoảng 5,5 GB), quá trình huấn luyện đọc ảnh trực tiếp từ file nén trong bộ nhớ, không giải nén ra ổ đĩa (scripts/train_locbeef_from_zip.py).",
    )

    add_heading(doc, "3. Phương pháp", 1)
    add_heading(doc, "3.1 Tiền xử lý và tách vùng thịt", 2)
    for step in [
        "Đọc ảnh, resize về 224 x 224 để chuẩn hóa đầu vào.",
        "Cân bằng sáng cục bộ bằng CLAHE trên kênh L của không gian màu Lab.",
        "Tách vùng thịt (meat-region masking): loại pixel nền quá sáng/trắng và quá tối, làm sạch bằng phép hình thái học; đặc trưng màu chỉ tính trên vùng thịt.",
    ]:
        add_number(doc, step)

    add_heading(doc, "3.2 Đặc trưng (vector 174 chiều)", 2)
    add_table(
        doc,
        ["Nhóm đặc trưng", "Chi tiết", "Số chiều"],
        [
            ["Histogram HSV", "H (32 bins, 0-179), S (16), V (16)", "64"],
            ["Histogram Lab", "L (16), a (16), b (16)", "48"],
            ["Thống kê màu", "mean, std, p10/p50/p90 trên 6 kênh HSV+Lab", "30"],
            ["Texture LBP", "Local Binary Pattern, 32 bins", "32"],
            ["Tổng", "", "174"],
        ],
        [3000, 5060, 1300],
    )
    add_paragraph(
        doc,
        "Đặc trưng màu HSV/Lab phù hợp vì thịt tươi có màu đỏ/hồng rõ, thịt hỏng ngả nâu/xám; LBP mô tả vân và độ thô mịn bề mặt vốn thay đổi khi thịt mất nước và oxy hóa.",
    )

    add_heading(doc, "3.3 Mô hình", 2)
    add_paragraph(
        doc,
        "Mô hình chính là RandomForest (300 cây, class_weight=balanced); mã nguồn cũng hỗ trợ SVM kernel RBF như lựa chọn thay thế. Đây là baseline nhẹ, chạy trên CPU, dễ giải thích. Hướng học sâu (transfer learning MobileNet/EfficientNet) có thể tổng quát tốt hơn nhưng cần dữ liệu lớn và GPU.",
    )

    add_heading(doc, "4. Kết quả", 1)
    add_paragraph(
        doc,
        "Đánh giá trên test set gốc của LocBeef gồm 980 ảnh chưa dùng khi huấn luyện:",
    )
    add_table(
        doc,
        ["Chỉ số", "fresh", "spoiled"],
        [
            ["Precision", "1.00", "0.96"],
            ["Recall", "0.96", "1.00"],
            ["F1-score", "0.98", "0.98"],
        ],
        [3200, 3080, 3080],
    )
    add_paragraph(
        doc,
        "Accuracy: 97,9% (959/980 ảnh đúng, 21 lỗi). 20 ảnh fresh bị đoán nhầm thành spoiled, không có ảnh spoiled nào bị đoán nhầm thành fresh - mô hình nghiêng về phía an toàn (thiên báo hỏng), phù hợp bài toán an toàn thực phẩm.",
        bold_prefix="Accuracy:",
    )
    if CONFUSION_MATRIX.exists():
        paragraph = doc.add_paragraph()
        paragraph.alignment = WD_ALIGN_PARAGRAPH.CENTER
        run = paragraph.add_run()
        run.add_picture(str(CONFUSION_MATRIX), width=Inches(4.4))
        caption = doc.add_paragraph()
        caption.alignment = WD_ALIGN_PARAGRAPH.CENTER
        caption_run = caption.add_run("Hình 1. Confusion matrix trên test set LocBeef (980 ảnh).")
        set_font(caption_run, size=10)
        caption_run.italic = True

    add_heading(doc, "5. Ứng dụng web demo", 1)
    add_paragraph(
        doc,
        "Repo kèm ứng dụng Flask (app.py): người dùng tải ảnh lên trình duyệt, hệ thống trả về nhãn tươi/hỏng kèm xác suất từng lớp. Ứng dụng có fallback giải mã ảnh AVIF/HEIC bằng Pillow (định dạng ảnh điện thoại/web mà OpenCV không đọc được). Chạy python app.py rồi mở http://127.0.0.1:5000.",
    )

    add_heading(doc, "6. Thảo luận và nhận xét", 1)
    add_paragraph(
        doc,
        "Ưu điểm: pipeline đơn giản, chạy nhanh trên CPU, không cần GPU, giải thích được dựa trên màu sắc/texture; đạt độ chính xác cao trên đúng phân phối dữ liệu huấn luyện.",
        bold_prefix="Ưu điểm:",
    )
    add_paragraph(doc, "Hạn chế và các điểm cần trung thực:", bold_prefix="Hạn chế và các điểm cần trung thực:")
    add_bullet(
        doc,
        "Cách chia train/test dùng phân chia có sẵn của dataset. Nếu nhiều ảnh chụp cùng một miếng thịt nằm ở cả train lẫn test, con số 97,9% có thể lạc quan hơn so với thực tế trên mẫu hoàn toàn mới.",
    )
    add_bullet(
        doc,
        "Lệch phân phối (domain shift): mô hình huấn luyện trên ảnh bò Aceh chụp khá đồng nhất. Khi thử với ảnh thịt lấy ngẫu nhiên trên web (khác camera, ánh sáng, loại thịt), độ tin cậy giảm và có trường hợp sai. Mô hình mạnh trên ảnh giống dữ liệu huấn luyện, không nên xem là bộ phân loại tổng quát.",
    )
    add_bullet(
        doc,
        "Ghi nhận khi phát triển: một lớp hybrid phân tích màu miền từng được thêm vào để hậu xử lý, nhưng khi đánh giá định lượng trên test set thật, lớp này kéo accuracy xuống 50% (ngưỡng màu chỉnh tay không khớp màu bò thật, ép hầu hết ảnh về hỏng). Vì vậy lớp hybrid đã bị loại bỏ và hệ thống dùng trực tiếp dự đoán RandomForest.",
    )
    add_paragraph(
        doc,
        "Hướng cải thiện: chia dữ liệu theo từng mẫu vật để tránh rò rỉ; tăng đa dạng dữ liệu; dùng transfer learning; thêm cơ chế từ chối dự đoán khi ảnh ngoài phân phối hoặc độ tin cậy thấp.",
    )
    add_paragraph(
        doc,
        "Kết luận: baseline màu + texture + tách vùng thịt + RandomForest đạt 97,9% trên bộ LocBeef. Hệ thống là công cụ hỗ trợ sàng lọc, không thay thế kiểm nghiệm vi sinh hoặc đánh giá an toàn thực phẩm chính thức.",
    )

    doc.add_section(WD_SECTION.NEW_PAGE)
    add_heading(doc, "Tài liệu tham khảo", 1)
    refs = [
        "LocBeef - Beef Quality Image Dataset (local Aceh beef, fresh/rotten). Kaggle. https://www.kaggle.com/datasets/mexwell/locbeef-beef-quality-image-dataset",
        "Bramantyo, H. A., Faridi, M. A., Chen, R., Harris, C., & Sun, Y. (2026). Deep Learning-Based Meat Freshness Detection with Segmentation and OOD-Aware Classification. arXiv:2603.00368.",
        "Hidalgo, M. M., Lima, R. C., De Nadai Fernandes, E. A., Bacchi, M. A., & Sarriés, G. A. (2025). Leveraging pre-trained computer vision models for accurate classification of meat freshness. Food Chemistry, 495(Pt 3), 146430.",
        "Ojala, T., Pietikäinen, M., & Mäenpää, T. (2002). Multiresolution gray-scale and rotation invariant texture classification with local binary patterns. IEEE TPAMI, 24(7), 971-987.",
    ]
    for ref in refs:
        add_number(doc, ref)

    footer = section.footer.paragraphs[0]
    footer.alignment = WD_ALIGN_PARAGRAPH.CENTER
    footer_run = footer.add_run("Báo cáo bài tập Thị giác máy tính")
    set_font(footer_run, size=9)
    footer_run.font.color.rgb = RGBColor(85, 85, 85)

    doc.save(REPORT_PATH)
    print(REPORT_PATH)


if __name__ == "__main__":
    build()

