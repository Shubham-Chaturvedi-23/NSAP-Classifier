"""
Module: api/services/storage.py
Description: Cloudinary file upload and management service.
             Handles document image storage for NSAP applications.
             Returns secure URLs stored in the Document table.
"""

import cloudinary
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


# ─── Upload ───────────────────────────────────────────────────
def upload_document(
    file_bytes:     bytes,
    filename:       str,
    application_id: str,
    doc_type:       str,
) -> dict:
    """
    Upload a document image to Cloudinary.
    Files are organized in folders by application ID.

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
        # Organize uploads: nsap_docs/application_id/doc_type
        public_id = f"nsap_docs/{application_id}/{doc_type}"

        result = cloudinary.uploader.upload(
            file_bytes,
            public_id       = public_id,
            resource_type   = "image",
            overwrite       = True,
            # Transformations for storage optimization
            transformation  = [
                {
                    "quality": "auto",   # auto compress
                    "fetch_format": "auto"
                }
            ],
        )

        return {
            "url":       result["secure_url"],
            "public_id": result["public_id"],
            "format":    result.get("format", ""),
            "bytes":     result.get("bytes", 0),
        }

    except Exception as e:
        raise HTTPException(
            status_code = 500,
            detail      = f"Document upload failed: {e}"
        )


# ─── Delete ───────────────────────────────────────────────────
def delete_document(public_id: str) -> bool:
    """
    Delete a document from Cloudinary by public ID.
    Called when an application is deleted or document is replaced.

    Args:
        public_id (str): Cloudinary public ID returned during upload.

    Returns:
        bool: True if deleted successfully, False otherwise.
    """
    try:
        result = cloudinary.uploader.destroy(public_id)
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
    try:
        # ping Cloudinary API
        cloudinary.api.ping()
        return True
    except Exception:
        return False