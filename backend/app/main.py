import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv
import logging
load_dotenv()

from .core.config import get_settings
from .api.routes import router as api_router

settings = get_settings()

logging.basicConfig(
    filename='app.log',  # or any path you want
    level=logging.INFO,  # or DEBUG, WARNING, etc.
    format='%(asctime)s %(levelname)s %(name)s %(message)s'
)
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
