"""
Module: run.py
Description: Single entry point to start the NSAP Classification API.
             Reads host and port from config and starts Uvicorn server.

Usage:
    cd backend
    python run.py

Then open:
    http://localhost:8000/docs    ← Swagger UI  (use for demo + testing)
    http://localhost:8000/redoc   ← ReDoc UI    (clean documentation view)

Notes:
    - reload=True   automatically restarts server on code changes
    - workers=1     single worker for development
    - For production use gunicorn with multiple workers instead
"""

import uvicorn
from api.config import API_HOST, API_PORT

if __name__ == "__main__":
    uvicorn.run(
        "api.app:app",
        host    = API_HOST,
        port    = API_PORT,
        reload  = True,    # auto-restart on code change (dev only)
        workers = 1,
    )