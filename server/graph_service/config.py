from functools import lru_cache
from typing import Annotated

from fastapi import Depends
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict  # type: ignore


class Settings(BaseSettings):
    llm_provider: str = 'openai'
    openai_api_key: str
    openai_base_url: str | None = Field(None)
    model_name: str | None = Field(None)
    embedding_provider: str = 'openai'
    embedding_model_name: str | None = Field(None)
    embedding_base_url: str | None = Field(None)
    embedding_api_key: str | None = Field(None)
    reranker_provider: str | None = Field(None)
    reranker_model_name: str | None = Field(None)
    reranker_api_key: str | None = Field(None)
    reranker_base_url: str | None = Field(None)
    neo4j_uri: str
    neo4j_user: str
    neo4j_password: str
    graphiti_api_key: str | None = Field(None)

    model_config = SettingsConfigDict(env_file='.env', extra='ignore')


@lru_cache
def get_settings():
    return Settings()  # type: ignore[call-arg]


ZepEnvDep = Annotated[Settings, Depends(get_settings)]
