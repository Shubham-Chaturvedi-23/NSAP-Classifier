"""
run.py
======
Single entry point to start the NSAP Classification API.

Usage:
    python run.py

Then open:
    http://localhost:8000/docs   ← Swagger UI (use for demo)
    http://localhost:8000/redoc  ← ReDoc UI
"""

import uvicorn
from config import API_HOST, API_PORT

if __name__ == "__main__":
    uvicorn.run(
        "api.app:app",
        host    = API_HOST,
        port    = API_PORT,
        reload  = True,   # auto-restart on code change
        workers = 1,
    )
