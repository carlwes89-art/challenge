"""
Configuration centralisée de l'application.
Toutes les valeurs sont surchargeables via un fichier .env (voir .env.example).
"""
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    # --- Général ---
    app_name: str = "RAG Notebook Chatbot"
    data_dir: str = "./data"                 # racine de stockage (uploads, db, vectorstore)

    # --- LLM ---
    # "ollama" ou "anthropic" -> permet de changer de moteur sans toucher au code
    llm_provider: str = "ollama"
    ollama_model: str = "qwen2.5:7b"
    ollama_host: str = "http://localhost:11434"
    anthropic_model: str = "claude-sonnet-4-6"
    anthropic_api_key: str = ""

    # --- Embeddings ---
    embedding_model: str = "sentence-transformers/all-MiniLM-L6-v2"

    # --- Chunking ---
    chunk_size: int = 1000
    chunk_overlap: int = 150

    # --- Retrieval ---
    top_k: int = 5

    @property
    def uploads_dir(self) -> str:
        return f"{self.data_dir}/uploads"

    @property
    def chroma_dir(self) -> str:
        return f"{self.data_dir}/chroma"

    @property
    def sqlite_path(self) -> str:
        return f"{self.data_dir}/app.db"


settings = Settings()
