# HTML / PHP API Notes

This document describes the current runtime contract used by:

- [ldct.html](/media/aiserver/structure_report_ldct/ldct.html)
- [ccta.html](/media/aiserver/structure_report_ldct/ccta.html)
- [report_api.php](/media/aiserver/structure_report_ldct/report_api.php)

## 1. `examname` rule

The frontend does not ask the user to enter `examname`.
It is derived from the HTML filename:

- `ldct.html` -> `examname=ldct`
- `ccta.html` -> `examname=ccta`

`report_api.php` uses `examname` to determine root folders:

- DOCX root: `__DIR__/{examname}_docx/`
- JSON root: `__DIR__/{examname}_json/`

Examples:

- `ldct` -> `ldct_docx/`, `ldct_json/`
- `ccta` -> `ccta_docx/`, `ccta_json/`

## 2. URL query parameters

### 2.1 `ldct.html`

Supported parameters:

- `acc` or `accession`: Accession Number
- `pid`: Patient ID
- `pname` or `p_name`: Patient Name
- `examdate`: Exam Date
- `d_name`: Doctor Name
- `d_id`: Doctor ID
- `t_name`: Tech Name

Example:

```text
/ldct.html?acc=HX-260301197&pid=0762026&pname=王小明&examdate=2026.03.26&d_name=陳醫師&d_id=R12345&t_name=林技師
```

Notes:

- if `acc/accession` and `pid` are present, `ldct.html` will auto-load an existing JSON case
- `pname` / `p_name` remains effective even if an existing JSON file is auto-loaded afterward

### 2.2 `ccta.html`

Supported parameters:

- `acc` or `accession`: Accession Number
- `pid` or `chartNo`: chart number
- `pname` or `p_name`: patient name
- `examdate`: exam date

Example:

```text
/ccta.html?acc=HX-260301197&pid=0762026&pname=王小明&examdate=2026.03.26
```

Notes:

- if `acc/accession` and `pid/chartNo` are present, `ccta.html` will auto-load an existing JSON case
- `pname` / `p_name` remains effective even if an existing JSON file is auto-loaded afterward

## 3. Shared load API

Both `ldct.html` and `ccta.html` load saved state through:

```http
GET /report_api.php?action=load
```

Query parameters:

- `accession_number`: required by current frontend load flow
- `patient_id`: required by current frontend load flow
- `exam_date`: optional
- `output_subdir`: optional relative subdirectory
- `examname`: required by current contract

Example:

```text
/report_api.php?action=load&accession_number=HX-260301197&patient_id=0762026&exam_date=2026.03.26&output_subdir=&examname=ccta
```

Success response:

```json
{
  "ok": true,
  "state_path": "/abs/path/to/file.json",
  "state": {
    "source": {},
    "review": {}
  }
}
```

Failure responses:

- `404`: state file not found
- `500`: state file read failed or JSON parse failed
- other non-2xx: `{"ok":false,"error":"..."}`

JSON filename rule:

- primary rule: `{accession_number}_{patient_id}.json`
- legacy fallback inside PHP: `{patient_id}_{exam_date}-{EXAMNAME}.json`

## 4. Save DOCX + JSON

Used by:

- `ldct.html`
- `ccta.html` final save button

Request:

```http
POST /report_api.php
Content-Type: application/json
```

Request body:

```json
{
  "filename": "2026.03.26_0762026_ccta.docx",
  "state_filename": "HX-260301197_0762026.json",
  "output_subdir": "",
  "examname": "ccta",
  "docx_base64": "<base64 docx bytes>",
  "state": {
    "source": {},
    "review": {}
  }
}
```

Field rules:

- `filename`: required, must end with `.docx`
- `state_filename`: required, must end with `.json`
- `output_subdir`: optional relative subdirectory
- `examname`: required by current save/load contract
- `docx_base64`: required
- `state`: required object

Success response:

```json
{
  "ok": true,
  "saved_path": "/abs/path/to/docx",
  "state_path": "/abs/path/to/json",
  "download_url": "./docx_files.php?action=download&examname=ccta&path=2026.03.26_0762026_ccta.docx"
}
```

Failure responses:

- `400`: invalid filename, invalid state filename, missing `docx_base64`, invalid base64, or missing `state`
- `500`: target directory creation failed, DOCX write failed, or JSON write failed

Storage rules:

- DOCX root: `__DIR__/{examname}_docx/`
- JSON root: `__DIR__/{examname}_json/`
- if `output_subdir` is non-empty, it is appended under both roots

Additional behavior:

- DOCX filenames are auto-versioned with `_v2`, `_v3`, etc.
- JSON files are overwritten in place when the same `state_filename` is reused

## 5. Save JSON only

Used by:

- `ccta.html` button `暫存報告`

Request:

```http
POST /report_api.php?action=save_state
Content-Type: application/json
```

Request body:

```json
{
  "state_filename": "HX-260301197_0762026.json",
  "output_subdir": "",
  "examname": "ccta",
  "state": {
    "source": {},
    "review": {}
  }
}
```

Success response:

```json
{
  "ok": true,
  "state_path": "/abs/path/to/file.json"
}
```

Failure responses:

- `400`: invalid state filename or missing `state`
- `500`: JSON directory creation failed, JSON encode failed, or JSON write failed

## 6. Translate API

Used by:

- `ldct.html`
- `ccta.html` when `translateOtherFindings()` runs in `local` mode

Request:

```http
POST /report_api.php?action=translate
Content-Type: application/json
```

Request body:

```json
{
  "text": "No cardiomegaly."
}
```

Success response:

```json
{
  "ok": true,
  "translated_text": "無心臟肥大。",
  "model": "..."
}
```

Backend note:

- PHP forwards this request to `TRANSLATE_API_URL` in [report_api.php](/media/aiserver/structure_report_ldct/report_api.php)

## 7. Local LLM proxy API

Used by:

- `ccta.html` when LLM source is `local`

Current use:

- suggestion generation
- local-LLM connectivity test

Request:

```http
POST /report_api.php?action=local_llm
Content-Type: application/json
```

Request body:

```json
{
  "prompt": "..."
}
```

Success response:

```json
{
  "ok": true,
  "content": "...",
  "model": "...",
  "endpoint": "http://..."
}
```

Backend note:

- PHP forwards this request to `LOCAL_LLM_API_URL` in [report_api.php](/media/aiserver/structure_report_ldct/report_api.php)
- the endpoint is no longer editable in `ccta.html`

## 8. State JSON structure

Saved case files use this top-level structure:

```json
{
  "source": {},
  "review": {}
}
```

This is the compatibility boundary to preserve if you replace either HTML page while keeping the current PHP backend and on-disk files.

### 8.1 `ldct.html` state

Representative `state.source` shape:

```json
{
  "accessionNumber": "HX-260301197",
  "patientId": "0762026",
  "patientName": "王小明",
  "examDate": "2026.03.26",
  "doctorName": "陳醫師",
  "doctorId": "R12345",
  "techName": "林技師",
  "outputSubdir": "",
  "imageQuality": "adequate",
  "previousCt": "none",
  "nodules": [],
  "structuredSelections": [],
  "structuredEnglish": [],
  "structuredZh": [],
  "otherFindings": []
}
```

Representative `state.review` shape:

```json
{
  "englishReport": "...",
  "rightRows": [],
  "leftRows": [],
  "otherText": "...",
  "conclusionLines": ["..."],
  "recommendationText": "..."
}
```

### 8.2 `ccta.html` state

Representative `state.source` shape:

```json
{
  "accessionNumber": "HX-260301197",
  "patientName": "王小明",
  "chartNo": "0762026",
  "examDate": "2026.03.26",
  "calcium": {
    "LM": 0,
    "LAD": 0,
    "LCX": 0,
    "RCA": 0
  },
  "heartRate": "60",
  "imageQuality": "良好",
  "motionArtifact": "無",
  "otherFindingsRaw": "No cardiomegaly.",
  "vessels": [],
  "keyImages": {
    "lad": ["", ""],
    "lcx": ["", ""],
    "rca": ["", ""]
  }
}
```

Representative `state.review` shape:

```json
{
  "reportText": "...",
  "summary": {
    "conclusionLines": [],
    "highRisk": [],
    "noteLines": [],
    "translatedOther": "",
    "normalCase": false
  },
  "suggestion": "...",
  "editedConclusionLines": [],
  "editedSuggestion": "...",
  "editedOtherFindings": "...",
  "generatedReport": {
    "conclusionLines": [],
    "otherFindings": "...",
    "suggestion": "..."
  }
}
```

## 9. Replacement compatibility checklist

If you replace `ldct.html` or `ccta.html` but want to keep the current backend and files:

- keep `examname` consistent with the intended output folder family
- keep `state.source` and `state.review`
- keep JSON filename rule based on `accessionNumber + patient id`
- use `GET ./report_api.php?action=load` for loading
- use `POST ./report_api.php` for DOCX + JSON save
- use `POST ./report_api.php?action=save_state` if you need JSON-only save
- use `POST ./report_api.php?action=translate` for backend translation
- use `POST ./report_api.php?action=local_llm` for backend-proxied local LLM calls
