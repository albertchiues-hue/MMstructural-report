#!/usr/bin/env python3
"""Create editable PDF form for mammography abnormal case report
(健康署婦女乳房X光攝影檢查服務異常個案報告表) with AcroForm fields."""

from reportlab.lib.pagesizes import A4
from reportlab.lib.colors import black, white, HexColor
from reportlab.pdfgen.canvas import Canvas
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfbase import pdfmetrics

# ── Constants ──
PAGE_W, PAGE_H = A4  # 595.27 x 841.89
MARGIN_L = 28
MARGIN_R = 28
MARGIN_T = 23
MARGIN_B = 17
CONTENT_W = PAGE_W - MARGIN_L - MARGIN_R
GREY_BG = HexColor('#D9D9D9')
LIGHT_GREY = HexColor('#E8E8E8')
CB_SIZE = 10
FONT_NAME = 'MSJhengHei'
OUTPUT = '/Users/chiutsecheng/MMstructural report/mammography_report_form.pdf'

# ── Font registration ──
pdfmetrics.registerFont(TTFont(FONT_NAME, '/Library/Fonts/Microsoft/Microsoft Jhenghei.ttf'))

# ── Create canvas ──
c = Canvas(OUTPUT, pagesize=A4)
c.setTitle('健康署婦女乳房X光攝影檢查服務異常個案報告表')
form = c.acroForm

y = PAGE_H - MARGIN_T  # start from top


# ══════════════════════════════════════════════
# Helper functions
# ══════════════════════════════════════════════
def draw_rect_fill(x, ry, w, h, color):
    c.setFillColor(color)
    c.rect(x, ry, w, h, fill=1, stroke=0)
    c.setFillColor(black)


def draw_cell(x, cy, w, h, text='', size=11, align='left', bg=None):
    """Draw a bordered cell with optional text and background."""
    if bg:
        draw_rect_fill(x, cy, w, h, bg)
    c.setStrokeColor(black)
    c.setLineWidth(0.5)
    c.rect(x, cy, w, h, fill=0, stroke=1)
    if text:
        c.setFont(FONT_NAME, size)
        ty = cy + h / 2 - size * 0.35
        if align == 'center':
            c.drawCentredString(x + w / 2, ty, text)
        elif align == 'right':
            c.drawRightString(x + w - 3, ty, text)
        else:
            c.drawString(x + 3, ty, text)


def add_checkbox(x, cy, name, size=CB_SIZE):
    """Add an AcroForm checkbox at position."""
    form.checkbox(
        name=name, x=x, y=cy,
        size=size,
        buttonStyle='check',
        borderColor=black,
        fillColor=white,
        borderWidth=0.5,
        forceBorder=True,
    )


def add_textfield(x, ty, w, h, name, max_len=0, font_size=10):
    """Add an AcroForm text field."""
    form.textfield(
        name=name, x=x, y=ty,
        width=w, height=h,
        fontSize=font_size,
        borderWidth=0.5,
        borderColor=black,
        fillColor=white,
        forceBorder=True,
        maxlen=max_len if max_len else 0,
    )


def checkbox_with_label(x, cy, name, label, size=CB_SIZE, font_size=11):
    """Draw checkbox + label text, return x after label for chaining."""
    add_checkbox(x, cy, name, size)
    c.setFont(FONT_NAME, font_size)
    label_x = x + size + 2
    c.drawString(label_x, cy + size / 2 - font_size * 0.35, label)
    return label_x + c.stringWidth(label, FONT_NAME, font_size) + 8


def draw_header_row(hy, h, text, size=13):
    """Draw a full-width grey header bar."""
    draw_cell(MARGIN_L, hy, CONTENT_W, h, text, size=size, align='center', bg=GREY_BG)


# ══════════════════════════════════════════════
# TITLE
# ══════════════════════════════════════════════
title_h = 20
y -= title_h
c.setFont(FONT_NAME, 16)
c.drawCentredString(PAGE_W / 2, y + 4, '健康署婦女乳房X光攝影檢查服務異常個案報告表')

# 病歷號 field (right side)
y -= 18
c.setFont(FONT_NAME, 12)
mrn_label_x = PAGE_W - MARGIN_R - 170
c.drawString(mrn_label_x, y + 3, '病歷號：')
add_textfield(mrn_label_x + 58, y, 112, 16, 'patient_mrn', font_size=11)

# ══════════════════════════════════════════════
# SECTION 1: 檢查資訊
# ══════════════════════════════════════════════
y -= 4
ROW_H = 20
header_h = 20

# Header row
y -= header_h
draw_header_row(y, header_h, '檢查資訊', size=13)

# Column widths for patient info
col0_w = 70   # label column
col1_w = 140  # value column
col2_w = 100  # label column 2
digit_w = (CONTENT_W - col0_w - col1_w - col2_w) / 10  # 10 digit cells

# Row 1: 姓名 | (name field) | 身份證統一編號 | 10 digit cells
y -= ROW_H
draw_cell(MARGIN_L, y, col0_w, ROW_H, '姓名', size=11, align='center', bg=LIGHT_GREY)
draw_cell(MARGIN_L + col0_w, y, col1_w, ROW_H)
add_textfield(MARGIN_L + col0_w + 2, y + 1, col1_w - 4, ROW_H - 2, 'patient_name', font_size=10)
draw_cell(MARGIN_L + col0_w + col1_w, y, col2_w, ROW_H, '身份證統一編號', size=10, align='center', bg=LIGHT_GREY)
id_start_x = MARGIN_L + col0_w + col1_w + col2_w
for i in range(10):
    dx = id_start_x + i * digit_w
    draw_cell(dx, y, digit_w, ROW_H)
    add_textfield(dx + 1, y + 1, digit_w - 2, ROW_H - 2, f'id_digit_{i}', max_len=1, font_size=11)

# Row 2: (empty) | (empty) | 統一證號(外籍) | 10 digit cells
y -= ROW_H
draw_cell(MARGIN_L, y, col0_w, ROW_H, '', bg=LIGHT_GREY)
draw_cell(MARGIN_L + col0_w, y, col1_w, ROW_H)
draw_cell(MARGIN_L + col0_w + col1_w, y, col2_w, ROW_H, '統一證號(外籍)', size=9, align='center', bg=LIGHT_GREY)
for i in range(10):
    dx = id_start_x + i * digit_w
    draw_cell(dx, y, digit_w, ROW_H)
    add_textfield(dx + 1, y + 1, digit_w - 2, ROW_H - 2, f'foreign_id_{i}', max_len=1, font_size=11)

# Row 3: 出生日期 | year/month/day | 攝影日期 | year/month/day
y -= ROW_H
half_w = CONTENT_W / 2
label_w3 = 70
field_w3 = half_w - label_w3

draw_cell(MARGIN_L, y, label_w3, ROW_H, '出生日期', size=11, align='center', bg=LIGHT_GREY)
draw_cell(MARGIN_L + label_w3, y, field_w3, ROW_H)
fx = MARGIN_L + label_w3 + 6
add_textfield(fx, y + 2, 42, ROW_H - 4, 'dob_year', font_size=10)
c.setFont(FONT_NAME, 11)
c.drawString(fx + 44, y + 6, '年')
add_textfield(fx + 60, y + 2, 30, ROW_H - 4, 'dob_month', font_size=10)
c.drawString(fx + 92, y + 6, '月')
add_textfield(fx + 108, y + 2, 30, ROW_H - 4, 'dob_day', font_size=10)
c.drawString(fx + 140, y + 6, '日')

draw_cell(MARGIN_L + half_w, y, label_w3, ROW_H, '攝影日期', size=11, align='center', bg=LIGHT_GREY)
draw_cell(MARGIN_L + half_w + label_w3, y, field_w3, ROW_H)
fx2 = MARGIN_L + half_w + label_w3 + 6
add_textfield(fx2, y + 2, 42, ROW_H - 4, 'exam_year', font_size=10)
c.setFont(FONT_NAME, 11)
c.drawString(fx2 + 44, y + 6, '年')
add_textfield(fx2 + 60, y + 2, 30, ROW_H - 4, 'exam_month', font_size=10)
c.drawString(fx2 + 92, y + 6, '月')
add_textfield(fx2 + 108, y + 2, 30, ROW_H - 4, 'exam_day', font_size=10)
c.drawString(fx2 + 140, y + 6, '日')

# Row 4: 醫院名稱 | (field) | 放射科醫師 | (field)
y -= ROW_H
draw_cell(MARGIN_L, y, label_w3, ROW_H, '醫院名稱', size=11, align='center', bg=LIGHT_GREY)
draw_cell(MARGIN_L + label_w3, y, field_w3, ROW_H)
add_textfield(MARGIN_L + label_w3 + 2, y + 2, field_w3 - 4, ROW_H - 4, 'hospital', font_size=10)
draw_cell(MARGIN_L + half_w, y, label_w3, ROW_H, '放射科醫師', size=11, align='center', bg=LIGHT_GREY)
draw_cell(MARGIN_L + half_w + label_w3, y, field_w3, ROW_H)
add_textfield(MARGIN_L + half_w + label_w3 + 2, y + 2, field_w3 - 4, ROW_H - 4, 'radiologist', font_size=10)

# ══════════════════════════════════════════════
# SECTION 2: 乳房X光攝影陽性結果
# (FIX 1: Proper bordered box enclosing all categories)
# ══════════════════════════════════════════════
y -= 6
y -= header_h
draw_header_row(y, header_h, '乳房X光攝影陽性結果', size=13)

# Calculate total content height for all 5 category lines
cat_line_h = 17
num_cat_lines = 5  # Cat 0, Cat 3, Cat 4, Cat 4 sub, Cat 5
cat_content_h = cat_line_h * num_cat_lines + 4  # +4 for top/bottom padding

# Draw the content border box FIRST
cat_content_top = y - cat_content_h
draw_cell(MARGIN_L, cat_content_top, CONTENT_W, cat_content_h)

# Place category checkboxes inside the box
cy = y - cat_line_h
checkbox_with_label(MARGIN_L + 6, cy + 3, 'cat_0', 'Category 0：Need Additional Imaging Evaluation.', font_size=11)

cy -= cat_line_h
checkbox_with_label(MARGIN_L + 6, cy + 3, 'cat_3', 'Category 3：Probably Benign Finding – Short Interval Follow-up Is Suggested.', font_size=11)

cy -= cat_line_h
checkbox_with_label(MARGIN_L + 6, cy + 3, 'cat_4', 'Category 4：Suspicious Abnormality – Biopsy Should Be Considered.', font_size=11)

cy -= cat_line_h
cx = MARGIN_L + 50
cx = checkbox_with_label(cx, cy + 3, 'cat_4a', 'a. Low suspicion；', font_size=11)
cx = checkbox_with_label(cx, cy + 3, 'cat_4b', 'b. Moderate suspicion；', font_size=11)
cx = checkbox_with_label(cx, cy + 3, 'cat_4c', 'c. High suspicion；', font_size=11)

cy -= cat_line_h
checkbox_with_label(MARGIN_L + 6, cy + 3, 'cat_5', 'Category 5：Highly Suggestive of Malignancy – Appropriate Action Should Be Taken.', font_size=11)

y = cat_content_top  # update y to bottom of BI-RADS box

# ══════════════════════════════════════════════
# SECTION 3: 病灶勾選 header
# ══════════════════════════════════════════════
y -= 4
y -= header_h
draw_header_row(y, header_h, '病灶勾選(如單側多處病灶或兩側皆有病灶，請以不同表單分開呈現)', size=11)


# ══════════════════════════════════════════════
# Reusable: Location table
# (FIX 2: "One view only" row uses 2 merged half-cells)
# ══════════════════════════════════════════════
def draw_location_table(ly, prefix):
    """Draw the location sub-table. Returns y after the table."""
    loc_row_h = 16
    label_w = 65
    cell_w = (CONTENT_W - label_w) / 6

    # Row 1: Location header + 6 quadrant checkboxes
    draw_cell(MARGIN_L, ly, label_w, loc_row_h, 'Location', size=10, align='center', bg=LIGHT_GREY)
    quads = ['UOQ', 'UIQ', 'LOQ', 'LIQ', 'Subareolar', 'Axillary tail']
    for i, q in enumerate(quads):
        qx = MARGIN_L + label_w + i * cell_w
        draw_cell(qx, ly, cell_w, loc_row_h)
        add_checkbox(qx + 3, ly + 3, f'{prefix}_loc_{q.lower().replace(" ", "_").replace(".", "")}')
        c.setFont(FONT_NAME, 9)
        c.drawString(qx + CB_SIZE + 5, ly + loc_row_h / 2 - 3, q)

    # Row 2: One view only + 2 merged hemisphere cells
    ly -= loc_row_h
    draw_cell(MARGIN_L, ly, label_w, loc_row_h, 'One view only', size=8, align='center', bg=LIGHT_GREY)
    half_area_w = (CONTENT_W - label_w) / 2

    # Left half: Upper Hemisphere + Lower Hemisphere
    left_x = MARGIN_L + label_w
    draw_cell(left_x, ly, half_area_w, loc_row_h)
    add_checkbox(left_x + 4, ly + 3, f'{prefix}_hem_upper')
    c.setFont(FONT_NAME, 9)
    c.drawString(left_x + CB_SIZE + 6, ly + loc_row_h / 2 - 3, 'Upper Hemisphere')
    mid_x = left_x + half_area_w / 2
    add_checkbox(mid_x + 4, ly + 3, f'{prefix}_hem_lower')
    c.drawString(mid_x + CB_SIZE + 6, ly + loc_row_h / 2 - 3, 'Lower Hemisphere')

    # Right half: Outer Hemisphere + Inner Hemisphere
    right_x = MARGIN_L + label_w + half_area_w
    draw_cell(right_x, ly, half_area_w, loc_row_h)
    add_checkbox(right_x + 4, ly + 3, f'{prefix}_hem_outer')
    c.setFont(FONT_NAME, 9)
    c.drawString(right_x + CB_SIZE + 6, ly + loc_row_h / 2 - 3, 'Outer Hemisphere')
    mid_r = right_x + half_area_w / 2
    add_checkbox(mid_r + 4, ly + 3, f'{prefix}_hem_inner')
    c.drawString(mid_r + CB_SIZE + 6, ly + loc_row_h / 2 - 3, 'Inner Hemisphere')

    return ly


def draw_property_row(py, label, options, prefix):
    """Draw a single property row with label + option checkboxes."""
    prop_h = 16
    label_w = 65
    opt_area_w = CONTENT_W - label_w

    draw_cell(MARGIN_L, py, label_w, prop_h, label, size=10, align='center', bg=LIGHT_GREY)
    draw_cell(MARGIN_L + label_w, py, opt_area_w, prop_h)

    spacing = opt_area_w / len(options)
    for i, (opt_label, opt_key) in enumerate(options):
        ix = MARGIN_L + label_w + i * spacing + 4
        add_checkbox(ix, py + 3, f'{prefix}_{opt_key}')
        c.setFont(FONT_NAME, 9)
        c.drawString(ix + CB_SIZE + 2, py + prop_h / 2 - 3, opt_label)

    return py


# ══════════════════════════════════════════════
# 1. Mass
# ══════════════════════════════════════════════
y -= 4
finding_line_h = 16
loc_row_h = 16
prop_h = 16

y -= finding_line_h
cx = MARGIN_L + 2
cx = checkbox_with_label(cx, y + 3, 'finding_mass', '1. Mass：', font_size=11)
cx = checkbox_with_label(cx, y + 3, 'mass_rt', 'Rt.', font_size=11)
cx = checkbox_with_label(cx, y + 3, 'mass_lt', 'Lt.', font_size=11)
cx = checkbox_with_label(cx, y + 3, 'mass_multi_uni', 'Multiple, Unilateral', font_size=11)
cx = checkbox_with_label(cx, y + 3, 'mass_multi_bi', 'Multiple, Bilateral', font_size=11)

y -= loc_row_h
y = draw_location_table(y, 'mass')

y -= prop_h
draw_property_row(y, 'Size', [
    ('<1.0 cm', 'size_lt1'), ('1-2 cm', 'size_1_2'), ('2-3 cm', 'size_2_3'),
    ('3-4 cm', 'size_3_4'), ('>4 cm', 'size_gt4')
], 'mass')

y -= prop_h
draw_property_row(y, 'Shape', [
    ('Round', 'shape_round'), ('Oval', 'shape_oval'),
    ('Lobular', 'shape_lobular'), ('Irregular', 'shape_irregular')
], 'mass')

y -= prop_h
draw_property_row(y, 'Margin', [
    ('Circumscribed', 'margin_circumscribed'), ('Microlobulated', 'margin_microlobulated'),
    ('Obscured', 'margin_obscured'), ('Indistinct', 'margin_indistinct'),
    ('Spiculated', 'margin_spiculated')
], 'mass')

y -= prop_h
draw_property_row(y, 'Density', [
    ('High density', 'density_high'), ('Equal density', 'density_equal'),
    ('Low-density', 'density_low'), ('Fat-containing', 'density_fat')
], 'mass')

# ══════════════════════════════════════════════
# 2. Calcifications
# ══════════════════════════════════════════════
y -= 4
y -= finding_line_h
cx = MARGIN_L + 2
cx = checkbox_with_label(cx, y + 3, 'finding_calc', '2. Calcifications：', font_size=11)
cx = checkbox_with_label(cx, y + 3, 'calc_rt', 'Rt.', font_size=11)
cx = checkbox_with_label(cx, y + 3, 'calc_lt', 'Lt.', font_size=11)
cx = checkbox_with_label(cx, y + 3, 'calc_multi_uni', 'Multiple, Unilateral', font_size=11)
cx = checkbox_with_label(cx, y + 3, 'calc_multi_bi', 'Multiple, Bilateral', font_size=11)

y -= loc_row_h
y = draw_location_table(y, 'calc')

y -= prop_h
draw_property_row(y, 'Distribution', [
    ('Grouped', 'dist_grouped'), ('Linear', 'dist_linear'),
    ('Segmental', 'dist_segmental'), ('Regional', 'dist_regional'),
    ('Diffuse', 'dist_diffuse')
], 'calc')

y -= prop_h
draw_property_row(y, 'Morphology', [
    ('Amorphous', 'morph_amorphous'), ('Coarse Heterogeneous', 'morph_coarse'),
    ('Fine Pleomorphic', 'morph_fine_pleo'), ('Fine Linear Branching', 'morph_fine_linear')
], 'calc')

# ══════════════════════════════════════════════
# 3. Asymmetry
# ══════════════════════════════════════════════
y -= 4
y -= finding_line_h
cx = MARGIN_L + 2
cx = checkbox_with_label(cx, y + 3, 'finding_asym', '3. Asymmetry：', font_size=11)
cx = checkbox_with_label(cx, y + 3, 'asym_rt', 'Rt.', font_size=11)
cx = checkbox_with_label(cx, y + 3, 'asym_lt', 'Lt.', font_size=11)
cx = checkbox_with_label(cx, y + 3, 'asym_asymmetry', 'Asymmetry', font_size=11)
cx = checkbox_with_label(cx, y + 3, 'asym_focal', 'Focal asymmetry', font_size=11)
cx = checkbox_with_label(cx, y + 3, 'asym_developing', 'Developing asymmetry', font_size=11)

y -= loc_row_h
y = draw_location_table(y, 'asym')

# ══════════════════════════════════════════════
# 4. Architectural Distortion
# ══════════════════════════════════════════════
y -= 4
y -= finding_line_h
cx = MARGIN_L + 2
cx = checkbox_with_label(cx, y + 3, 'finding_distort', '4. Architectural Distortion：', font_size=11)
cx = checkbox_with_label(cx, y + 3, 'distort_rt', 'Rt.', font_size=11)
cx = checkbox_with_label(cx, y + 3, 'distort_lt', 'Lt.', font_size=11)

y -= loc_row_h
y = draw_location_table(y, 'distort')

# ══════════════════════════════════════════════
# 5-9. Additional findings
# ══════════════════════════════════════════════
assoc_h = 16

y -= 3
y -= assoc_h
cx = MARGIN_L + 2
cx = checkbox_with_label(cx, y + 3, 'finding5', '5. Thickening or retraction of the skin and/or nipple:', font_size=11)
cx = checkbox_with_label(cx, y + 3, 'finding5_rt', 'Rt.', font_size=11)
c.setFont(FONT_NAME, 11)
c.drawString(cx - 4, y + 6, '/')
cx = checkbox_with_label(cx + 4, y + 3, 'finding5_lt', 'Lt.', font_size=11)

y -= assoc_h
cx = MARGIN_L + 2
cx = checkbox_with_label(cx, y + 3, 'finding6', '6. Dense or enlarged axillary LNs:', font_size=11)
cx = checkbox_with_label(cx, y + 3, 'finding6_rt', 'Rt.', font_size=11)
c.setFont(FONT_NAME, 11)
c.drawString(cx - 4, y + 6, '/')
cx = checkbox_with_label(cx + 4, y + 3, 'finding6_lt', 'Lt.', font_size=11)

y -= assoc_h
cx = MARGIN_L + 2
cx = checkbox_with_label(cx, y + 3, 'finding7', '7. Dilated lactiferous ducts:', font_size=11)
cx = checkbox_with_label(cx, y + 3, 'finding7_rt', 'Rt.', font_size=11)
c.setFont(FONT_NAME, 11)
c.drawString(cx - 4, y + 6, '/')
cx = checkbox_with_label(cx + 4, y + 3, 'finding7_lt', 'Lt.', font_size=11)

y -= assoc_h
cx = MARGIN_L + 2
cx = checkbox_with_label(cx, y + 3, 'finding8', '8. Diffuse thickening of the skin and increased density:', font_size=11)
cx = checkbox_with_label(cx, y + 3, 'finding8_rt', 'Rt.', font_size=11)
c.setFont(FONT_NAME, 11)
c.drawString(cx - 4, y + 6, '/')
cx = checkbox_with_label(cx + 4, y + 3, 'finding8_lt', 'Lt.', font_size=11)

y -= assoc_h
cx = MARGIN_L + 2
cx = checkbox_with_label(cx, y + 3, 'finding9', '9. Others:', font_size=11)
add_textfield(cx, y + 1, MARGIN_L + CONTENT_W - cx - 4, 14, 'finding9_text', font_size=10)

# ══════════════════════════════════════════════
# Footer
# ══════════════════════════════════════════════
y -= 14
c.setFont(FONT_NAME, 9)
c.drawRightString(PAGE_W - MARGIN_R, y, '(113年1月修訂)')
y -= 14
c.drawRightString(PAGE_W - MARGIN_R, y, '第一聯：存病歷　　第二聯：存放射線科')

# ══════════════════════════════════════════════
# Save
# ══════════════════════════════════════════════
c.save()
print(f'Editable PDF saved to: {OUTPUT}')
print(f'Final y position: {y:.1f} (bottom margin at {MARGIN_B})')
