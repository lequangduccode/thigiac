# -*- coding: utf-8 -*-
"""Sinh bao cao NCKH "Nhan biet thit tuoi" theo dung format de cuong PTIT.

Format: Times New Roman 13, gian dong 1.5, le 35/30/35/20mm, trang bia ngoai +
trong, danh so trang tu 1, cac muc I-V, Chuong 1-3 voi Gioi thieu/Noi dung/Ket
luan chuong. Nhung hinh + bang ty le %.

Usage: python scripts/build_report_nckh.py
"""
from pathlib import Path

from docx import Document
from docx.shared import Pt, Mm, Inches, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.enum.section import WD_SECTION
from docx.oxml.ns import qn
from docx.oxml import OxmlElement

FONT = "Times New Roman"
ROOT = Path(__file__).resolve().parents[1]
FIG = ROOT / "outputs" / "report_figures"
CM = ROOT / "outputs" / "locbeef_rf_v1" / "confusion_matrix.png"
OUT = ROOT / "reports" / "bao_cao_nckh_nhan_biet_thit_tuoi.docx"

doc = Document()
style = doc.styles["Normal"]
style.font.name = FONT
style.font.size = Pt(13)
style._element.rPr.rFonts.set(qn("w:eastAsia"), FONT)
style._element.rPr.rFonts.set(qn("w:cs"), FONT)
pf = style.paragraph_format
pf.line_spacing = 1.5
pf.space_before = Pt(0)
pf.space_after = Pt(0)


def set_margins(section):
    section.page_height = Mm(297)
    section.page_width = Mm(210)
    section.top_margin = Mm(35)
    section.bottom_margin = Mm(30)
    section.left_margin = Mm(35)
    section.right_margin = Mm(20)


def _run(p, text, size=13, bold=False, italic=False, upper=False):
    r = p.add_run(text.upper() if upper else text)
    r.font.name = FONT
    r.font.size = Pt(size)
    r.font.bold = bold
    r.font.italic = italic
    rpr = r._element.get_or_add_rPr()
    rf = rpr.find(qn("w:rFonts"))
    if rf is None:
        rf = OxmlElement("w:rFonts")
        rpr.append(rf)
    rf.set(qn("w:ascii"), FONT)
    rf.set(qn("w:hAnsi"), FONT)
    rf.set(qn("w:cs"), FONT)
    return r


def para(text="", align=None, bold=False, italic=False, size=13,
         indent=False, before=0, after=0, spacing=1.5):
    p = doc.add_paragraph()
    ppf = p.paragraph_format
    ppf.line_spacing = spacing
    ppf.space_before = Pt(before)
    ppf.space_after = Pt(after)
    if align is not None:
        p.alignment = align
    if indent:
        ppf.first_line_indent = Mm(10)
    if text:
        _run(p, text, size=size, bold=bold, italic=italic)
    return p


def heading(text, size=13, before=10, after=4):
    return para(text, align=WD_ALIGN_PARAGRAPH.LEFT, bold=True, size=size,
                before=before, after=after)


def center_heading(text, size=14, before=6, after=6):
    return para(text, align=WD_ALIGN_PARAGRAPH.CENTER, bold=True, size=size,
                before=before, after=after)


def body(text):
    return para(text, align=WD_ALIGN_PARAGRAPH.JUSTIFY, indent=True)


def sub_label(text):
    return para(text, bold=True, italic=True, align=WD_ALIGN_PARAGRAPH.JUSTIFY)


def figure(path, caption, width_in=5.7):
    if not Path(path).exists():
        return
    p = doc.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p.paragraph_format.space_before = Pt(6)
    p.add_run().add_picture(str(path), width=Inches(width_in))
    cap = para(caption, align=WD_ALIGN_PARAGRAPH.CENTER, italic=True, size=12,
               before=2, after=8)
    return cap


def grid_table(headers, rows, widths_mm=None):
    t = doc.add_table(rows=1, cols=len(headers))
    t.style = "Table Grid"
    for i, h in enumerate(headers):
        c = t.rows[0].cells[i]
        c.paragraphs[0].alignment = WD_ALIGN_PARAGRAPH.CENTER
        _run(c.paragraphs[0], h, bold=True, size=12)
    for row in rows:
        cells = t.add_row().cells
        for i, v in enumerate(row):
            cp = cells[i].paragraphs[0]
            if i == 0:
                cp.alignment = WD_ALIGN_PARAGRAPH.CENTER
            _run(cp, v, size=12)
    para("", after=4)
    return t


def add_page_number(paragraph):
    fld1 = OxmlElement("w:fldChar"); fld1.set(qn("w:fldCharType"), "begin")
    instr = OxmlElement("w:instrText"); instr.set(qn("xml:space"), "preserve"); instr.text = "PAGE"
    fld2 = OxmlElement("w:fldChar"); fld2.set(qn("w:fldCharType"), "end")
    r = paragraph.add_run(); r.font.name = FONT; r.font.size = Pt(13)
    r._r.append(fld1); r._r.append(instr); r._r.append(fld2)


# =====================================================================
# SECTION 1 - TRANG BIA
# =====================================================================
sec1 = doc.sections[0]
set_margins(sec1)

# ---- Trang bia ngoai ----
para("[ TÊN TRƯỜNG / HỌC VIỆN ]", WD_ALIGN_PARAGRAPH.CENTER, bold=True, size=14, before=6)
para("[ KHOA / BỘ MÔN ]", WD_ALIGN_PARAGRAPH.CENTER, bold=True, size=13)
para("---------------------------------------", WD_ALIGN_PARAGRAPH.CENTER)
para("[ Chèn logo tại đây ]", WD_ALIGN_PARAGRAPH.CENTER, italic=True, before=18, after=18)
para("(Điền họ tên sinh viên thực hiện)", WD_ALIGN_PARAGRAPH.CENTER, italic=True, size=11, after=30)
para("ĐỀ CƯƠNG NGHIÊN CỨU KHOA HỌC", WD_ALIGN_PARAGRAPH.CENTER, bold=True, size=18, before=18)
para("NHẬN BIẾT THỊT TƯƠI BẰNG THỊ GIÁC MÁY TÍNH", WD_ALIGN_PARAGRAPH.CENTER, bold=True, size=16, before=10, after=6)
para("(Học phần: Thị giác máy tính)", WD_ALIGN_PARAGRAPH.CENTER, italic=True, size=13)
para("HÀ NỘI - 2026", WD_ALIGN_PARAGRAPH.CENTER, bold=True, size=14, before=60)

doc.add_page_break()

# ---- Trang bia trong ----
para("[ TÊN TRƯỜNG / HỌC VIỆN ]", WD_ALIGN_PARAGRAPH.CENTER, bold=True, size=14, before=6)
para("[ KHOA / BỘ MÔN ]", WD_ALIGN_PARAGRAPH.CENTER, bold=True, size=13)
para("---------------------------------------", WD_ALIGN_PARAGRAPH.CENTER)
para("[ Chèn logo tại đây ]", WD_ALIGN_PARAGRAPH.CENTER, italic=True, before=12, after=12)
para("(Điền họ tên sinh viên thực hiện)", WD_ALIGN_PARAGRAPH.CENTER, italic=True, size=11, after=16)
para("NHẬN BIẾT THỊT TƯƠI BẰNG THỊ GIÁC MÁY TÍNH — PHÂN LOẠI ĐỘ TƯƠI THỊT BÒ TỪ ẢNH BẰNG ĐẶC TRƯNG MÀU, TEXTURE VÀ RANDOMFOREST",
     WD_ALIGN_PARAGRAPH.CENTER, bold=True, size=15, after=12)
para("CHUYÊN NGÀNH: [ ĐIỀN CHUYÊN NGÀNH ]", WD_ALIGN_PARAGRAPH.CENTER, size=12)
para("HỌC PHẦN: THỊ GIÁC MÁY TÍNH", WD_ALIGN_PARAGRAPH.CENTER, size=12, after=12)
para("ĐỀ CƯƠNG NGHIÊN CỨU KHOA HỌC", WD_ALIGN_PARAGRAPH.CENTER, bold=True, size=14)
para("GIẢNG VIÊN HƯỚNG DẪN: (điền học hàm, học vị, họ tên)", WD_ALIGN_PARAGRAPH.CENTER, bold=True, size=12, before=18, after=30)
para("HÀ NỘI - 2026", WD_ALIGN_PARAGRAPH.CENTER, bold=True, size=12, before=36)

# =====================================================================
# SECTION 2 - NOI DUNG (danh so trang tu 1)
# =====================================================================
new = doc.add_section(WD_SECTION.NEW_PAGE)
set_margins(new)
new.header.is_linked_to_previous = False
sec1.header.is_linked_to_previous = False
sec1.header.paragraphs[0].text = ""
hdr = new.header.paragraphs[0]
hdr.alignment = WD_ALIGN_PARAGRAPH.CENTER
add_page_number(hdr)
sectPr = new._sectPr
pgnum = OxmlElement("w:pgNumType"); pgnum.set(qn("w:start"), "1"); sectPr.append(pgnum)

# ---------------------- I. MO DAU ----------------------
center_heading("I. MỞ ĐẦU", before=0)

heading("1. Lý do chọn đề tài")
body("Chất lượng và độ an toàn của thịt ảnh hưởng trực tiếp đến sức khỏe người tiêu dùng. Thịt là môi trường giàu dinh dưỡng nên rất dễ bị vi sinh vật phân hủy; quá trình ôi thiu kèm theo các biến đổi hóa học (oxy hóa myoglobin, sinh amin, mất nước) làm thay đổi màu sắc và kết cấu bề mặt. Bằng mắt thường, người mua thường đánh giá độ tươi qua màu đỏ/hồng, độ bóng và độ đàn hồi — đây chính là các tín hiệu thị giác mà máy tính có thể học để tự động hóa việc sàng lọc.")
body("So với kiểm nghiệm hóa sinh hoặc vi sinh, phương pháp dựa trên ảnh có ưu điểm không phá hủy mẫu, chi phí thấp, cho kết quả tức thì và dễ triển khai bằng camera phổ thông hoặc điện thoại. Bên cạnh ý nghĩa về sức khỏe, bài toán còn giúp giảm lãng phí thực phẩm, tối ưu luân chuyển hàng trong kho và giảm phụ thuộc vào đánh giá cảm quan chủ quan của từng người.")
body("Vì vậy, việc nghiên cứu và xây dựng một hệ thống nhận biết độ tươi của thịt từ ảnh vừa có ý nghĩa khoa học (đề xuất quy trình trích đặc trưng và đánh giá phù hợp), vừa có ý nghĩa thực tiễn cao và có tính khả thi (tận dụng được các kỹ thuật xử lý ảnh và học máy sẵn có, chạy được trên CPU mà không cần GPU).")

heading("2. Tổng quan về vấn đề nghiên cứu")
body("Đánh giá độ tươi thịt bằng ảnh đã được nghiên cứu theo hai hướng chính. Hướng đặc trưng thủ công kết hợp học máy sử dụng màu sắc (RGB/HSV/Lab), thống kê và texture (LBP, GLCM) làm đầu vào cho SVM, RandomForest hoặc k-NN; ưu điểm là nhẹ, dễ giải thích, phù hợp dữ liệu vừa và nhỏ. Hướng học sâu dùng mạng tích chập (ResNet, EfficientNet, MobileNet) hoặc Transformer để tự học đặc trưng, thường cho độ chính xác cao hơn khi có dữ liệu lớn và GPU.")
body("Một điểm chung của các nghiên cứu là nhấn mạnh vai trò của màu sắc — đặc biệt độ đỏ liên quan tới myoglobin — như tín hiệu chủ đạo, đồng thời cảnh báo rủi ro mô hình học nhầm đặc trưng nền hoặc điều kiện chụp. Các công trình gần đây còn kết hợp phân vùng (segmentation) để tách vùng thịt và bổ sung cơ chế phát hiện mẫu ngoài phân phối nhằm tăng độ tin cậy khi triển khai.")
body("Qua khảo sát, có thể thấy khoảng trống cần giải quyết gồm: (i) cần một quy trình đặc trưng gọn nhưng đủ mạnh cho ảnh thịt thật; (ii) cần loại bỏ ảnh hưởng của nền để mô hình tập trung vào vùng thịt; (iii) cần đánh giá định lượng trung thực trên dữ liệu thật thay vì heuristic cảm tính. Đề tài tập trung vào các vấn đề này với bộ dữ liệu ảnh thịt bò thật.")

heading("3. Mục đích nghiên cứu")
body("Mục tiêu tổng quát là nghiên cứu và xây dựng được một hệ thống thị giác máy tính nhận biết độ tươi của thịt bò từ ảnh, phân loại nhị phân thành tươi (fresh) hoặc hỏng (spoiled), kèm ứng dụng minh họa. Các kết quả cụ thể cần đạt gồm:")
body("Về mặt lý luận: hệ thống hóa cơ sở lý thuyết về không gian màu, cân bằng sáng CLAHE, đặc trưng texture LBP và các bộ phân loại học máy; đề xuất quy trình tách vùng thịt và trích đặc trưng phù hợp với ảnh thịt thật.")
body("Về mặt thực tiễn: xây dựng được hệ thống thử nghiệm hoạt động trên bộ dữ liệu ảnh thịt bò thật; đánh giá định lượng theo accuracy, precision, recall, F1-score và confusion matrix; đóng gói thành ứng dụng web cho phép tải ảnh và xem kết quả.")

heading("4. Đối tượng và phạm vi nghiên cứu")
body("Đối tượng nghiên cứu: quy trình trích đặc trưng màu và texture cho ảnh thịt; kỹ thuật tách vùng thịt khỏi nền; các bộ phân loại học máy (RandomForest, SVM) cho bài toán nhận biết độ tươi.")
body("Phạm vi nghiên cứu: Về nội dung, đề tài tập trung vào phân loại nhị phân tươi/hỏng bằng đặc trưng thủ công + học máy, không huấn luyện mô hình học sâu từ đầu. Về dữ liệu, thực nghiệm tiến hành trên bộ LocBeef gồm 3.268 ảnh thịt bò địa phương. Về công cụ, hệ thống chạy hoàn toàn trên CPU bằng Python và các thư viện mã nguồn mở.")

heading("5. Phương pháp nghiên cứu")
body("Phương pháp nghiên cứu lý thuyết: thu thập, tổng hợp và phân tích các tài liệu về không gian màu, CLAHE, LBP và các thuật toán phân loại để xây dựng cơ sở lý luận và lựa chọn giải pháp phù hợp.")
body("Phương pháp thực nghiệm: thiết kế và cài đặt pipeline xử lý ảnh; huấn luyện mô hình trên tập train và đánh giá trên tập test độc lập; so sánh các cấu hình đặc trưng và mô hình.")
body("Phương pháp đánh giá và thống kê: sử dụng các độ đo accuracy, precision, recall, F1-score và confusion matrix; phân tích độ quan trọng đặc trưng và phân tích lỗi để rút ra nhận định.")
body("Công cụ và môi trường: ngôn ngữ Python; thư viện OpenCV và NumPy cho xử lý ảnh; scikit-learn cho huấn luyện; Matplotlib cho biểu đồ; Flask và Pillow cho ứng dụng web; joblib để lưu mô hình.")

# ---------------------- II. NOI DUNG ----------------------
center_heading("II. NỘI DUNG", before=12)
body("Đề tài được cấu trúc thành ba chương với nội dung chính như sau:")

# ---- Chuong 1 ----
heading("Chương 1: CƠ SỞ LÝ LUẬN")
sub_label("Giới thiệu chương:")
body("Trình bày mục tiêu và bố cục của chương; giới thiệu các khái niệm nền tảng về màu sắc, cân bằng sáng, đặc trưng texture và bộ phân loại làm cơ sở cho phương pháp đề xuất ở Chương 2.")
sub_label("Nội dung:")
body("Không gian màu: RGB trộn lẫn độ sáng và sắc màu nên nhạy với chiếu sáng; HSV tách riêng sắc độ, độ bão hòa và độ sáng; CIELAB có kênh a* mô tả độ đỏ liên hệ trực tiếp với trạng thái myoglobin của thịt. Đây là cơ sở để chọn đặc trưng màu.")
body("Cân bằng sáng CLAHE: kỹ thuật cân bằng histogram thích nghi theo vùng, có giới hạn tương phản để tránh khuếch đại nhiễu, áp trên kênh L của Lab nhằm giảm ảnh hưởng chiếu sáng không đều mà vẫn giữ thông tin màu.")
body("Đặc trưng texture LBP: với điểm trung tâm g_c và 8 lân cận, mã LBP = Σ s(g_i − g_c)·2^i với s(x)=1 nếu x≥0. Histogram mã LBP mô tả độ thô/mịn, vân cơ và đốm bề mặt — các đặc điểm thay đổi khi thịt mất nước và oxy hóa.")
body("Bộ phân loại: RandomForest là tập hợp nhiều cây quyết định huấn luyện trên mẫu bootstrap và tập con đặc trưng ngẫu nhiên, tách nút theo độ vẩn đục Gini = 1 − Σ p_k²; ưu điểm là mạnh với đặc trưng không đồng nhất, ít overfit và cung cấp độ quan trọng đặc trưng. SVM kernel RBF là lựa chọn thay thế nhưng cần chuẩn hóa và nhạy tham số.")
body("Chỉ số đánh giá: Accuracy = (TP+TN)/(tổng); Precision = TP/(TP+FP); Recall = TP/(TP+FN); F1 = 2·P·R/(P+R); confusion matrix cho biết lớp nào hay bị nhầm. Với an toàn thực phẩm, recall lớp 'hỏng' đặc biệt quan trọng.")
sub_label("Kết luận chương.")

# ---- Chuong 2 ----
heading("Chương 2: PHƯƠNG PHÁP ĐỀ XUẤT")
sub_label("Giới thiệu chương:")
body("Trình bày pipeline xử lý, bước tách vùng thịt, tập đặc trưng 174 chiều và cách huấn luyện mô hình.")
sub_label("Nội dung:")
body("Pipeline gồm sáu bước: đọc ảnh và resize 224×224; cân bằng sáng CLAHE; tách vùng thịt; trích đặc trưng màu và texture trên vùng thịt; ghép thành vector 174 chiều; phân loại bằng RandomForest và đánh giá.")
figure(FIG / "pipeline_diagram.png", "Hình 2.1. Sơ đồ khối tổng quan của pipeline.", 6.4)
body("Tách vùng thịt: loại pixel quá sáng và ít bão hòa (nền/đĩa trắng) và pixel quá tối (bóng), làm sạch bằng phép hình thái học mở rồi đóng; nếu vùng thịt nhỏ hơn 3% diện tích thì dùng toàn ảnh để tránh mất dữ liệu. Nhờ đó mô hình không học nhầm màu nền.")
figure(FIG / "preprocessing.png", "Hình 2.2. Tiền xử lý: ảnh gốc → CLAHE → mask vùng thịt → vùng thịt giữ lại.", 6.5)
body("Tập đặc trưng gồm bốn nhóm, tổng 174 chiều; histogram từng kênh được chuẩn hóa theo mật độ để bất biến với số lượng pixel vùng thịt:")
grid_table(
    ["Nhóm đặc trưng", "Chi tiết", "Số chiều", "Tỷ lệ"],
    [
        ["Histogram HSV", "H (32), S (16), V (16)", "64", "36,8%"],
        ["Histogram Lab", "L (16), a (16), b (16)", "48", "27,6%"],
        ["Thống kê màu", "mean, std, p10/p50/p90 × 6 kênh", "30", "17,2%"],
        ["Texture LBP", "LBP 32 bins", "32", "18,4%"],
        ["Tổng cộng", "", "174", "100%"],
    ],
)
body("Huấn luyện: RandomForest 300 cây, class_weight='balanced', random_state cố định. Mô hình được huấn luyện trên tập train và đánh giá trên tập test độc lập; riêng mô hình đóng gói kèm ứng dụng được huấn luyện lại trên toàn bộ dữ liệu để tận dụng tối đa mẫu.")
sub_label("Kết luận chương.")

# ---- Chuong 3 ----
heading("Chương 3: THỰC NGHIỆM VÀ ĐÁNH GIÁ")
sub_label("Giới thiệu chương:")
body("Trình bày bộ dữ liệu, thiết lập thực nghiệm, kết quả định lượng, phân tích lỗi và ứng dụng web demo.")
sub_label("Nội dung:")
body("Bộ dữ liệu LocBeef (Kaggle) gồm 3.268 ảnh thịt bò Aceh, hai lớp fresh và rotten (ánh xạ sang spoiled), đã chia sẵn train/test. Hai lớp cân bằng hoàn hảo nên accuracy là chỉ số đánh giá hợp lý.")
grid_table(
    ["Tập", "fresh", "rotten", "Tổng", "Tỷ lệ"],
    [
        ["Train", "1.144", "1.144", "2.288", "70,0%"],
        ["Test", "490", "490", "980", "30,0%"],
        ["Tổng", "1.634", "1.634", "3.268", "100%"],
    ],
)
body("Tỷ lệ hai lớp là 50,0% fresh và 50,0% spoiled trên toàn bộ dữ liệu.")
figure(FIG / "dataset_samples.png", "Hình 3.1. Ảnh mẫu LocBeef: hàng trên tươi, hàng dưới hỏng.", 6.2)
figure(FIG / "eda_scatter.png", "Hình 3.2. Phân bố màu vùng thịt (a*, L*): hai lớp tách biệt khá rõ.", 5.4)
body("Kết quả trên tập test 980 ảnh: accuracy đạt 97,9% (959/980 ảnh đúng, 21 lỗi). Bảng dưới trình bày các chỉ số theo lớp dưới dạng phần trăm:")
grid_table(
    ["Chỉ số", "fresh", "spoiled"],
    [
        ["Precision", "100,0%", "95,9%"],
        ["Recall", "95,7%", "100,0%"],
        ["F1-score", "97,8%", "97,9%"],
        ["Accuracy chung", "97,9%", "97,9%"],
    ],
)
body("Confusion matrix cho thấy toàn bộ 490 ảnh hỏng được nhận đúng (469 ảnh tươi đúng); 21 ảnh tươi bị đoán nhầm thành hỏng và không có ảnh hỏng nào bị đoán nhầm thành tươi. Mô hình nghiêng về phía thận trọng (thiên báo hỏng), phù hợp bài toán an toàn thực phẩm.")
figure(CM, "Hình 3.3. Confusion matrix trên tập test LocBeef (980 ảnh).", 4.5)
body("Phân tích độ quan trọng đặc trưng của RandomForest theo nhóm: đặc trưng màu chiếm tới 96,4% quyết định (HSV 56,5%, thống kê màu 27,4%, Lab 12,6%), trong khi texture LBP chỉ đóng góp 3,6%. Kết quả phù hợp trực giác: màu là dấu hiệu chính phân biệt tươi và hỏng.")
grid_table(
    ["Nhóm đặc trưng", "Độ quan trọng"],
    [
        ["Histogram HSV", "56,5%"],
        ["Thống kê màu", "27,4%"],
        ["Histogram Lab", "12,6%"],
        ["Texture LBP", "3,6%"],
        ["Tổng nhóm màu", "96,4%"],
    ],
)
figure(FIG / "feature_importance.png", "Hình 3.4. Đóng góp của từng nhóm đặc trưng vào mô hình.", 5.6)
body("Phân tích lỗi: cả 21 lỗi đều là ảnh tươi bị phân loại thành hỏng, thường do miếng thịt sẫm màu hơn trung bình hoặc bị bóng/thiếu sáng cục bộ khiến độ đỏ đo được thấp đi — các trường hợp ở vùng chuyển tiếp về màu.")
body("Ứng dụng web demo: người dùng tải ảnh lên trình duyệt và nhận nhãn tươi/hỏng kèm xác suất từng lớp. Các hình dưới minh họa giao diện thực tế khi phân tích ảnh thịt tươi và thịt hỏng.")
figure(FIG / "web_result_fresh.png", "Hình 3.5. Kết quả web cho ảnh thịt tươi (nhãn 'Tươi', xác suất cao ở lớp Tươi).", 6.2)
figure(FIG / "web_result_spoiled.png", "Hình 3.6. Kết quả web cho ảnh thịt hỏng (nhãn 'Hỏng', xác suất cao ở lớp Hỏng).", 6.2)
figure(FIG / "demo_predictions.png", "Hình 3.7. Dự đoán trên 6 ảnh test: tất cả đều đúng (✓).", 6.2)
body("Kiểm tra tổng quát hóa: khi thử với ảnh thịt lấy ngẫu nhiên trên web (khác camera, ánh sáng, loại thịt), độ tin cậy giảm rõ và xuất hiện lỗi. Mô hình mạnh trên ảnh giống phân phối huấn luyện, chưa tổng quát cho mọi điều kiện.")
sub_label("Kết luận chương.")

# ---------------------- III. KET LUAN ----------------------
center_heading("III. KẾT LUẬN", before=12)
body("Đề tài đã đạt được các kết quả chính: (i) hệ thống hóa cơ sở lý luận về đặc trưng màu, CLAHE, LBP và bộ phân loại học máy cho bài toán nhận biết độ tươi thịt; (ii) đề xuất pipeline tách vùng thịt + đặc trưng 174 chiều + RandomForest; (iii) xây dựng hệ thống thử nghiệm đạt 97,9% accuracy trên tập test LocBeef và đóng gói thành ứng dụng web.")
body("Về hạn chế: kết quả dựa trên phân chia train/test có sẵn nên có thể lạc quan nếu tồn tại ảnh cùng mẫu vật ở cả hai tập; mô hình bị giảm hiệu năng khi gặp ảnh lệch phân phối. Ngoài ra, một lớp hậu xử lý màu 'hybrid' từng được thử nhưng bị loại bỏ do làm accuracy tụt xuống 50% trên dữ liệu thật — minh chứng cho tầm quan trọng của đánh giá định lượng.")
body("Hướng nghiên cứu tiếp theo: chia dữ liệu theo từng mẫu vật để loại rò rỉ; tăng cường và đa dạng hóa dữ liệu; áp dụng transfer learning (MobileNetV3, EfficientNet); bổ sung cơ chế từ chối dự đoán khi ảnh ngoài phân phối. Hệ thống là công cụ hỗ trợ sàng lọc, không thay thế kiểm nghiệm vi sinh chính thức.")

# ---------------------- IV. TAI LIEU THAM KHAO ----------------------
center_heading("IV. DANH MỤC CÁC TÀI LIỆU THAM KHẢO", before=12)


def ref(text):
    p = doc.add_paragraph()
    ppf = p.paragraph_format
    ppf.line_spacing = 1.5
    ppf.space_after = Pt(2)
    ppf.left_indent = Mm(10)
    ppf.first_line_indent = Mm(-10)
    _run(p, text, size=13)
    return p


para("Tiếng Anh", bold=True, before=4)
ref("[1] Ojala T., Pietikäinen M., Mäenpää T. (2002), “Multiresolution gray-scale and rotation invariant texture classification with local binary patterns”, IEEE TPAMI, 24(7), pp. 971-987.")
ref("[2] Breiman L. (2001), “Random Forests”, Machine Learning, 45(1), pp. 5-32.")
ref("[3] Zuiderveld K. (1994), “Contrast Limited Adaptive Histogram Equalization”, Graphics Gems IV, pp. 474-485.")
ref("[4] Bramantyo H. A., et al. (2026), “Deep Learning-Based Meat Freshness Detection with Segmentation and OOD-Aware Classification”, arXiv:2603.00368.")
ref("[5] Hidalgo M. M., et al. (2025), “Leveraging pre-trained computer vision models for accurate classification of meat freshness”, Food Chemistry, 495(Pt 3), 146430.")
para("Tài liệu Internet", bold=True, before=6)
ref("[6] LocBeef — Beef Quality Image Dataset. Kaggle. <https://www.kaggle.com/datasets/mexwell/locbeef-beef-quality-image-dataset>. Truy cập ngày 02 tháng 8 năm 2026.")

# ---------------------- V. KE HOACH ----------------------
center_heading("V. DỰ KIẾN KẾ HOẠCH THỰC HIỆN", before=12)
table = doc.add_table(rows=1, cols=3)
table.style = "Table Grid"
for c, t in zip(table.rows[0].cells, ["TT", "Nội dung", "Thời gian thực hiện"]):
    c.paragraphs[0].alignment = WD_ALIGN_PARAGRAPH.CENTER
    _run(c.paragraphs[0], t, bold=True, size=12)
for tt, nd, tg in [
    ("1", "Nghiên cứu tài liệu, chọn đề tài, xây dựng đề cương", "Tuần 1 - 2"),
    ("2", "Thu thập, chuẩn bị bộ dữ liệu LocBeef", "Tuần 3"),
    ("3", "Cài đặt pipeline trích đặc trưng và tách vùng thịt", "Tuần 4 - 5"),
    ("4", "Huấn luyện, đánh giá mô hình và phân tích kết quả", "Tuần 6 - 7"),
    ("5", "Xây dựng ứng dụng web demo", "Tuần 8"),
    ("6", "Viết báo cáo, hoàn thiện và thuyết trình", "Tuần 9 - 10"),
]:
    cells = table.add_row().cells
    p0 = cells[0].paragraphs[0]; p0.alignment = WD_ALIGN_PARAGRAPH.CENTER; _run(p0, tt, size=12)
    _run(cells[1].paragraphs[0], nd, size=12)
    p2 = cells[2].paragraphs[0]; p2.alignment = WD_ALIGN_PARAGRAPH.CENTER; _run(p2, tg, size=12)

para("")
sig = doc.add_table(rows=1, cols=2)
for c, lines in [
    (sig.rows[0].cells[0], ["Ý KIẾN CỦA", "GIẢNG VIÊN HƯỚNG DẪN", "(Ký ghi rõ họ tên)"]),
    (sig.rows[0].cells[1], ["SINH VIÊN THỰC HIỆN", "", "(Ký ghi rõ họ tên)"]),
]:
    for i, ln in enumerate(lines):
        p = c.paragraphs[0] if i == 0 else c.add_paragraph()
        p.alignment = WD_ALIGN_PARAGRAPH.CENTER
        _run(p, ln, bold=(i < 2), italic=(i == 2), size=12)

OUT.parent.mkdir(parents=True, exist_ok=True)
doc.save(OUT)
print("Saved:", OUT)
