"""
api/ocr.py
==========
Document upload, preprocessing and OCR text extraction.
Supports Aadhaar, Income Certificate, Disability Certificate, Death Certificate.

Requires Tesseract OCR installed:
    Download: https://github.com/UB-Mannheim/tesseract/wiki
    Default path: C:\Program Files\Tesseract-OCR\tesseract.exe
"""

import os
import re
import io
import pytesseract
import cv2
import numpy as np
from PIL import Image
from pathlib import Path
from fastapi import UploadFile

from config import TESSERACT_PATH, MAX_UPLOAD_MB, ALLOWED_EXTENSIONS

# Set Tesseract path
pytesseract.pytesseract.tesseract_cmd = TESSERACT_PATH


# ─── Image Preprocessing ──────────────────────────────────────
def preprocess_image(img_array: np.ndarray) -> np.ndarray:
    """Enhance image quality for better OCR accuracy."""
    # Convert to grayscale
    if len(img_array.shape) == 3:
        gray = cv2.cvtColor(img_array, cv2.COLOR_BGR2GRAY)
    else:
        gray = img_array

    # Denoise
    denoised = cv2.fastNlMeansDenoising(gray, h=10)

    # Increase contrast
    clahe     = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
    contrasted = clahe.apply(denoised)

    # Threshold
    _, thresh = cv2.threshold(
        contrasted, 0, 255,
        cv2.THRESH_BINARY + cv2.THRESH_OTSU
    )

    return thresh


def load_image_from_upload(file_bytes: bytes, filename: str) -> np.ndarray:
    """Load uploaded file bytes into numpy array."""
    ext = Path(filename).suffix.lower()

    if ext == ".pdf":
        # Convert PDF first page to image
        try:
            import fitz  # PyMuPDF
            doc  = fitz.open(stream=file_bytes, filetype="pdf")
            page = doc[0]
            mat  = fitz.Matrix(2.0, 2.0)   # 2x zoom for better OCR
            pix  = page.get_pixmap(matrix=mat)
            img  = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)
            return cv2.cvtColor(np.array(img), cv2.COLOR_RGB2BGR)
        except ImportError:
            raise ValueError("PDF support requires PyMuPDF: pip install pymupdf")
    else:
        # Image file
        nparr = np.frombuffer(file_bytes, np.uint8)
        return cv2.imdecode(nparr, cv2.IMREAD_COLOR)


# ─── OCR Extraction ───────────────────────────────────────────
def extract_text(img_array: np.ndarray) -> str:
    """Run Tesseract OCR on preprocessed image."""
    processed = preprocess_image(img_array)
    pil_img   = Image.fromarray(processed)
    text      = pytesseract.image_to_string(
        pil_img,
        lang="eng",
        config="--psm 6 --oem 3"
    )
    return text.strip()


# ─── Field Extractors ─────────────────────────────────────────
def extract_aadhaar_fields(text: str) -> dict:
    """Extract age, gender, state from Aadhaar card text."""
    fields = {}

    # Age — look for DOB or age patterns
    dob_match = re.search(
        r'(?:DOB|Date of Birth|d\.o\.b)[:\s]+(\d{2})[\/\-](\d{2})[\/\-](\d{4})',
        text, re.IGNORECASE
    )
    if dob_match:
        from datetime import date
        birth_year = int(dob_match.group(3))
        fields["age"] = date.today().year - birth_year

    age_match = re.search(r'\b(?:Age|AGE)[:\s]+(\d{2,3})', text, re.IGNORECASE)
    if age_match and "age" not in fields:
        fields["age"] = int(age_match.group(1))

    # Gender
    if re.search(r'\b(MALE|Male)\b', text):
        fields["gender"] = "Male"
    elif re.search(r'\b(FEMALE|Female)\b', text):
        fields["gender"] = "Female"

    # State — look for known Indian state names
    from config import INDIAN_STATES
    for state in INDIAN_STATES:
        if state.lower() in text.lower():
            fields["state"] = state
            break

    # Area type — pin code based (rough heuristic)
    pin_match = re.search(r'\b(\d{6})\b', text)
    if pin_match:
        pin = pin_match.group(1)
        # Metro pin ranges (rough)
        metro_pins = ["110", "400", "700", "600", "500", "560", "380"]
        fields["area_type"] = "Urban" if any(
            pin.startswith(p) for p in metro_pins
        ) else "Rural"

    fields["aadhaar_linked"] = "Yes"
    return fields


def extract_income_fields(text: str) -> dict:
    """Extract annual income and BPL status from income certificate."""
    fields = {}

    # Annual income — various patterns
    income_patterns = [
        r'(?:Annual Income|annual income|ANNUAL INCOME)[:\s]+(?:Rs\.?|INR|₹)?\s*([\d,]+)',
        r'(?:Rs\.?|INR|₹)\s*([\d,]+)\s*(?:per annum|p\.a\.|annually)',
        r'income[:\s]+(?:Rs\.?|INR|₹)?\s*([\d,]+)',
    ]
    for pattern in income_patterns:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            income_str    = match.group(1).replace(",", "")
            fields["annual_income"] = int(income_str)
            break

    # BPL status
    if re.search(r'\b(BPL|Below Poverty Line)\b', text, re.IGNORECASE):
        fields["bpl_card"] = "Yes"
    elif re.search(r'\b(APL|Above Poverty Line)\b', text, re.IGNORECASE):
        fields["bpl_card"] = "No"

    return fields


def extract_disability_fields(text: str) -> dict:
    """Extract disability percentage and type from disability certificate."""
    fields = {"has_disability": "Yes"}

    # Disability percentage
    pct_patterns = [
        r'(\d{1,3})\s*(?:%|percent|PERCENT)\s*(?:disability|disabled|impairment)',
        r'(?:disability|disabled|impairment)[:\s]+(\d{1,3})\s*(?:%|percent)',
        r'(\d{1,3})%',
    ]
    for pattern in pct_patterns:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            pct = int(match.group(1))
            if 0 < pct <= 100:
                fields["disability_percentage"] = pct
                break

    # Disability type
    type_map = {
        "locomotor":   "Locomotor",
        "visual":      "Visual",
        "hearing":     "Hearing",
        "mental":      "Mental Illness",
        "intellectual":"Intellectual",
        "cerebral":    "Cerebral Palsy",
        "multiple":    "Multiple Disabilities",
    }
    for keyword, dtype in type_map.items():
        if keyword in text.lower():
            fields["disability_type"] = dtype
            break

    return fields


def extract_death_cert_fields(text: str) -> dict:
    """Extract marital status from spouse death certificate."""
    return {"marital_status": "Widowed"}


# ─── Document Type Detector ───────────────────────────────────
def detect_document_type(text: str) -> str:
    """Identify document type from OCR text."""
    text_lower = text.lower()

    if any(kw in text_lower for kw in ["aadhaar", "aadhar", "uidai", "unique identification"]):
        return "aadhaar"
    elif any(kw in text_lower for kw in ["income certificate", "annual income", "income proof"]):
        return "income"
    elif any(kw in text_lower for kw in ["disability certificate", "person with disability",
                                          "handicap", "divyangjan"]):
        return "disability"
    elif any(kw in text_lower for kw in ["death certificate", "cause of death", "deceased"]):
        return "death_certificate"
    else:
        return "unknown"


# ─── Main Processor ───────────────────────────────────────────
async def process_document(file: UploadFile) -> dict:
    """
    Full pipeline: validate → load → OCR → extract fields.

    Returns:
        dict with extracted fields + document_type + raw_text
    """
    # Validate file
    ext = Path(file.filename).suffix.lower()
    if ext not in ALLOWED_EXTENSIONS:
        return {
            "success": False,
            "error": f"File type {ext} not allowed. Use: {ALLOWED_EXTENSIONS}"
        }

    file_bytes = await file.read()

    if len(file_bytes) > MAX_UPLOAD_MB * 1024 * 1024:
        return {
            "success": False,
            "error": f"File too large. Maximum size: {MAX_UPLOAD_MB}MB"
        }

    try:
        # Load and OCR
        img        = load_image_from_upload(file_bytes, file.filename)
        raw_text   = extract_text(img)
        doc_type   = detect_document_type(raw_text)

        # Extract fields based on document type
        extractors = {
            "aadhaar":           extract_aadhaar_fields,
            "income":            extract_income_fields,
            "disability":        extract_disability_fields,
            "death_certificate": extract_death_cert_fields,
        }

        extracted = {}
        if doc_type in extractors:
            extracted = extractors[doc_type](raw_text)

        return {
            "success":       True,
            "document_type": doc_type,
            "extracted":     extracted,
            "raw_text":      raw_text[:500],  # first 500 chars for debugging
            "filename":      file.filename,
        }

    except Exception as e:
        return {
            "success": False,
            "error":   str(e),
            "filename": file.filename
        }
