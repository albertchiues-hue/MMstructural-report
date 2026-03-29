#!/usr/bin/env python3
"""
Overlay interactive AcroForm fields onto the Word-exported PDF.
- Checkboxes placed exactly on top of every ☐ character
- Text fields for 身份證統一編號 (10 cells) and 統一證號(外籍) (10 cells)
"""

import io
from reportlab.pdfgen.canvas import Canvas
from reportlab.lib.pagesizes import A4
from reportlab.lib.colors import black, white, HexColor

PAGE_W, PAGE_H = A4  # 595.27 x 841.89

BASE_PDF = '/Users/chiutsecheng/MMstructural report/mammography_report_form.pdf'
OUTPUT   = '/Users/chiutsecheng/MMstructural report/mammography_report_form.pdf'

# ── All ☐ character positions extracted from the Word PDF via pdfminer ──
# Format: (name, x0, y0, size)
CHECKBOXES = [
    # BI-RADS Categories
    ('cat_0',          33.6, 621.0, 11.0),
    ('cat_3',          33.6, 604.9, 11.0),
    ('cat_4',          33.6, 589.1, 11.0),
    ('cat_4a',         56.5, 573.0, 11.0),
    ('cat_4b',        150.6, 573.0, 11.0),
    ('cat_4c',        266.1, 573.0, 11.0),
    ('cat_5',          33.6, 556.9, 11.0),
    # 1. Mass
    ('mass',           33.6, 521.6, 11.0),
    ('mass_rt',        89.4, 521.6, 11.0),
    ('mass_lt',       119.8, 521.6, 11.0),
    ('mass_multi_uni',149.6, 521.6, 11.0),
    ('mass_multi_bi', 249.9, 521.6, 11.0),
    # Mass Location
    ('mass_uoq',      110.4, 504.1, 10.1),
    ('mass_uiq',      147.1, 504.1, 10.1),
    ('mass_loq',      180.2, 504.1, 10.1),
    ('mass_liq',      215.9, 504.1, 10.1),
    ('mass_subareolar',248.0, 504.1, 10.1),
    ('mass_axillary', 305.1, 504.1, 10.1),
    # Mass Hemispheres (One view only)
    ('mass_upper',    291.9, 485.4, 10.1),
    ('mass_lower',    380.3, 485.4, 10.1),
    ('mass_outer',    288.5, 465.9, 10.1),
    ('mass_inner',    379.0, 465.9, 10.1),
    # Mass Size
    ('mass_lt1',      110.4, 447.2, 10.1),
    ('mass_1_2',      161.3, 447.2, 10.1),
    ('mass_2_3',      207.7, 447.2, 10.1),
    ('mass_3_4',      254.1, 447.2, 10.1),
    ('mass_gt4',      300.5, 447.2, 10.1),
    # Mass Shape
    ('mass_round',    110.4, 429.9, 10.1),
    ('mass_oval',     154.5, 429.9, 10.1),
    ('mass_lobular',  191.7, 429.9, 10.1),
    ('mass_irregular',241.2, 429.9, 10.1),
    # Mass Margin
    ('mass_circumscribed',  110.4, 412.4, 10.1),
    ('mass_microlobulated', 182.6, 412.4, 10.1),
    ('mass_obscured',       257.5, 412.4, 10.1),
    ('mass_indistinct',     310.4, 412.4, 10.1),
    ('mass_spiculated',     362.8, 412.4, 10.1),
    # Mass Density
    ('mass_high_density',  110.4, 394.9, 10.1),
    ('mass_equal_density', 178.7, 394.9, 10.1),
    ('mass_low_density',   250.1, 394.9, 10.1),
    ('mass_fat_containing',317.4, 394.9, 10.1),
    # 2. Calcifications
    ('calc',          33.6, 377.1, 11.0),
    ('calc_rt',      124.9, 377.1, 11.0),
    ('calc_lt',      155.3, 377.1, 11.0),
    ('calc_multi_uni',185.2, 377.1, 11.0),
    ('calc_multi_bi', 285.5, 377.1, 11.0),
    # Calc Location
    ('calc_uoq',      110.4, 359.9, 10.1),
    ('calc_uiq',      147.1, 359.9, 10.1),
    ('calc_loq',      180.2, 359.9, 10.1),
    ('calc_liq',      215.9, 359.9, 10.1),
    ('calc_subareolar',248.0, 359.9, 10.1),
    ('calc_axillary', 305.1, 359.9, 10.1),
    # Calc Hemispheres (One view only)
    ('calc_upper',    291.9, 341.4, 10.1),
    ('calc_lower',    380.3, 341.4, 10.1),
    ('calc_outer',    288.5, 321.7, 10.1),
    ('calc_inner',    379.0, 321.7, 10.1),
    # Calc Distribution
    ('calc_grouped',  110.4, 303.2, 10.1),
    ('calc_linear',   163.1, 303.2, 10.1),
    ('calc_segmental',207.4, 303.2, 10.1),
    ('calc_regional', 266.8, 303.2, 10.1),
    ('calc_diffuse',  320.5, 303.2, 10.1),
    # Calc Morphology
    ('calc_amorphous',      110.4, 285.7, 10.1),
    ('calc_coarse',         174.5, 285.7, 10.1),
    ('calc_fine_pleo',      279.4, 285.7, 10.1),
    ('calc_fine_linear',    366.5, 285.7, 10.1),
    # 3. Asymmetry
    ('asym',          33.6, 267.9, 11.0),
    ('asym_rt',      116.3, 267.9, 11.0),
    ('asym_lt',      146.7, 267.9, 11.0),
    ('asym_asymmetry',176.6, 267.9, 11.0),
    ('asym_focal',   243.4, 267.9, 11.0),
    ('asym_developing',333.2, 267.9, 11.0),
    # Asym Location
    ('asym_uoq',     110.4, 250.7, 10.1),
    ('asym_uiq',     147.1, 250.7, 10.1),
    ('asym_loq',     180.2, 250.7, 10.1),
    ('asym_liq',     215.9, 250.7, 10.1),
    ('asym_subareolar',248.0, 250.7, 10.1),
    ('asym_axillary',305.1, 250.7, 10.1),
    # Asym Hemispheres (One view only)
    ('asym_upper',   291.9, 232.2, 10.1),
    ('asym_lower',   380.3, 232.2, 10.1),
    ('asym_outer',   288.5, 212.5, 10.1),
    ('asym_inner',   379.0, 212.5, 10.1),
    # 4. Architectural Distortion
    ('distort',       33.6, 192.6, 11.0),
    ('distort_rt',   166.8, 192.6, 11.0),
    ('distort_lt',   197.2, 192.6, 11.0),
    # Distort Location
    ('distort_uoq',  110.4, 174.3, 10.1),
    ('distort_uiq',  147.1, 174.3, 10.1),
    ('distort_loq',  180.2, 174.3, 10.1),
    ('distort_liq',  215.9, 174.3, 10.1),
    ('distort_subareolar',248.0, 174.3, 10.1),
    ('distort_axillary', 305.1, 174.3, 10.1),
    # Distort Hemispheres (One view only)
    ('distort_upper',291.9, 155.9, 10.1),
    ('distort_lower',380.3, 155.9, 10.1),
    ('distort_outer',288.5, 136.2, 10.1),
    ('distort_inner',379.0, 136.2, 10.1),
    # Items 5-9
    ('item5',         28.3, 115.3, 11.0),
    ('item5_rt',     265.8, 115.3, 11.0),
    ('item5_lt',     299.1, 115.3, 11.0),
    ('item6',         28.3,  97.5, 11.0),
    ('item6_rt',     190.6,  97.5, 11.0),
    ('item6_lt',     223.9,  97.5, 11.0),
    ('item7',         28.3,  79.5, 11.0),
    ('item7_rt',     161.4,  79.5, 11.0),
    ('item7_lt',     194.7,  79.5, 11.0),
    ('item8',         28.3,  61.5, 11.0),
    ('item8_rt',     276.7,  61.5, 11.0),
    ('item8_lt',     310.0,  61.5, 11.0),
    ('item9',         28.3,  43.5, 11.0),
]

# ── Digit cell x positions (from fitz border analysis) ──
DIGIT_XS = [241.2, 273.8, 306.5, 339.1, 371.5, 404.2, 436.8, 469.4, 502.1, 534.7]
DIGIT_W = 30.0

# Row 1 (身份證統一編號): fitz y=100.80 (bottom) → pdfminer y=841.9-100.80=741.1
# Row top: fitz y=78.0 → pdfminer y=841.9-78.0=763.9 → row height=22.8
ID_ROW_Y    = 741.1   # pdfminer bottom y of row 1
ID_ROW_H    = 22.8

# Row 2 (統一證號外籍): fitz y=119.76 (bottom) → pdfminer y=722.1
# Row top: pdfminer y=741.1 → row height=19.0
FID_ROW_Y   = 722.1   # pdfminer bottom y of row 2
FID_ROW_H   = 19.0

# Others text field: after "9. Others:" at x=28.3, y0=43.5
OTHERS_X = 108.0
OTHERS_Y = 43.5
OTHERS_W = 458.0
OTHERS_H = 14.0

# 姓名 value cell: fitz x=69.8-146.9, y=78.0-100.8 → pdfminer x=70-147, y=741.1-763.9
NAME_X = 70.0
NAME_Y = 741.1
NAME_W = 76.0
NAME_H = 22.8

# 病歷號 value: to the right of "病歷號：" label (ends at x=521.8) in title row, pm y=785.8-797.8
PID_X = 522.0
PID_Y = 785.8
PID_W = 44.0
PID_H = 12.0

# Date row: fitz y=119.7-152.1 → pm y=689.8-722.2
# 出生日期 value cell: pm x=70-276.5, y=689.8-722.2
# 攝影日期 value cell: pm x=360-566.9, y=689.8-722.2
BIRTH_DATE_X = 71.0
BIRTH_DATE_Y = 691.0
BIRTH_DATE_W = 204.0
BIRTH_DATE_H = 30.0

EXAM_DATE_X = 361.0
EXAM_DATE_Y = 691.0
EXAM_DATE_W = 204.0
EXAM_DATE_H = 30.0

# 放射科醫師 value cell: fitz y=152.6-184.5 → pm y=657.4-689.3; x=360-567
RADIOLOGIST_X = 361.0
RADIOLOGIST_Y = 659.0
RADIOLOGIST_W = 204.0
RADIOLOGIST_H = 28.0


def build_overlay():
    """Build overlay PDF in memory with all AcroForm fields."""
    buf = io.BytesIO()
    c = Canvas(buf, pagesize=A4)
    form = c.acroForm

    # ── Checkboxes ──
    for name, x, y, size in CHECKBOXES:
        form.checkbox(
            name=name,
            x=x, y=y,
            size=size,
            buttonStyle='check',
            borderColor=black,
            fillColor=white,
            borderWidth=0.3,
            forceBorder=True,
        )

    # ── 身份證統一編號 digit fields ──
    for i, x in enumerate(DIGIT_XS):
        form.textfield(
            name=f'id_{i}',
            x=x + 1,
            y=ID_ROW_Y + 1,
            width=DIGIT_W,
            height=ID_ROW_H - 2,
            maxlen=1,
            fontSize=11,
            borderWidth=0,
            borderColor=None,
            fillColor=None,
            forceBorder=False,
            textColor=black,
        )

    # ── 統一證號(外籍) digit fields ──
    for i, x in enumerate(DIGIT_XS):
        form.textfield(
            name=f'fid_{i}',
            x=x + 1,
            y=FID_ROW_Y + 1,
            width=DIGIT_W,
            height=FID_ROW_H - 2,
            maxlen=1,
            fontSize=11,
            borderWidth=0,
            borderColor=None,
            fillColor=None,
            forceBorder=False,
            textColor=black,
        )

    # ── 9. Others text field ──
    form.textfield(
        name='others_text',
        x=OTHERS_X,
        y=OTHERS_Y,
        width=OTHERS_W,
        height=OTHERS_H,
        fontSize=10,
        borderWidth=0,
        borderColor=None,
        fillColor=None,
        forceBorder=False,
    )

    # ── 姓名 text field ──
    form.textfield(
        name='patient_name',
        x=NAME_X,
        y=NAME_Y + 1,
        width=NAME_W,
        height=NAME_H - 2,
        fontSize=10,
        borderWidth=0,
        borderColor=None,
        fillColor=None,
        forceBorder=False,
        textColor=black,
    )

    # ── 病歷號 text field ──
    form.textfield(
        name='patient_id_field',
        x=PID_X,
        y=PID_Y + 1,
        width=PID_W,
        height=PID_H - 2,
        fontSize=9,
        borderWidth=0,
        borderColor=None,
        fillColor=None,
        forceBorder=False,
        textColor=black,
    )

    # ── 出生日期 text field ──
    form.textfield(
        name='birth_date',
        x=BIRTH_DATE_X,
        y=BIRTH_DATE_Y,
        width=BIRTH_DATE_W,
        height=BIRTH_DATE_H,
        fontSize=10,
        borderWidth=0,
        borderColor=None,
        fillColor=white,
        forceBorder=False,
        textColor=black,
    )

    # ── 攝影日期 text field ──
    form.textfield(
        name='exam_date',
        x=EXAM_DATE_X,
        y=EXAM_DATE_Y,
        width=EXAM_DATE_W,
        height=EXAM_DATE_H,
        fontSize=10,
        borderWidth=0,
        borderColor=None,
        fillColor=white,
        forceBorder=False,
        textColor=black,
    )

    # ── 放射科醫師 text field ──
    form.textfield(
        name='radiologist',
        x=RADIOLOGIST_X,
        y=RADIOLOGIST_Y,
        width=RADIOLOGIST_W,
        height=RADIOLOGIST_H,
        fontSize=10,
        borderWidth=0,
        borderColor=None,
        fillColor=None,
        forceBorder=False,
        textColor=black,
    )

    c.save()
    buf.seek(0)
    return buf


def merge_pdfs(base_path, overlay_buf, output_path):
    """Merge overlay AcroForm fields onto base PDF using pypdf."""
    from pypdf import PdfReader, PdfWriter

    overlay_buf.seek(0)
    reader_overlay = PdfReader(overlay_buf)
    reader_base    = PdfReader(open(base_path, 'rb'))

    # Start writer from overlay so all AcroForm objects are properly cloned
    writer = PdfWriter()
    writer.clone_reader_document_root(reader_overlay)

    # Merge base PDF page content underneath the overlay (transparent form layer)
    writer.pages[0].merge_page(reader_base.pages[0], over=False)

    with open(output_path, 'wb') as f:
        writer.write(f)

    print(f'Saved to: {output_path}')


if __name__ == '__main__':
    overlay = build_overlay()
    merge_pdfs(BASE_PDF, overlay, OUTPUT)
    print('Done.')
