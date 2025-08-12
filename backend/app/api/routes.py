from fastapi import APIRouter
from app.models.schemas import (
    GenerateRequest,
    GenerateResponse,
    BasicRequest,
    BasicResponse,
)
from app.services.llm_model import LLMModel
from app.core.config import get_settings

router = APIRouter()
settings = get_settings()
llm = LLMModel()

@router.get("/")
def root():
    return {"message": "Welcome to the GenAI API. Use /generate, /tests, or /docs endpoints."}

@router.post("/generate", response_model=GenerateResponse)
async def generate_code(payload: GenerateRequest):
    text = llm.generate_code(payload.prompt, payload.language, payload.api_key)
    return GenerateResponse(code=text, language=payload.language)


@router.post("/tests", response_model=BasicResponse)
async def generate_tests(payload: BasicRequest):
    text = llm.generate_tests(payload.code)
    return BasicResponse(code=text)

@router.post("/docs", response_model=BasicResponse)
async def generate_docs(payload: BasicRequest):
    text = llm.generate_docs(payload.code)
    return BasicResponse(code=text)
