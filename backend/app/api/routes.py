from fastapi import APIRouter
from app.models.schemas import (
    GenerateRequest,
    GenerateResponse,
    BasicRequest,
    BasicResponse,
    CodeReviewResponse,
    FpfRagRequest,
    FpfRagResponse,
    ChemblSqlPlanRequest,
    ChemblSqlEditRequest,
    ChemblSqlEditResponse,
    ChemblSqlReexecuteRequest,
    ChemblSqlReexecuteResponse,
)
from app.services.llm_model import LLMModel
from app.core.config import get_settings
from typing import Any

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


@router.post("/code-review/webhook", response_model=CodeReviewResponse)
async def code_review_webhook(payload: dict):
    """Accept a generic pull request webhook payload (GitHub-style) and return an LLM review.

    Expected minimal shape:
    {
        "action": "opened",
        "pull_request": {"title": str, "body": str, "base": {"ref": str}, "head": {"ref": str}, "diff_url": str},
        "repository": {"full_name": str}
    }
    """
    pr = payload.get("pull_request") or {}
    title = pr.get("title") or "(untitled PR)"
    body = pr.get("body") or ""
    base_branch = (pr.get("base") or {}).get("ref")
    head_branch = (pr.get("head") or {}).get("ref")
    diff_url = pr.get("diff_url")
    repository = (payload.get("repository") or {}).get("full_name")

    diff_summary = (
    f"Repository: {repository}\nBase: {base_branch} -> Head: {head_branch}\nDiff URL: {diff_url}"
    if (repository or base_branch or head_branch or diff_url)
    else "(no diff metadata provided)"
    )
    review_text = llm.generate_code_review(title, body, diff_summary)
    return CodeReviewResponse(review=review_text)

@router.post("/fpf-rag/chat", response_model=FpfRagResponse)
async def fpf_rag_chat(payload: FpfRagRequest):
    text = llm.generate_rag_response(payload.prompt, payload.api_key, payload.config_key)
    return FpfRagResponse(reply=text)

@router.post("/chembl/run", response_model=dict)
async def chembl_run(payload: ChemblSqlPlanRequest):
    """End-to-end run: plan → retrieve → synthesize → execute.

    Returns: { sql, related_tables, columns, rows, retries, repaired, no_context, not_chembl, chembl_reason }
    """
    try:
        state: dict[str, Any] = llm.run_chembl_full(payload.prompt, limit=100, api_key=payload.api_key)
        # Attach prompt and persist session if memory_id provided
        state["prompt"] = payload.prompt
        if getattr(payload, "memory_id", None):
            llm.chembl_session_set(payload.memory_id, state)
        response = {
            "sql": state.get("sql", ""),
            "related_tables": state.get("structured_tables", []),
            "columns": state.get("columns", []),
            "rows": state.get("rows", []),
            "retries": state.get("retries", 0),
            "repaired": bool(state.get("retries", 0) > 0),
            "no_context": bool(state.get("no_context", False)),
            "not_chembl": bool(state.get("not_chembl", False)),
            "chembl_reason": state.get("chembl_reason", ""),
            "optimized_guidelines": state.get("optimized_guidelines", ""),
            "memory_id": payload.memory_id or None,
        }
        print(response)
        return response
    except ValueError as e:
        from fastapi import HTTPException
        raise HTTPException(status_code=400, detail=str(e)) from e


@router.post("/chembl/edit", response_model=ChemblSqlEditResponse)
async def chembl_edit(payload: ChemblSqlEditRequest):
    """Apply a tweak to the last SQL for a session and return updated SQL/results."""
    # Ensure model running with api key
    llm.check_model_running(payload.api_key)
    state = llm.chembl_apply_edit(payload.memory_id, payload.instruction, payload.api_key, prev_sql=getattr(payload, "prev_sql", None))
    return ChemblSqlEditResponse(
        sql=state.get("sql", ""),
        related_tables=state.get("structured_tables", []),
        columns=state.get("columns", []),
        rows=state.get("rows", []),
        retries=int(state.get("retries") or 0),
        repaired=bool(state.get("repaired") or False),
        no_context=bool(state.get("no_context") or False),
        not_chembl=bool(state.get("not_chembl") or False),
        chembl_reason=state.get("chembl_reason") or "",
        optimized_guidelines=state.get("optimized_guidelines") or "",
    )


@router.post("/chembl/reexecute", response_model=ChemblSqlReexecuteResponse)
async def chembl_reexecute(payload: ChemblSqlReexecuteRequest):
    """Re-execute the last SQL for a given session with a new LIMIT."""
    # Ensure model running with api key
    llm.check_model_running(payload.api_key)
    prev = llm.chembl_session_get(payload.memory_id)
    if not prev:
        from fastapi import HTTPException
        raise HTTPException(status_code=400, detail="Unknown memory_id; run a query first.")
    sql = (prev.get("sql") or "").strip()
    if not sql:
        from fastapi import HTTPException
        raise HTTPException(status_code=400, detail="No SQL present for this session.")
    cols, rows = llm.chembl_reexecute(payload.memory_id, payload.limit, payload.api_key)
    return ChemblSqlReexecuteResponse(columns=cols, rows=rows)
