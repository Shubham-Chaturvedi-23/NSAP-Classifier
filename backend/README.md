## Backend Setup

The FastAPI backend stores uploaded NSAP documents in Cloudinary.

Add these values to `backend/.env` before starting the API:

- `CLOUDINARY_CLOUD_NAME`
- `CLOUDINARY_API_KEY`
- `CLOUDINARY_API_SECRET`

The upload flow supports both images and PDFs. Images are uploaded as Cloudinary image resources, while PDFs are uploaded as raw resources so OCR can still process them.

If these variables are missing, document uploads will fail with a clear configuration error instead of silently saving an empty file URL.
