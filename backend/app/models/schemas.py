from pydantic import BaseModel, Field

class GenerateRequest(BaseModel):
    prompt: str = Field(..., min_length=0, max_length=8000)
    language: str
    api_key: str


class GenerateResponse(BaseModel):
    code: str
    language: str


class BasicRequest(BaseModel):
    code: str = Field(..., min_length=1)


class BasicResponse(BaseModel):
    code: str = Field(..., min_length=1)


class ErrorResponse(BaseModel):
    detail: str
