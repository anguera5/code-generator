from pydantic import BaseModel, Field

class GenerateRequest(BaseModel):
    prompt: str = Field(..., min_length=1, max_length=8000)
    language: str


class GenerateResponse(BaseModel):
    code: str
    language: str


class BasicRequest(BaseModel):
    code: str = Field(..., min_length=1)


class BasicResponse(BaseModel):
    code: str = Field(..., min_length=1)


class ErrorResponse(BaseModel):
    detail: str
