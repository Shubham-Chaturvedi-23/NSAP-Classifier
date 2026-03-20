"""
Module: api/services/ocr.py
Description: Document upload, preprocessing, OCR text extraction
             and field extraction for NSAP documents.
             Supports Aadhaar, BPL Card, Disability Certificate
             and Death Certificate.

Requires Tesseract OCR installed:
    Download: https://github.com/UB-Mannheim/tesseract/wiki
    Default:  C:\\Program Files\\Tesseract-OCR\\tesseract.exe
"""

import re
import numpy as np
import pytesseract
import cv2
from PIL import Image
from pathlib import Path
from fastapi import UploadFile

from api.config import (
    TESSERACT_PATH, MAX_UPLOAD_MB,
    ALLOWED_EXTENSIONS, INDIAN_STATES,
)

# Set Tesseract executable path
pytesseract.pytesseract.tesseract_cmd = TESSERACT_PATH


# ─── Image Preprocessing ──────────────────────────────────────
def preprocess_image(img_array: np.ndarray) -> np.ndarray:
    """
    Enhance image quality for better OCR accuracy.
    Pipeline: grayscale → denoise → contrast → threshold.

    Args:
        img_array (np.ndarray): Raw image as numpy array.

    Returns:
        np.ndarray: Preprocessed binary image.
    """
    # Convert to grayscale if needed
    if len(img_array.shape) == 3:
        gray = cv2.cvtColor(img_array, cv2.COLOR_BGR2GRAY)
    else:
        gray = img_array

    # Denoise
    denoised = cv2.fastNlMeansDenoising(gray, h=10)

    # Enhance contrast using CLAHE
    clahe      = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
    contrasted = clahe.apply(denoised)

    # Otsu thresholding — automatically finds optimal threshold
    _, thresh = cv2.threshold(
        contrasted, 0, 255,
        cv2.THRESH_BINARY + cv2.THRESH_OTSU
    )
    return thresh


def load_image_from_bytes(file_bytes: bytes, filename: str) -> np.ndarray:
    """
    Load uploaded file bytes into a numpy array.
    Handles both image files and PDFs (first page only).

    Args:
        file_bytes (bytes): Raw file content.
        filename   (str):   Original filename for extension detection.

    Returns:
        np.ndarray: Image as BGR numpy array.

    Raises:
        ValueError: If PDF support is unavailable or file is unreadable.
    """
    ext = Path(filename).suffix.lower()

    if ext == ".pdf":
        try:
            import fitz  # PyMuPDF
            doc  = fitz.open(stream=file_bytes, filetype="pdf")
            page = doc[0]
            # 2x zoom for better OCR resolution
            mat  = fitz.Matrix(2.0, 2.0)
            pix  = page.get_pixmap(matrix=mat)
            img  = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)
            return cv2.cvtColor(np.array(img), cv2.COLOR_RGB2BGR)
        except ImportError:
            raise ValueError(
                "PDF support requires PyMuPDF: pip install pymupdf"
            )
    else:
        nparr = np.frombuffer(file_bytes, np.uint8)
        img   = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
        if img is None:
            raise ValueError(f"Could not read image file: {filename}")
        return img


# ─── OCR Extraction ───────────────────────────────────────────
def extract_text(img_array: np.ndarray) -> str:
    """
    Run Tesseract OCR on preprocessed image.

    Args:
        img_array (np.ndarray): Raw image array.

    Returns:
        str: Extracted text string.
    """
    processed = preprocess_image(img_array)
    pil_img   = Image.fromarray(processed)
    text      = pytesseract.image_to_string(
        pil_img,
        lang   = "eng",
        config = "--psm 6 --oem 3"
    )
    return text.strip()


# ─── Certificate Number Extraction ────────────────────────────
def extract_certificate_number(text: str, doc_type: str) -> str:
    """
    Extract certificate number from OCR text for mock verification.
    Certificate number is used to look up the mock govt database.

    Args:
        text     (str): Raw OCR text.
        doc_type (str): Document type code.

    Returns:
        str: Certificate number if found, None otherwise.
    """
    patterns = {
        "aadhaar": [
            # Standard Aadhaar format: XXXX-XXXX-XXXX or XXXX XXXX XXXX
            r'\b(\d{4}[\s\-]\d{4}[\s\-]\d{4})\b',
        ],
        "bpl_card": [
            # BPL/STATE/YEAR/NUMBER
            r'\b(BPL[\/\-][A-Z]{2}[\/\-]\d{4}[\/\-]\d{3,6})\b',
        ],
        "disability_certificate": [
            # DIS/STATE/YEAR/NUMBER
            r'\b(DIS[\/\-][A-Z]{2}[\/\-]\d{4}[\/\-]\d{3,6})\b',
        ],
        "death_certificate": [
            # DC/STATE/YEAR/NUMBER
            r'\b(DC[\/\-][A-Z]{2}[\/\-]\d{4}[\/\-]\d{3,6})\b',
        ],
    }
    for pattern in patterns.get(doc_type, []):
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            return match.group(1).upper().replace(" ", "-")
    return None


# ─── Field Extractors ─────────────────────────────────────────
def extract_aadhaar_fields(text: str) -> dict:
    """
    Extract age, gender, state and area type from Aadhaar card text.

    Args:
        text (str): OCR text from Aadhaar card.

    Returns:
        dict: Extracted fields with keys matching model feature names.
    """
    fields = {}

    # Age — try DOB pattern first, then direct age pattern
    dob_match = re.search(
        r'(?:DOB|Date of Birth|d\.o\.b)[:\s]+(\d{2})[\/\-](\d{2})[\/\-](\d{4})',
        text, re.IGNORECASE
    )
    if dob_match:
        from datetime import date
        birth_year    = int(dob_match.group(3))
        fields["age"] = date.today().year - birth_year

    age_match = re.search(
        r'\b(?:Age|AGE)[:\s]+(\d{2,3})', text, re.IGNORECASE
    )
    if age_match and "age" not in fields:
        fields["age"] = int(age_match.group(1))

    # Gender
    if re.search(r'\b(MALE|Male)\b', text):
        fields["gender"] = "Male"
    elif re.search(r'\b(FEMALE|Female)\b', text):
        fields["gender"] = "Female"

    # State — match against known Indian states
    for state in INDIAN_STATES:
        if state.lower() in text.lower():
            fields["state"] = state
            break

    # Area type — rough heuristic based on PIN code prefix
    pin_match = re.search(r'\b(\d{6})\b', text)
    if pin_match:
        pin         = pin_match.group(1)
        metro_pins  = ["110", "400", "700", "600", "500", "560", "380"]
        fields["area_type"] = (
            "Urban" if any(pin.startswith(p) for p in metro_pins)
            else "Rural"
        )

    # Aadhaar presence confirms aadhaar_linked
    fields["aadhaar_linked"] = "Yes"
    return fields


def extract_bpl_fields(text: str) -> dict:
    """
    Extract annual income and BPL status from BPL card text.

    Args:
        text (str): OCR text from BPL card.

    Returns:
        dict: Extracted fields.
    """
    fields = {}

    # Annual income — multiple common patterns
    income_patterns = [
        r'(?:Annual Income|ANNUAL INCOME)[:\s]+(?:Rs\.?|INR|₹)?\s*([\d,]+)',
        r'(?:Rs\.?|INR|₹)\s*([\d,]+)\s*(?:per annum|p\.a\.|annually)',
        r'income[:\s]+(?:Rs\.?|INR|₹)?\s*([\d,]+)',
    ]
    for pattern in income_patterns:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            fields["annual_income"] = int(match.group(1).replace(",", ""))
            break

    # BPL / APL status
    if re.search(r'\b(BPL|Below Poverty Line)\b', text, re.IGNORECASE):
        fields["bpl_card"] = "Yes"
    elif re.search(r'\b(APL|Above Poverty Line)\b', text, re.IGNORECASE):
        fields["bpl_card"] = "No"

    return fields


def extract_disability_fields(text: str) -> dict:
    """
    Extract disability percentage and type from disability certificate.

    Args:
        text (str): OCR text from disability certificate.

    Returns:
        dict: Extracted fields.
    """
    fields = {"has_disability": "Yes"}

    # Disability percentage
    pct_patterns = [
        r'(\d{1,3})\s*(?:%|percent)\s*(?:disability|disabled|impairment)',
        r'(?:disability|disabled)[:\s]+(\d{1,3})\s*(?:%|percent)',
        r'(\d{1,3})%',
    ]
    for pattern in pct_patterns:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            pct = int(match.group(1))
            if 0 < pct <= 100:
                fields["disability_percentage"] = pct
                break

    # Disability type — keyword mapping
    type_map = {
        "locomotor":    "Locomotor",
        "visual":       "Visual",
        "hearing":      "Hearing",
        "mental":       "Mental Illness",
        "intellectual": "Intellectual",
        "cerebral":     "Cerebral Palsy",
        "multiple":     "Multiple Disabilities",
    }
    for keyword, dtype in type_map.items():
        if keyword in text.lower():
            fields["disability_type"] = dtype
            break

    return fields


def extract_death_cert_fields(text: str) -> dict:
    """
    Extract marital status from spouse death certificate.

    Args:
        text (str): OCR text from death certificate.

    Returns:
        dict: marital_status set to Widowed.
    """
    return {"marital_status": "Widowed"}


# ─── Document Type Detector ───────────────────────────────────
def detect_document_type(text: str) -> str:
    """
    Identify document type from OCR text keywords.

    Args:
        text (str): Raw OCR text.

    Returns:
        str: Document type code or 'unknown'.
    """
    text_lower = text.lower()

    if any(kw in text_lower for kw in
           ["aadhaar", "aadhar", "uidai", "unique identification"]):
        return "aadhaar"

    elif any(kw in text_lower for kw in
             ["income certificate", "annual income", "income proof",
              "below poverty", "bpl"]):
        return "bpl_card"

    elif any(kw in text_lower for kw in
             ["disability certificate", "person with disability",
              "handicap", "divyangjan", "udid"]):
        return "disability_certificate"

    elif any(kw in text_lower for kw in
             ["death certificate", "cause of death", "deceased"]):
        return "death_certificate"

    return "unknown"


# ─── Main Document Processor ──────────────────────────────────
async def process_document(file: UploadFile) -> dict:
    """
    Full OCR pipeline for a single uploaded document.

    Pipeline:
        1. Validate file type and size
        2. Load image from bytes
        3. Run Tesseract OCR
        4. Detect document type
        5. Extract relevant fields
        6. Extract certificate number for verification

    Args:
        file (UploadFile): Uploaded document file.

    Returns:
        dict: {
            success             (bool),
            document_type       (str),
            extracted           (dict),   fields for form auto-fill
            certificate_number  (str),    for mock verification
            verification_status (str),    always "pending" at this stage
            raw_text            (str),    first 500 chars for debugging
            filename            (str),
            error               (str)     only if success=False
        }
    """
    # Step 1 — Validate file extension
    ext = Path(file.filename).suffix.lower()
    if ext not in ALLOWED_EXTENSIONS:
        return {
            "success": False,
            "error":   f"File type '{ext}' not allowed. "
                       f"Accepted: {ALLOWED_EXTENSIONS}",
            "filename": file.filename,
        }

    # Step 2 — Validate file size
    file_bytes = await file.read()
    if len(file_bytes) > MAX_UPLOAD_MB * 1024 * 1024:
        return {
            "success": False,
            "error":   f"File too large. Maximum size: {MAX_UPLOAD_MB}MB",
            "filename": file.filename,
        }

    try:
        # Step 3 — Load image and run OCR
        img      = load_image_from_bytes(file_bytes, file.filename)
        raw_text = extract_text(img)

        # Step 4 — Detect document type
        doc_type = detect_document_type(raw_text)

        # Step 5 — Extract fields by document type
        extractors = {
            "aadhaar":              extract_aadhaar_fields,
            "bpl_card":             extract_bpl_fields,
            "disability_certificate": extract_disability_fields,
            "death_certificate":    extract_death_cert_fields,
        }
        extracted = {}
        if doc_type in extractors:
            extracted = extractors[doc_type](raw_text)

        # Step 6 — Extract certificate number for mock verification
        cert_number = extract_certificate_number(raw_text, doc_type)

        return {
            "success":             True,
            "document_type":       doc_type,
            "extracted":           extracted,
            "certificate_number":  cert_number,
            "verification_status": "pending",
            "raw_text":            raw_text[:500],
            "filename":            file.filename,
        }

    except Exception as e:
        return {
            "success":  False,
            "error":    str(e),
            "filename": file.filename,
        }


# ─── Multiple Documents Processor ────────────────────────────
async def process_multiple_documents(files: list) -> dict:
    """
    Process multiple uploaded documents and merge extracted fields.
    Later documents override earlier ones for the same field.

    Args:
        files (list): List of UploadFile objects.

    Returns:
        dict: {
            success   (bool),
            documents (list),  per-file results
            extracted (dict),  merged fields from all documents
            message   (str)
        }
    """
    merged   = {}
    doc_info = []

    for file in files:
        result = await process_document(file)
        doc_info.append({
            "filename":            result.get("filename"),
            "document_type":       result.get("document_type"),
            "success":             result.get("success"),
            "certificate_number":  result.get("certificate_number"),
            "verification_status": result.get("verification_status"),
            "error":               result.get("error"),
        })
        if result["success"]:
            # Merge fields — later documents override earlier ones
            merged.update(result.get("extracted", {}))

    success_count = sum(1 for d in doc_info if d["success"])

    return {
        "success":   success_count > 0,
        "documents": doc_info,
        "extracted": merged,
        "message":   (
            f"Successfully processed {success_count}/{len(files)} documents. "
            f"Please verify extracted fields before submitting."
        ),
    }