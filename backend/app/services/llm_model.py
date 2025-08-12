import re
from fastapi import HTTPException
from langchain_ollama import ChatOllama # TODO: use OLlama when key is missing
from langchain_openai import ChatOpenAI
from app.core.config import get_settings
from app.core.prompts import generate_code_template, generate_test_template, generate_documentation_template

_settings = get_settings()

class LLMModel:
    def __init__(self):
        self.model = _settings.openai_model
        self.temperature = _settings.temperature
        self.api_key = ''
        self.llm = None

    def generate_code(self, prompt: str, language: str, api_key: str):
        if not prompt or len(prompt) < 1 or len(prompt) > 8000:
            raise HTTPException(status_code=400, detail="Please introduce code-related prompt")
        if api_key != self.api_key:
            self.llm = ChatOpenAI(
                model=self.model,
                temperature=self.temperature,
                openai_api_key=api_key
            )
        if not self.llm:
            raise HTTPException(status_code=400, detail="API key is required to initialize the model.")
        processed_prompt = generate_code_template(language, prompt)
        response = self.llm.invoke(processed_prompt)
        text = response.content or ""
        return self.strip_markdown_fences(text)

    def generate_tests(self, code: str):
        processed_prompt = generate_test_template(code)
        response = self.llm.invoke(processed_prompt)
        text = response.content or ""
        return self.strip_markdown_fences(text)

    def generate_docs(self, code: str):
        processed_prompt = generate_documentation_template(code)
        response = self.llm.invoke(processed_prompt)
        text = response.content or ""
        return self.strip_markdown_fences(text)


    def strip_markdown_fences(self, text: str) -> str:
        # Remove triple backtick code fences with optional language hints
        if not text:
            return text
        pattern = r"^\s*```[a-zA-Z0-9_\-]*\s*\n([\s\S]*?)\n\s*```\s*$"
        m = re.match(pattern, text.strip())
        if m:
            return m.group(1).strip()
        return text.strip()
