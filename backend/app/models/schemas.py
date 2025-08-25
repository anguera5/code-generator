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


class PullRequestInfo(BaseModel):
    title: str
    body: str | None = None
    base_branch: str | None = None
    head_branch: str | None = None
    repository: str | None = None
    diff_url: str | None = None


class CodeReviewResponse(BaseModel):
    review: str

class FpfRagRequest(BaseModel):
    prompt: str = Field(..., min_length=0, max_length=8000)
    api_key: str
    config_key: str
class FpfRagResponse(BaseModel):
    reply: str

class ChemblSqlPlanRequest(BaseModel):
    prompt: str
    api_key: str


class ChemblSqlPlanResponse(BaseModel):
    sql: str
    related_tables: list[str] | None = None


class ChemblSqlExecuteRequest(BaseModel):
    sql: str = Field(..., min_length=1)
    limit: int | None = Field(default=100, ge=1, le=10000)


class ChemblSqlExecuteResponse(BaseModel):
    columns: list[str]
    rows: list[list]

