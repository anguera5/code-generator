import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv
import logging
import os
import time
from logging.handlers import TimedRotatingFileHandler
from datetime import datetime, timezone
load_dotenv()

from .core.config import get_settings
from .api.routes import router as api_router

settings = get_settings()

# Configure logging: daily rotation at UTC midnight, logs under fixed path
LOG_DIR = "/var/log/genai-portfolio"
os.makedirs(LOG_DIR, exist_ok=True)

logger = logging.getLogger()
logger.setLevel(logging.INFO)

# Avoid duplicate handlers if module reloaded (e.g., during uvicorn reload)
if not any(isinstance(h, TimedRotatingFileHandler) for h in logger.handlers):
    log_path = os.path.join(LOG_DIR, "app.log")
    file_handler = TimedRotatingFileHandler(
        filename=log_path,
        when="midnight",
        interval=1,
        utc=True,
        backupCount=14,  # keep two weeks of logs
        encoding="utf-8",
    )
    # Name rotated files with date suffix
    file_handler.suffix = "%Y-%m-%d"

    formatter = logging.Formatter(
        fmt="%(asctime)s %(levelname)s %(name)s %(message)s",
        datefmt="%Y-%m-%dT%H:%M:%SZ",
    )
    # Force UTC timestamps in logs
    formatter.converter = time.gmtime
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)

    # Also log to stdout for container logs
    if not any(isinstance(h, logging.StreamHandler) for h in logger.handlers):
        stream_handler = logging.StreamHandler()
        stream_handler.setFormatter(formatter)
        logger.addHandler(stream_handler)

logger.info("Starting FastAPI app at %s", datetime.now(timezone.utc).isoformat())
app = FastAPI(title=settings.app_name)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(api_router, prefix="/api")


if __name__ == "__main__":
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)
