"""
Module: api/services/verification.py
Description: Mock government portal verification service.
             Simulates real-world API calls to UIDAI (Aadhaar),
             State BPL portals, UDID (Disability) and Civil Registry
             (Death Certificate) using seeded test data.

             In production these would be replaced with actual
             authorized API calls requiring government MoUs.

             Disclaimer: For prototype/demo purposes only.
"""

import json
import re
from datetime import datetime

from api.config import (
    VALID_AADHAAR, VALID_BPL,
    VALID_DISABILITY, VALID_DEATH_CERT,
    INVALID_CERTIFICATES, DocType,
    VerificationStatus,
)


def _normalize_aadhaar(cert_number: str) -> str:
    """Normalize Aadhaar to XXXX-XXXX-XXXX when possible."""
    if not cert_number:
        return cert_number

    digits = re.sub(r"\D", "", cert_number)
    if len(digits) == 12:
        return f"{digits[0:4]}-{digits[4:8]}-{digits[8:12]}"

    return cert_number.strip().replace(" ", "-")


def _canonical_cert(cert_number: str) -> str:
    """Canonicalize registry-like certs: collapse separators and uppercase."""
    if not cert_number:
        return cert_number

    return re.sub(r"[^A-Z0-9]+", "/", cert_number.upper()).strip("/")


def _lookup_canonical(mapping: dict, cert_number: str):
    """Find value in mapping using canonicalized key comparison."""
    target = _canonical_cert(cert_number)
    for key, value in mapping.items():
        if _canonical_cert(key) == target:
            return key, value
    return None, None


def _is_invalid_certificate(cert_number: str) -> bool:
    """Check invalid-certificate list with canonicalized comparison."""
    target = _canonical_cert(cert_number)
    return any(_canonical_cert(c) == target for c in INVALID_CERTIFICATES)


# ─── Verification Result Builder ──────────────────────────────
def _build_result(
    status:       str,
    doc_type:     str,
    cert_number:  str,
    data:         dict = None,
    message:      str  = None,
) -> dict:
    """
    Build a standardized verification result dict.

    Args:
        status      (str):  verified | failed | pending
        doc_type    (str):  Document type code
        cert_number (str):  Certificate number checked
        data        (dict): Verified data returned by mock portal
        message     (str):  Human readable status message

    Returns:
        dict: Standardized verification result
    """
    return {
        "status":             status,
        "document_type":      doc_type,
        "certificate_number": cert_number,
        "verified_data":      data or {},
        "message":            message or "",
        "verified_at":        datetime.now().isoformat(),
        # Clearly label as simulated for demo transparency
        "note": (
            "Simulated verification — in production this connects "
            "to authorized government APIs (UIDAI/UDID/State portals)."
        ),
    }


# ─── Individual Verifiers ─────────────────────────────────────
def verify_aadhaar(cert_number: str) -> dict:
    """
    Simulate UIDAI Aadhaar verification.
    Checks certificate number against seeded valid Aadhaar database.

    Args:
        cert_number (str): Aadhaar number in XXXX-XXXX-XXXX format.

    Returns:
        dict: Verification result with name, age, gender, state.
    """
    if not cert_number:
        return _build_result(
            status      = VerificationStatus.FAILED,
            doc_type    = DocType.AADHAAR,
            cert_number = cert_number,
            message     = "No Aadhaar number found in document."
        )

    # Normalize format — ensure XXXX-XXXX-XXXX
    normalized = _normalize_aadhaar(cert_number)

    # Check against known invalid certificates
    if _is_invalid_certificate(normalized):
        return _build_result(
            status      = VerificationStatus.FAILED,
            doc_type    = DocType.AADHAAR,
            cert_number = normalized,
            message     = "Aadhaar number flagged as invalid."
        )

    # Check against valid Aadhaar database
    matched_key, data = _lookup_canonical(VALID_AADHAAR, normalized)
    if data:
        return _build_result(
            status      = VerificationStatus.VERIFIED,
            doc_type    = DocType.AADHAAR,
            cert_number = matched_key,
            data        = data,
            message     = (
                f"Aadhaar verified for {data['name']} "
                f"(Age: {data['age']}, State: {data['state']})"
            )
        )

    return _build_result(
        status      = VerificationStatus.FAILED,
        doc_type    = DocType.AADHAAR,
        cert_number = normalized,
        message     = "Aadhaar number not found in database."
    )


def verify_bpl_card(cert_number: str) -> dict:
    """
    Simulate State BPL portal verification.
    Checks certificate number against seeded BPL card database.

    Args:
        cert_number (str): BPL card number in BPL/STATE/YEAR/NUM format.

    Returns:
        dict: Verification result with holder name and income.
    """
    if not cert_number:
        return _build_result(
            status      = VerificationStatus.FAILED,
            doc_type    = DocType.BPL_CARD,
            cert_number = cert_number,
            message     = "No BPL card number found in document."
        )

    normalized = _canonical_cert(cert_number)

    if _is_invalid_certificate(normalized):
        return _build_result(
            status      = VerificationStatus.FAILED,
            doc_type    = DocType.BPL_CARD,
            cert_number = normalized,
            message     = "BPL card number flagged as invalid."
        )

    matched_key, data = _lookup_canonical(VALID_BPL, normalized)
    if data:
        return _build_result(
            status      = VerificationStatus.VERIFIED,
            doc_type    = DocType.BPL_CARD,
            cert_number = matched_key,
            data        = data,
            message     = (
                f"BPL card verified for {data['holder']} "
                f"(Annual Income: ₹{data['income']:,})"
            )
        )

    return _build_result(
        status      = VerificationStatus.FAILED,
        doc_type    = DocType.BPL_CARD,
        cert_number = normalized,
        message     = "BPL card number not found in database."
    )


def verify_disability_certificate(cert_number: str) -> dict:
    """
    Simulate UDID (Unique Disability ID) portal verification.
    Checks certificate number against seeded disability database.

    Args:
        cert_number (str): Disability cert number in DIS/STATE/YEAR/NUM format.

    Returns:
        dict: Verification result with disability percentage and type.
    """
    if not cert_number:
        return _build_result(
            status      = VerificationStatus.FAILED,
            doc_type    = DocType.DISABILITY,
            cert_number = cert_number,
            message     = "No disability certificate number found in document."
        )

    normalized = _canonical_cert(cert_number)

    if _is_invalid_certificate(normalized):
        return _build_result(
            status      = VerificationStatus.FAILED,
            doc_type    = DocType.DISABILITY,
            cert_number = normalized,
            message     = "Disability certificate flagged as invalid."
        )

    matched_key, data = _lookup_canonical(VALID_DISABILITY, normalized)
    if data:
        return _build_result(
            status      = VerificationStatus.VERIFIED,
            doc_type    = DocType.DISABILITY,
            cert_number = matched_key,
            data        = data,
            message     = (
                f"Disability certificate verified — "
                f"{data['percentage']}% {data['type']} disability."
            )
        )

    return _build_result(
        status      = VerificationStatus.FAILED,
        doc_type    = DocType.DISABILITY,
        cert_number = normalized,
        message     = "Disability certificate number not found in database."
    )


def verify_death_certificate(cert_number: str) -> dict:
    """
    Simulate Civil Registry death certificate verification.
    Checks certificate number against seeded death registry database.

    Args:
        cert_number (str): Death cert number in DC/STATE/YEAR/NUM format.

    Returns:
        dict: Verification result with deceased name and widow name.
    """
    if not cert_number:
        return _build_result(
            status      = VerificationStatus.FAILED,
            doc_type    = DocType.DEATH_CERT,
            cert_number = cert_number,
            message     = "No death certificate number found in document."
        )

    normalized = _canonical_cert(cert_number)

    if _is_invalid_certificate(normalized):
        return _build_result(
            status      = VerificationStatus.FAILED,
            doc_type    = DocType.DEATH_CERT,
            cert_number = normalized,
            message     = "Death certificate flagged as invalid."
        )

    matched_key, data = _lookup_canonical(VALID_DEATH_CERT, normalized)
    if data:
        return _build_result(
            status      = VerificationStatus.VERIFIED,
            doc_type    = DocType.DEATH_CERT,
            cert_number = matched_key,
            data        = data,
            message     = (
                f"Death certificate verified — "
                f"Deceased: {data['deceased']}, "
                f"Widow: {data['widow']}."
            )
        )

    return _build_result(
        status      = VerificationStatus.FAILED,
        doc_type    = DocType.DEATH_CERT,
        cert_number = normalized,
        message     = "Death certificate number not found in database."
    )


# ─── Main Verification Router ─────────────────────────────────
def verify_document(doc_type: str, cert_number: str) -> dict:
    """
    Route verification request to correct verifier by document type.

    Args:
        doc_type    (str): Document type code from DocType class.
        cert_number (str): Certificate number extracted by OCR.

    Returns:
        dict: Standardized verification result.
    """
    verifiers = {
        DocType.AADHAAR:    verify_aadhaar,
        DocType.BPL_CARD:   verify_bpl_card,
        DocType.DISABILITY: verify_disability_certificate,
        DocType.DEATH_CERT: verify_death_certificate,
    }

    verifier = verifiers.get(doc_type)

    if not verifier:
        return _build_result(
            status      = VerificationStatus.FAILED,
            doc_type    = doc_type,
            cert_number = cert_number,
            message     = f"Unknown document type: {doc_type}"
        )

    return verifier(cert_number)


# ─── Batch Verification ───────────────────────────────────────
def verify_documents(documents: list[dict]) -> list[dict]:
    """
    Verify multiple documents at once.

    Args:
        documents (list[dict]): List of dicts with keys:
                                doc_type, certificate_number

    Returns:
        list[dict]: List of verification results.
    """
    return [
        verify_document(
            doc.get("doc_type", ""),
            doc.get("certificate_number", "")
        )
        for doc in documents
    ]


# ─── Verification Summary ─────────────────────────────────────
def get_verification_summary(results: list[dict]) -> dict:
    """
    Summarize verification results for multiple documents.

    Args:
        results (list[dict]): List of verification result dicts.

    Returns:
        dict: {
            all_verified (bool),
            verified_count (int),
            failed_count (int),
            extracted_fields (dict)  merged verified data
        }
    """
    verified_count = sum(
        1 for r in results
        if r["status"] == VerificationStatus.VERIFIED
    )
    failed_count = len(results) - verified_count

    # Merge all verified data into single dict for form auto-fill
    extracted_fields = {}
    for result in results:
        if result["status"] == VerificationStatus.VERIFIED:
            extracted_fields.update(result.get("verified_data", {}))

    return {
        "all_verified":      failed_count == 0,
        "verified_count":    verified_count,
        "failed_count":      failed_count,
        "extracted_fields":  extracted_fields,
    }