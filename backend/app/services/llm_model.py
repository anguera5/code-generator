import re
from fastapi import HTTPException
from langchain_openai import ChatOpenAI
from app.core.config import get_settings
from app.core.prompts import (
    generate_code_template,
    generate_test_template,
    generate_documentation_template,
    generate_code_review_template,
)

_settings = get_settings()


class LLMModel:
    def __init__(self):
        self.model = _settings.openai_model
        self.temperature = _settings.temperature
        self.api_key = ''
        self.llm = None

    # ---------------------- Code Generation ----------------------
    def generate_code(self, prompt: str, language: str, api_key: str):
        if not prompt or len(prompt) < 1 or len(prompt) > 8000:
            raise HTTPException(status_code=400, detail="Please introduce code-related prompt")
        # Re-initialize LLM if API key changed
        if api_key and api_key != self.api_key:
            self.api_key = api_key
            self.llm = ChatOpenAI(
                model=self.model,
                temperature=self.temperature,
                openai_api_key=api_key,
            )
        if not self.llm:
            raise HTTPException(status_code=400, detail="API key is required to initialize the model.")
        processed_prompt = generate_code_template(language, prompt)
        response = self.llm.invoke(processed_prompt)
        text = response.content or ""
        return self.strip_markdown_fences(text)

    # ---------------------- Tests Generation ----------------------
    def generate_tests(self, code: str):
        if not self.llm:
            raise HTTPException(status_code=400, detail="Model not initialized; generate code first or supply API key.")
        processed_prompt = generate_test_template(code)
        response = self.llm.invoke(processed_prompt)
        text = response.content or ""
        return self.strip_markdown_fences(text)

    # ---------------------- Documentation Generation ----------------------
    def generate_docs(self, code: str):
        if not self.llm:
            raise HTTPException(status_code=400, detail="Model not initialized; generate code first or supply API key.")
        processed_prompt = generate_documentation_template(code)
        response = self.llm.invoke(processed_prompt)
        text = response.content or ""
        return self.strip_markdown_fences(text)

    # ---------------------- Code Review Generation ----------------------
    def generate_code_review(self, title: str, body: str | None, diff_summary: str | None):
        if not self.llm:
            raise HTTPException(status_code=400, detail="Model not initialized; supply API key via /generate first.")
        processed_prompt = generate_code_review_template(title, body or "", diff_summary or "")
        response = self.llm.invoke(processed_prompt)
        text = response.content or ""
        return self.strip_markdown_fences(text)

    # ---------------------- Helpers ----------------------
    def strip_markdown_fences(self, text: str) -> str:
        """Remove triple backtick code fences with optional language hints."""
        if not text:
            return text
        pattern = r"^\s*```[a-zA-Z0-9_\-]*\s*\n([\s\S]*?)\n\s*```\s*$"
        m = re.match(pattern, text.strip())
        if m:
            return m.group(1).strip()
        return text.strip()
