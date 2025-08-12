import os
from pydantic import BaseModel


class Settings(BaseModel):
    openai_model: str = "gpt-4.1-mini"
    temperature: str
    app_name: str = "CodeGen API"


def get_settings() -> Settings:
    return Settings(
        openai_model=os.getenv("OPENAI_MODEL", "gpt-4.1-mini"),
        temperature=os.getenv("TEMPERATURE", "0.3"),
    )
