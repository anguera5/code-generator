import re
from langchain_ollama import ChatOllama
from langchain_openai import ChatOpenAI
from app.core.config import get_settings
from app.core.prompts import generate_code_template, generate_test_template, generate_documentation_template

_settings = get_settings()

class LLMModel:
    def __init__(self):
        if not _settings.openai_api_key:
            raise ValueError("The OpenAI API key is missing!")
        self.model = ChatOpenAI(api_key=_settings.openai_api_key, 
                                model=_settings.openai_model,
                                temperature=_settings.temperature)

    def generate_code(self, prompt: str, language: str):
        processed_prompt = generate_code_template(language, prompt)
        response = self.model.invoke(processed_prompt)
        text = response.content or ""
        return self.strip_markdown_fences(text)

    def generate_tests(self, code: str):
        processed_prompt = generate_test_template(code)
        response = self.model.invoke(processed_prompt)
        text = response.content or ""
        return self.strip_markdown_fences(text)

    def generate_docs(self, code: str):
        processed_prompt = generate_documentation_template(code)
        response = self.model.invoke(processed_prompt)
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
