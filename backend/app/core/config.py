import os
from pydantic import BaseModel


class Settings(BaseModel):
    openai_api_key: str | None = None
    openai_model: str = "gpt-3.5-turbo"
    temperature: str
    app_name: str = "CodeGen API"


def get_settings() -> Settings:
    return Settings(
        openai_api_key=os.getenv("OPENAI_API_KEY"),
        openai_model=os.getenv("OPENAI_MODEL", "gpt-3.5-turbo"),
        temperature=os.getenv("TEMPERATURE", "0.3"),
    )
