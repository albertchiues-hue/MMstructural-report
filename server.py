from flask import Flask, request, jsonify, send_file
from flask_cors import CORS
import sqlite3
import json
import os
import io

app = Flask(__name__)
CORS(app)

DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'mammography_reports.db')


def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    conn = get_db()
    conn.execute('''
        CREATE TABLE IF NOT EXISTS reports (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            patient_id TEXT,
            patient_name TEXT,
            national_id TEXT,
            birth_date TEXT,
            exam_date TEXT,
            hospital TEXT,
            radiologist TEXT,
            category TEXT,
            form_data TEXT,
            text_report TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    conn.commit()
    conn.close()


@app.route('/api/reports', methods=['POST'])
def save_report():
    data = request.get_json()
    conn = get_db()
    cursor = conn.execute(
        '''INSERT INTO reports
           (patient_id, patient_name, national_id, birth_date, exam_date,
            hospital, radiologist, category, form_data, text_report)
           VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)''',
        (
            data.get('patient_id', ''),
            data.get('patient_name', ''),
            data.get('national_id', ''),
            data.get('birth_date', ''),
            data.get('exam_date', ''),
            data.get('hospital', ''),
            data.get('radiologist', ''),
            data.get('category', ''),
            json.dumps(data.get('form_data', {}), ensure_ascii=False),
            data.get('text_report', '')
        )
    )
    conn.commit()
    report_id = cursor.lastrowid
    conn.close()
    return jsonify({'id': report_id, 'message': 'Report saved successfully'}), 201


@app.route('/api/reports', methods=['GET'])
def list_reports():
    search = request.args.get('search', '')
    conn = get_db()
    if search:
        rows = conn.execute(
            '''SELECT id, patient_id, patient_name, exam_date, category, created_at
               FROM reports
               WHERE patient_id LIKE ? OR patient_name LIKE ?
               ORDER BY created_at DESC''',
            (f'%{search}%', f'%{search}%')
        ).fetchall()
    else:
        rows = conn.execute(
            '''SELECT id, patient_id, patient_name, exam_date, category, created_at
               FROM reports ORDER BY created_at DESC LIMIT 100'''
        ).fetchall()
    conn.close()
    return jsonify([dict(row) for row in rows])


@app.route('/api/reports/<int:report_id>', methods=['GET'])
def get_report(report_id):
    conn = get_db()
    row = conn.execute('SELECT * FROM reports WHERE id = ?', (report_id,)).fetchone()
    conn.close()
    if row is None:
        return jsonify({'error': 'Report not found'}), 404
    result = dict(row)
    result['form_data'] = json.loads(result['form_data']) if result['form_data'] else {}
    return jsonify(result)


TEMPLATE_PDF = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'mammography_report_form.pdf')

QUAD_MAP = {
    'UOQ': 'uoq', 'UIQ': 'uiq', 'LOQ': 'loq', 'LIQ': 'liq',
    'Subareolar': 'subareolar', 'Axillary tail': 'axillary'
}
HEMI_MAP = {
    'Upper Hemisphere': 'upper', 'Lower Hemisphere': 'lower',
    'Outer Hemisphere': 'outer', 'Inner Hemisphere': 'inner'
}


def build_field_map(finding, form_data):
    """Return dict of {field_name: '/Yes'} for the given finding."""
    fields = {}
    t = finding.get('type', '')
    prefix = {'mass': 'mass', 'calc': 'calc', 'asym': 'asym', 'arch': 'distort'}.get(t)
    if not prefix:
        return fields

    fields[prefix] = '/Yes'

    # Side
    side = finding.get('side', '') or ''
    side_key = {
        'Rt': f'{prefix}_rt', 'Lt': f'{prefix}_lt',
        'Multiple, Unilateral': f'{prefix}_multi_uni',
        'Multiple, Bilateral': f'{prefix}_multi_bi'
    }.get(side)
    if side_key:
        fields[side_key] = '/Yes'

    # Quadrant (multi-select)
    quads = finding.get('quadrant') or []
    if isinstance(quads, str):
        quads = [quads]
    for q in quads:
        k = QUAD_MAP.get(q)
        if k:
            fields[f'{prefix}_{k}'] = '/Yes'

    # Hemisphere
    hemi = HEMI_MAP.get(finding.get('hemisphere', '') or '')
    if hemi:
        fields[f'{prefix}_{hemi}'] = '/Yes'

    # Type-specific fields
    if t == 'mass':
        try:
            sz = float(finding.get('size') or 0)
            if sz > 0:
                key = 'mass_lt1' if sz < 1.0 else 'mass_1_2' if sz <= 2.0 else \
                      'mass_2_3' if sz <= 3.0 else 'mass_3_4' if sz <= 4.0 else 'mass_gt4'
                fields[key] = '/Yes'
        except (ValueError, TypeError):
            pass

        shape = (finding.get('shape') or '').lower()
        for s in ('round', 'oval', 'lobular', 'irregular'):
            if shape == s:
                fields[f'mass_{s}'] = '/Yes'

        margin_map = {
            'circumscribed': 'mass_circumscribed', 'microlobulated': 'mass_microlobulated',
            'obscured': 'mass_obscured', 'indistinct': 'mass_indistinct',
            'spiculated': 'mass_spiculated'
        }
        m = (finding.get('margin') or '').lower()
        if m in margin_map:
            fields[margin_map[m]] = '/Yes'

        density_map = {
            'high density': 'mass_high_density', 'equal density': 'mass_equal_density',
            'low density': 'mass_low_density', 'fat-containing': 'mass_fat_containing'
        }
        d = (finding.get('density') or '').lower()
        if d in density_map:
            fields[density_map[d]] = '/Yes'

    elif t == 'calc':
        dist_map = {
            'grouped': 'calc_grouped', 'linear': 'calc_linear',
            'segmental': 'calc_segmental', 'regional': 'calc_regional',
            'diffuse': 'calc_diffuse'
        }
        d = (finding.get('distribution') or '').lower()
        if d in dist_map:
            fields[dist_map[d]] = '/Yes'

        morph = (finding.get('morphology') or '').lower()
        # punctate maps to amorphous on the PDF form
        if morph == 'punctate':
            morph = 'amorphous'
        morph_map = {
            'amorphous': 'calc_amorphous', 'coarse heterogeneous': 'calc_coarse',
            'fine pleomorphic': 'calc_fine_pleo', 'fine linear branching': 'calc_fine_linear'
        }
        if morph in morph_map:
            fields[morph_map[morph]] = '/Yes'

    elif t == 'asym':
        atype_map = {
            'asymmetry': 'asym_asymmetry', 'focal asymmetry': 'asym_focal',
            'developing asymmetry': 'asym_developing'
        }
        at = (finding.get('asymType') or '').lower()
        if at in atype_map:
            fields[atype_map[at]] = '/Yes'

    return fields


def build_assoc_fields(form_data):
    fields = {}
    for item in range(5, 10):
        if form_data.get(f'item{item}-enabled'):
            fields[f'item{item}'] = '/Yes'
            side = form_data.get(f'item{item}-side', '') or ''
            if side == 'Rt':
                fields[f'item{item}_rt'] = '/Yes'
            elif side == 'Lt':
                fields[f'item{item}_lt'] = '/Yes'
    return fields


def fmt_date(iso_str):
    """Convert 'YYYY-MM-DD' to 'YYYY年MM月DD日'. Returns '' if invalid."""
    if not iso_str:
        return ''
    try:
        y, m, d = iso_str.split('-')
        return f'{y}年{m}月{d}日'
    except Exception:
        return iso_str


def fill_template_pdf(finding, form_data, national_id='', foreign_id='',
                      others_text='', patient_name='', patient_id='',
                      birth_date='', exam_date='', radiologist=''):
    """Fill the template PDF for one finding. Returns bytes."""
    from pypdf import PdfReader, PdfWriter

    reader = PdfReader(TEMPLATE_PDF)
    writer = PdfWriter()
    writer.clone_reader_document_root(reader)

    field_values = {}
    field_values['cat_0'] = '/Yes'  # always BI-RADS 0

    field_values.update(build_field_map(finding, form_data))
    field_values.update(build_assoc_fields(form_data))

    # Digit text fields
    for i, ch in enumerate(national_id[:10]):
        field_values[f'id_{i}'] = ch
    for i, ch in enumerate(foreign_id[:10]):
        field_values[f'fid_{i}'] = ch
    if others_text:
        field_values['others_text'] = others_text
    if patient_name:
        field_values['patient_name'] = patient_name
    if patient_id:
        field_values['patient_id_field'] = patient_id
    if birth_date:
        field_values['birth_date'] = fmt_date(birth_date)
    if exam_date:
        field_values['exam_date'] = fmt_date(exam_date)
    if radiologist:
        field_values['radiologist'] = radiologist

    writer.update_page_form_field_values(
        writer.pages[0], field_values, auto_regenerate=False
    )

    buf = io.BytesIO()
    writer.write(buf)
    buf.seek(0)
    return buf.read()


@app.route('/api/fill-pdf', methods=['POST'])
def fill_pdf():
    data = request.get_json()
    findings = data.get('findings', [])
    form_data = data.get('form_data', {})
    national_id = data.get('national_id', '')
    foreign_id = data.get('foreign_id', '')
    others_text = form_data.get('item9-text', '') if form_data.get('item9-enabled') else ''
    patient_name = data.get('patient_name', '')
    patient_id = data.get('patient_id', 'report')
    birth_date = data.get('birth_date', '')
    exam_date = data.get('exam_date', '')

    radiologist = data.get('radiologist', '')
    kwargs = dict(national_id=national_id, foreign_id=foreign_id,
                  others_text=others_text, patient_name=patient_name,
                  patient_id=patient_id, birth_date=birth_date,
                  exam_date=exam_date, radiologist=radiologist)

    if not findings:
        pages_bytes = [fill_template_pdf({}, form_data, **kwargs)]
    else:
        pages_bytes = [fill_template_pdf(f, form_data, **kwargs) for f in findings]

    if len(pages_bytes) == 1:
        final_bytes = pages_bytes[0]
    else:
        # Merge multiple pages into one PDF
        from pypdf import PdfReader, PdfWriter
        merged = PdfWriter()
        for pb in pages_bytes:
            r = PdfReader(io.BytesIO(pb))
            merged.add_page(r.pages[0])
        buf = io.BytesIO()
        merged.write(buf)
        buf.seek(0)
        final_bytes = buf.read()

    fname = f'MMReport_{patient_id}_{exam_date or "form"}.pdf'
    return send_file(
        io.BytesIO(final_bytes),
        mimetype='application/pdf',
        as_attachment=True,
        download_name=fname
    )


if __name__ == '__main__':
    init_db()
    print(f'Database: {DB_PATH}')
    print('Server running at http://localhost:5001')
    app.run(debug=True, port=5001)
