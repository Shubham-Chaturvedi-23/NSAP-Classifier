"""
Module: api/services/storage.py
Description: Cloudinary file upload and management service.
             Handles document storage for NSAP applications.
             Returns secure URLs stored in the Document table.
"""

from pathlib import Path

import cloudinary
import cloudinary.api
import cloudinary.uploader
from fastapi import HTTPException

from api.config import (
    CLOUDINARY_CLOUD_NAME,
    CLOUDINARY_API_KEY,
    CLOUDINARY_API_SECRET,
)

# ─── Cloudinary Configuration ─────────────────────────────────
cloudinary.config(
    cloud_name = CLOUDINARY_CLOUD_NAME,
    api_key    = CLOUDINARY_API_KEY,
    api_secret = CLOUDINARY_API_SECRET,
    secure     = True,   # always use HTTPS URLs
)


def _is_configured() -> bool:
    return all([
        CLOUDINARY_CLOUD_NAME,
        CLOUDINARY_API_KEY,
        CLOUDINARY_API_SECRET,
    ])


def _infer_resource_type(filename: str) -> str:
    """Map an uploaded file to the Cloudinary resource type we should use."""
    ext = Path(filename).suffix.lower()
    return "raw" if ext == ".pdf" else "image"


# ─── Upload ───────────────────────────────────────────────────
def upload_document(
    file_bytes:     bytes,
    filename:       str,
    application_id: str,
    doc_type:       str,
) -> dict:
    """
    Upload a document to Cloudinary.
    Files are organized by application ID and document type.
    Images are uploaded as image resources, PDFs as raw resources.

    Args:
        file_bytes     (bytes): Raw file content.
        filename       (str):   Original filename.
        application_id (str):   Application UUID for folder organization.
        doc_type       (str):   Document type for public_id naming.

    Returns:
        dict: {
            url        (str):  Secure Cloudinary URL,
            public_id  (str):  Cloudinary public ID for deletion,
            format     (str):  File format,
            bytes      (int):  File size in bytes
        }

    Raises:
        HTTPException 500: If Cloudinary upload fails.
    """
    try:
        if not _is_configured():
            raise HTTPException(
                status_code = 503,
                detail      = (
                    "Cloudinary is not configured. Set CLOUDINARY_CLOUD_NAME, "
                    "CLOUDINARY_API_KEY and CLOUDINARY_API_SECRET in backend/.env."
                ),
            )

        # Organize uploads: nsap_docs/application_id/doc_type
        public_id = f"nsap_docs/{application_id}/{doc_type}"
        resource_type = _infer_resource_type(filename)

        upload_kwargs = {
            "public_id": public_id,
            "resource_type": resource_type,
            "overwrite": True,
        }

        # Image-specific optimization. PDFs are uploaded as raw assets.
        if resource_type == "image":
            upload_kwargs["transformation"] = [
                {
                    "quality": "auto",
                    "fetch_format": "auto",
                }
            ]

        result = cloudinary.uploader.upload(
            file_bytes,
            **upload_kwargs,
        )

        return {
            "url":       result["secure_url"],
            "public_id": result["public_id"],
            "format":    result.get("format", ""),
            "bytes":     result.get("bytes", 0),
            "resource_type": result.get("resource_type", resource_type),
        }

    except Exception as e:
        if isinstance(e, HTTPException):
            raise
        raise HTTPException(
            status_code = 500,
            detail      = f"Document upload failed: {e}"
        )


# ─── Delete ───────────────────────────────────────────────────
def delete_document(public_id: str, resource_type: str = "image") -> bool:
    """
    Delete a document from Cloudinary by public ID.
    Called when an application is deleted or document is replaced.

    Args:
        public_id (str): Cloudinary public ID returned during upload.
        resource_type (str): Cloudinary resource type used during upload.

    Returns:
        bool: True if deleted successfully, False otherwise.
    """
    try:
        result = cloudinary.uploader.destroy(
            public_id,
            resource_type = resource_type,
            invalidate    = True,
        )
        return result.get("result") == "ok"
    except Exception:
        return False


# ─── Get URL ──────────────────────────────────────────────────
def get_document_url(public_id: str, width: int = 800) -> str:
    """
    Generate a Cloudinary URL with optional resizing.
    Useful for displaying document thumbnails in officer review.

    Args:
        public_id (str): Cloudinary public ID.
        width     (int): Optional max width for resizing.

    Returns:
        str: Transformed Cloudinary URL.
    """
    try:
        return cloudinary.CloudinaryImage(public_id).build_url(
            width       = width,
            crop        = "limit",
            fetch_format = "auto",
            quality     = "auto",
            secure      = True,
        )
    except Exception:
        return ""


# ─── Cloudinary Health Check ──────────────────────────────────
def check_cloudinary_connection() -> bool:
    """
    Verify Cloudinary credentials are valid.
    Called during application startup.

    Returns:
        bool: True if connection successful, False otherwise.
    """
    ok, _ = get_cloudinary_connection_status()
    return ok


def get_cloudinary_connection_status() -> tuple[bool, str]:
    """Return Cloudinary connectivity and a human-readable reason."""
    try:
        if not _is_configured():
            return False, "missing credentials"

        # ping Cloudinary API
        cloudinary.api.ping()
        return True, "ok"
    except Exception as exc:
        return False, str(exc)