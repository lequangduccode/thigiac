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
CONFUSION_MATRIX = ROOT / "outputs" / "demo_v2" / "confusion_matrix.png"


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
        "Đề tài được chọn từ nhóm nhận dạng thực phẩm tươi trong ảnh đề bài. Báo cáo trình bày bài toán, phương pháp học máy/học sâu, thử nghiệm, kết quả và nhận xét; độ dài thiết kế dưới 20 trang.",
    )

    add_heading(doc, "1. Bài toán", 1)
    add_paragraph(
        doc,
        "Bài toán là phân loại ảnh thịt theo mức độ tươi. Đầu vào là ảnh RGB chụp miếng thịt trong điều kiện ánh sáng thông thường; đầu ra là nhãn fresh, half_fresh hoặc spoiled. Với bài toán đơn giản hơn, có thể gom thành hai lớp fresh và spoiled.",
    )
    add_paragraph(
        doc,
        "Ý nghĩa: nhận biết nhanh chất lượng thịt giúp hỗ trợ kiểm soát an toàn thực phẩm, giảm rủi ro cho người tiêu dùng, giảm lãng phí và hỗ trợ các điểm bán lẻ hoặc kho bảo quản kiểm tra sơ bộ bằng camera.",
        bold_prefix="Ý nghĩa:",
    )
    add_bullet(doc, "Tính chất thị giác quan trọng: màu đỏ/hồng của thịt tươi, màu xỉn/nâu/xám của thịt kém tươi, độ bóng bề mặt, vân cơ và các đốm lạ.")
    add_bullet(doc, "Khó khăn: ánh sáng thay đổi, nền ảnh phức tạp, phản chiếu từ bao bì, khác biệt giữa các loại thịt và nhãn dữ liệu có thể không đồng nhất.")

    add_heading(doc, "2. Phương pháp", 1)
    add_heading(doc, "2.1 Pipeline xử lý", 2)
    for step in [
        "Đọc ảnh, resize về 224 x 224 để đầu vào thống nhất.",
        "Cân bằng sáng cục bộ bằng CLAHE trên kênh L của không gian màu Lab.",
        "Trích xuất đặc trưng màu HSV, Lab, thống kê kênh màu và texture LBP.",
        "Chuẩn hóa vector đặc trưng, huấn luyện SVM kernel RBF hoặc RandomForest.",
        "Đánh giá bằng accuracy, precision, recall, F1-score và confusion matrix.",
    ]:
        add_number(doc, step)

    add_heading(doc, "2.2 Đặc trưng sử dụng", 2)
    add_table(
        doc,
        ["Nhóm đặc trưng", "Mục đích", "Lý do phù hợp"],
        [
            ["HSV histogram", "Mô tả phân bố sắc độ, độ bão hòa và độ sáng", "Thịt tươi thường có màu hồng/đỏ rõ hơn, thịt hỏng thường xỉn màu."],
            ["Lab histogram", "Tách sáng và thành phần màu", "Giúp giảm ảnh hưởng của thay đổi chiếu sáng so với RGB thuần."],
            ["Thống kê màu", "Mean, std, percentile trên HSV/Lab", "Tạo đặc trưng gọn, dễ học với SVM/RandomForest."],
            ["LBP texture", "Mô tả vân, độ thô mịn và đốm bề mặt", "Hữu ích khi bề mặt thịt thay đổi trong quá trình giảm độ tươi."],
        ],
        [1800, 3300, 4260],
    )

    add_heading(doc, "2.3 Mô hình học sâu liên quan", 2)
    add_paragraph(
        doc,
        "Các nghiên cứu gần đây dùng transfer learning từ ResNet, EfficientNet, MobileNet hoặc Transformer để phân loại độ tươi thịt. Hướng học sâu có thể tự học đặc trưng phức tạp hơn, nhưng cần dataset lớn và nên có GPU. Với bài tập này, baseline màu + texture + SVM được chọn vì nhẹ, dễ chạy và dễ giải thích.",
    )
    add_paragraph(
        doc,
        "Một hướng nâng cấp quan trọng là segmentation: tách vùng thịt trước khi phân loại để giảm nhiễu nền, đặc biệt khi ảnh có khay, bao bì hoặc phản chiếu.",
    )

    add_heading(doc, "3. Thử nghiệm", 1)
    add_heading(doc, "3.1 Dữ liệu", 2)
    add_paragraph(
        doc,
        "Dataset thật khuyến nghị: Kaggle Meat Quality Assessment Dataset hoặc Meat Freshness Image Dataset. Cấu trúc thư mục trong repo yêu cầu mỗi lớp là một thư mục con, ví dụ data/meat_dataset/fresh, data/meat_dataset/half_fresh, data/meat_dataset/spoiled.",
    )
    add_paragraph(
        doc,
        "Do chưa có ảnh thịt thật trong workspace, repo có script sinh dataset minh họa để kiểm thử pipeline kỹ thuật. Kết quả minh họa không được xem là kết luận khoa học về thịt thật.",
    )
    add_heading(doc, "3.2 Kết quả kiểm thử pipeline", 2)
    add_table(
        doc,
        ["Mục", "Giá trị"],
        [
            ["Dataset demo", "135 ảnh sinh tự động, 3 lớp fresh/half_fresh/spoiled"],
            ["Chia dữ liệu", "80% train, 20% test, stratify theo nhãn"],
            ["Mô hình", "SVM kernel RBF, class_weight=balanced"],
            ["Accuracy demo", "92.59%"],
            ["Dự đoán mẫu", "fresh_000.png -> fresh, xác suất fresh 0.995"],
        ],
        [2300, 7060],
    )
    if CONFUSION_MATRIX.exists():
        paragraph = doc.add_paragraph()
        paragraph.alignment = WD_ALIGN_PARAGRAPH.CENTER
        run = paragraph.add_run()
        run.add_picture(str(CONFUSION_MATRIX), width=Inches(4.8))
        caption = doc.add_paragraph()
        caption.alignment = WD_ALIGN_PARAGRAPH.CENTER
        caption_run = caption.add_run("Hình 1. Confusion matrix trên dataset minh họa.")
        set_font(caption_run, size=10)
        caption_run.italic = True

    add_heading(doc, "4. Thảo luận và nhận xét", 1)
    add_paragraph(
        doc,
        "Ưu điểm của phương pháp là đơn giản, chạy nhanh trên CPU, dễ triển khai và giải thích được bằng các dấu hiệu màu sắc/texture. Đây là baseline phù hợp để so sánh trước khi chuyển sang mô hình học sâu.",
    )
    add_paragraph(
        doc,
        "Hạn chế là mô hình nhạy với ánh sáng, góc chụp, nền ảnh và loại thịt. Nếu dataset nhỏ hoặc ít đa dạng, mô hình có thể học nhầm màu nền/bao bì thay vì đặc trưng của thịt.",
    )
    add_paragraph(
        doc,
        "Hướng cải thiện gồm: tăng dữ liệu, chuẩn hóa điều kiện chụp, dùng segmentation để tách vùng thịt, áp dụng transfer learning với MobileNetV3/EfficientNet-B0 và thêm cơ chế từ chối dự đoán khi ảnh có độ tin cậy thấp.",
    )
    add_paragraph(
        doc,
        "Kết luận: nhận biết thịt tươi bằng ảnh là bài toán có ý nghĩa thực tế. Pipeline màu + texture + SVM là nền tảng tốt cho bài tập; với dataset thật lớn hơn, học sâu kết hợp segmentation sẽ có khả năng tổng quát tốt hơn.",
    )

    doc.add_section(WD_SECTION.NEW_PAGE)
    add_heading(doc, "Tài liệu tham khảo", 1)
    refs = [
        "Bramantyo, H. A., Faridi, M. A., Chen, R., Harris, C., & Sun, Y. (2026). Deep Learning-Based Meat Freshness Detection with Segmentation and OOD-Aware Classification. arXiv:2603.00368.",
        "Hidalgo, M. M., Lima, R. C., De Nadai Fernandes, E. A., Bacchi, M. A., & Sarriés, G. A. (2025). Leveraging pre-trained computer vision models for accurate classification of meat freshness. Food Chemistry, 495(Pt 3), 146430.",
        "Kaggle. Meat Quality Assessment Dataset. https://www.kaggle.com/datasets/crowww/meat-quality-assessment-based-on-deep-learning",
        "Kaggle. Meat Freshness Image Dataset. https://www.kaggle.com/datasets/vinayakshanawad/meat-freshness-image-dataset",
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

