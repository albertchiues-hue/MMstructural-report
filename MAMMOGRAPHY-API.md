# Mammography Report — Save / Export / Load API

This document describes the data flow for saving, exporting, and loading mammography screening reports in `mammography-report.html`.

---

## 1. Architecture Overview

```
mammography-report.html
        |
        |── (1) Copy text report to clipboard
        |
        |── (2) POST /api/reports ──────────► Flask server.py (localhost:5001)
        |       (SQLite insert)                  └─ mammography_reports.db
        |
        |── (3) POST /api/fill-pdf ─────────► Flask server.py (localhost:5001)
        |       (template PDF filling)           └─ mammography_report_form.pdf
        |       ◄── PDF blob response
        |       └─ browser download (local .pdf)
        |
        |── (4) POST /report_api.php ───────► Office server (report_api.php)
        |       (PDF base64 + state JSON)        ├─ mammography_pdf/{subdir}/{file}.pdf
        |                                        └─ mammography_json/{subdir}/{file}.json
        |
        └── (on page load) GET /report_api.php?action=load
                ◄── state JSON ──────────► restoreState() fills the form
```

All four steps are triggered sequentially by the **"Copy, Save & Close"** button (`copyAndFinish()`).

---

## 2. Configuration Constants

```javascript
const REPORT_API_URL = './report_api.php';       // office server (relative when deployed)
const FLASK_API_URL  = 'http://localhost:5001';   // local Flask for PDF generation + SQLite
const EXAM_NAME      = 'mammography';
```

- `REPORT_API_URL`: relative path — works when `mammography-report.html` is deployed alongside `report_api.php` on the office server.
- `FLASK_API_URL`: absolute URL — the local Python Flask server must be running for PDF generation and SQLite saves.
- `EXAM_NAME`: determines storage folder names on the office server (`mammography_pdf/`, `mammography_json/`).

---

## 3. Save Flow (copyAndFinish)

### Step 1 — Copy to Clipboard

The generated English text report is copied via `navigator.clipboard.writeText()` with `document.execCommand('copy')` fallback.

### Step 2 — Save to Local SQLite

```
POST http://localhost:5001/api/reports
Content-Type: application/json
```

Request body:

```json
{
  "patient_id": "0762026",
  "patient_name": "王小明",
  "national_id": "A123456789",
  "birth_date": "1980-01-15",
  "exam_date": "2026-03-29",
  "hospital": "羅東博愛醫院",
  "radiologist": "邱則誠醫師",
  "category": "0",
  "form_data": { ... },
  "text_report": "Right breast:\nA 1.5 cm irregular, ..."
}

```

The `form_data` object contains all finding instances, associated findings, dates, and category. See Section 6 for its shape.

Response:

```json
{ "id": 42, "message": "Report saved successfully" }
```

**Failure handling**: silent — if Flask server is not running, the error is caught and ignored.

### Step 3 — Generate & Download PDF

```
POST http://localhost:5001/api/fill-pdf
Content-Type: application/json
```

Request body:

```json
{
  "findings": [ { "type": "mass", "side": "Rt", "size": "1.5", ... } ],
  "form_data": { "item5-enabled": true, "item5-side": "Rt", ... },
  "national_id": "A123456789",
  "foreign_id": "",
  "patient_name": "王小明",
  "patient_id": "0762026",
  "birth_date": "1980-01-15",
  "exam_date": "2026-03-29",
  "radiologist": "邱則誠醫師"
}
```

The Flask server fills the template PDF (`mammography_report_form.pdf`) using pypdf:
- Checkboxes set to `/Yes` for selected findings/locations/properties
- Text fields filled: patient name, patient ID, birth date, exam date, radiologist, national ID digits, others text
- One page per finding; multiple findings produce a merged multi-page PDF
- Dates formatted as `YYYY年MM月DD日`

Response: `application/pdf` blob.

The blob is:
1. Downloaded locally as `MMReport_{patientId}_{examDate}.pdf`
2. Returned to `copyAndFinish()` for the next step

### Step 4 — Upload to Office Server (report_api.php)

```
POST ./report_api.php
Content-Type: application/json
```

Request body:

```json
{
  "filename":       "2026-03-29_0762026_mammography.pdf",
  "state_filename": "HX-260301197_0762026.json",
  "output_subdir":  "",
  "examname":       "mammography",
  "pdf_base64":     "<base64 encoded PDF bytes>",
  "state": {
    "source": { ... },
    "review": { ... }
  }
}
```

Server-side storage:
- PDF saved to: `mammography_pdf/{output_subdir}/{filename}`
- JSON saved to: `mammography_json/{output_subdir}/{state_filename}`
- PDF filenames are auto-versioned (`_v2`, `_v3`, ...) if duplicates exist
- JSON files are overwritten in place when the same `state_filename` is reused

Response:

```json
{
  "ok": true,
  "saved_path": "/abs/path/to/pdf",
  "state_path": "/abs/path/to/json",
  "download_url": "./docx_files.php?action=download&examname=mammography&path=..."
}
```

**Failure handling**: warns to console but does not block the user.

---

## 4. Save State Only (JSON without PDF)

For interim saves without generating a PDF. Currently wired but not yet exposed as a UI button.

```
POST ./report_api.php?action=save_state
Content-Type: application/json
```

```json
{
  "state_filename": "HX-260301197_0762026.json",
  "output_subdir":  "",
  "examname":       "mammography",
  "state": {
    "source": { ... },
    "review": { ... }
  }
}
```

Response:

```json
{ "ok": true, "state_path": "/abs/path/to/file.json" }
```

---

## 5. Load Flow (auto-load on page open)

### URL Parameters

The page can be opened with pre-filled patient info:

```
mammography-report.html?acc=HX-260301197&pid=0762026&pname=王小明&examdate=2026.03.29&d_name=邱則誠醫師
```

| Parameter | Aliases | Description |
|-----------|---------|-------------|
| `acc` | `accession` | Accession Number |
| `pid` | — | Patient ID (病歷號) |
| `pname` | `p_name` | Patient Name (姓名) |
| `examdate` | — | Exam Date (`YYYY.MM.DD` or `YYYY-MM-DD`) |
| `d_name` | — | Radiologist name |
| `d_id` | — | Doctor ID |
| `t_name` | — | Technologist name |

### Auto-Load Behavior

When both `acc` and `pid` are present in URL params:

```
GET ./report_api.php?action=load&accession_number=HX-260301197&patient_id=0762026&examname=mammography
```

If a saved state JSON is found (HTTP 200):
1. `restoreState()` populates all form fields from the loaded JSON
2. Finding cards are re-created with their toggle button selections
3. Associated findings checkboxes and sub-options are restored
4. The text report is restored from `state.review.textReport`
5. URL `pname` overrides the loaded `patientName` (per API-2.md spec)

If not found (HTTP 404): the form stays with only URL-param values pre-filled.

### JSON Filename Rules

Primary (when accession number is available):
```
{accessionNumber}_{patientId}.json
→ HX-260301197_0762026.json
```

Legacy fallback (no accession number):
```
{patientId}_{examDate}-MAMMOGRAPHY.json
→ 0762026_2026-03-29-MAMMOGRAPHY.json
```

---

## 6. State JSON Structure

The state JSON follows the `{source, review}` contract shared with LDCT and CCTA reports.

### `state.source`

```json
{
  "accessionNumber": "HX-260301197",
  "patientId": "0762026",
  "patientName": "王小明",
  "nationalId": "A123456789",
  "foreignId": "",
  "birthDate": "1980-01-15",
  "examDate": "2026-03-29",
  "hospital": "羅東博愛醫院",
  "radiologist": "邱則誠醫師",
  "category": "0",
  "findings": [
    {
      "type": "mass",
      "instanceId": "mass-1",
      "side": "Rt",
      "quadrant": ["UOQ"],
      "hemisphere": null,
      "depth": "Middle third",
      "distance": "5",
      "size": "1.5",
      "shape": "irregular",
      "margin": "spiculated",
      "density": "high density"
    }
  ],
  "formData": {
    "findings": [ ... ],
    "item5-enabled": true,
    "item5-side": "Rt",
    "item5-detail": ["Skin retraction"],
    "item6-enabled": false,
    "item6-side": null,
    "item7-enabled": false,
    "item7-side": null,
    "item8-enabled": false,
    "item8-side": null,
    "item9-enabled": false,
    "item9-text": "",
    "birth_date": "1980-01-15",
    "exam_date": "2026-03-29",
    "category": "0"
  }
}
```

### `state.review`

```json
{
  "textReport": "Right breast:\nA 1.5 cm irregular, spiculated, high density mass in the upper outer quadrant, at the Middle third, approximately 5 cm from the nipple.\n\nAssociated findings: right Skin retraction.\n\nNo enlarged lymph nodes are found in the bilateral axilla.\n\nASSESSMENT: BI-RADS 0 - Incomplete.\nRECOMMENDATION: Spot compression view and ultrasound of the right breast are recommended."
}
```

---

## 7. PDF Template Field Mapping

The Flask server maps form data to PDF AcroForm fields in `mammography_report_form.pdf`.

### Checkbox Fields

| Finding Type | Field Pattern | Example |
|-------------|---------------|---------|
| Mass | `mass`, `mass_rt`, `mass_lt`, `mass_multi_uni`, `mass_multi_bi` | Side |
| Mass | `mass_uoq`, `mass_uiq`, `mass_loq`, `mass_liq`, `mass_subareolar`, `mass_axillary` | Quadrant |
| Mass | `mass_upper`, `mass_lower`, `mass_outer`, `mass_inner` | Hemisphere |
| Mass | `mass_lt1`, `mass_1_2`, `mass_2_3`, `mass_3_4`, `mass_gt4` | Size range |
| Mass | `mass_round`, `mass_oval`, `mass_lobular`, `mass_irregular` | Shape |
| Mass | `mass_circumscribed`, `mass_microlobulated`, `mass_obscured`, `mass_indistinct`, `mass_spiculated` | Margin |
| Mass | `mass_high_density`, `mass_equal_density`, `mass_low_density`, `mass_fat_containing` | Density |
| Calcifications | `calc`, `calc_rt`, `calc_lt`, ... | Same side/location pattern |
| Calcifications | `calc_grouped`, `calc_linear`, `calc_segmental`, `calc_regional`, `calc_diffuse` | Distribution |
| Calcifications | `calc_amorphous`, `calc_coarse`, `calc_fine_pleo`, `calc_fine_linear` | Morphology |
| Asymmetry | `asym`, `asym_rt`, `asym_lt`, ... | Same side/location pattern |
| Asymmetry | `asym_asymmetry`, `asym_focal`, `asym_developing` | Asymmetry type |
| Arch. Distortion | `distort`, `distort_rt`, `distort_lt`, ... | Same side/location pattern |
| Associated | `item5` through `item9`, plus `item{N}_rt`, `item{N}_lt` | Associated findings |
| BI-RADS | `cat_0` | Always checked (screening = BI-RADS 0) |

### Text Fields

| Field Name | Content |
|-----------|---------|
| `patient_name` | Patient name (CJK) |
| `patient_id_field` | 病歷號 |
| `birth_date` | Formatted as `YYYY年MM月DD日` |
| `exam_date` | Formatted as `YYYY年MM月DD日` |
| `radiologist` | Radiologist name |
| `id_0` – `id_9` | National ID digits |
| `fid_0` – `fid_9` | Foreign ID digits |
| `others_text` | Item 9 free text |

### Special Mappings

| UI Selection | PDF Field | Text Report |
|-------------|-----------|-------------|
| Morphology: Punctate | `calc_amorphous` (maps to Amorphous) | "punctate" |
| Size: 1.5 (exact cm) | `mass_1_2` (auto-categorized to 1-2cm range) | "1.5 cm" |
| Shape: Lobular | exists on PDF but NOT selectable from UI | — |

---

## 8. Error Handling Summary

| Step | On Failure |
|------|-----------|
| Clipboard copy | Falls back to `document.execCommand('copy')` |
| SQLite save (Flask) | Silent catch — server may not be running locally |
| PDF generation (Flask) | Shows error status: "PDF generation failed. Is the server running?" |
| report_api.php save | Console warning — office server may not be reachable |
| report_api.php load | Returns `null`, form stays with URL-param values only |

---

## 9. File Inventory

| File | Role |
|------|------|
| `mammography-report.html` | Frontend: form UI, report generation, save/load orchestration |
| `server.py` | Flask backend: SQLite storage + PDF template filling |
| `report_api.php` | Office server: persistent PDF/JSON storage, load/save API |
| `mammography_report_form.pdf` | Editable PDF template with AcroForm fields |
| `add_interactive_fields.py` | Script that builds the template PDF (overlay AcroForm onto base) |
| `create_mammo_form.py` | Script that generates the base Word/PDF form layout |
| `mammography_reports.db` | SQLite database (auto-created by Flask) |
| `API-2.md` | Contract documentation for report_api.php (shared with LDCT/CCTA) |
