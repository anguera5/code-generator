import re
from fastapi import HTTPException
from langchain_openai import ChatOpenAI
from langchain_chroma import Chroma
from langchain_openai import OpenAIEmbeddings
from app.core.config import get_settings
from app.core.prompts import (
    generate_code_template,
    generate_test_template,
    generate_documentation_template,
    generate_code_review_template,
)
from app.services.rag_model import build_langgraph, rag_answer_process
from app.services.chembl_sql_pipeline import ChemblSqlPipeline
import logging

_settings = get_settings()
logger = logging.getLogger(__name__)

class LLMModel:
    def __init__(self):
        self.model = _settings.openai_model
        self.temperature = _settings.temperature
        self.api_key = None
        self.llm = None
        self.embeddings = None
        self.vector_store_website = None
        self.vector_store_sql = None
        self.rag_chain = None
        self.chembl_pipeline = None

    def check_model_running(self, api_key: str):
        # Re-initialize LLM if API key changed
        if not self.api_key and api_key not in [None, '', self.api_key]:
            self.api_key = api_key
            # Add request-level timeout to avoid long hanging LLM calls
            self.llm = ChatOpenAI(
                model=self.model,
                temperature=self.temperature,
                openai_api_key=api_key,
                timeout=55,  # seconds (shorter than typical reverse proxy timeouts)
            )
            self.embeddings = OpenAIEmbeddings(model=_settings.openai_embedding_model, api_key=api_key)
            self.vector_store_website = Chroma(
                embedding_function=self.embeddings,
                persist_directory="app/chroma_db",
            )
            self.vector_store_sql = Chroma(
                collection_name="chembl_schema",
                embedding_function=self.embeddings,
                persist_directory="app/chroma_db",
            )
        if not self.llm:
            raise HTTPException(status_code=400, detail="API key is required to initialize the model.")
        return True


    # ---------------------- Code Generation ----------------------
    def generate_code(self, prompt: str, language: str, api_key: str):
        self.check_model_running(api_key)
        if not prompt or len(prompt) < 1 or len(prompt) > 8000:
            raise HTTPException(status_code=400, detail="Please introduce code-related prompt")
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
    
    def generate_rag_response(self, prompt, api_key, config_key):
        if not self.check_model_running(api_key) or not self.rag_chain:
            print("Initializing chain")
            print("Using model: ", self.llm.get_name())
            self.initialize_chain()
        return rag_answer_process(self.rag_chain, prompt, config_key)

    def initialize_chain(self):
        self.rag_chain = build_langgraph(self.llm, self.vector_store_website)
        return

    def run_chembl_full(self, prompt: str, limit: int, api_key: str):
        self.check_model_running(api_key)
        if not self.chembl_pipeline:
            self.chembl_pipeline = ChemblSqlPipeline(self.llm, self.vector_store_sql)
        return self.chembl_pipeline.run_all(prompt, limit)

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
