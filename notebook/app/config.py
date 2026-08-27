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
    # "ollama", "gemini" ou "anthropic" -> permet de changer de moteur sans toucher au code
    # Par défaut "ollama" pour le dev local (docker-compose lance un serveur Ollama).
    # En déploiement sans Ollama (Render, etc), régler LLM_PROVIDER=gemini dans les env vars.
    llm_provider: str = "ollama"
    ollama_model: str = "qwen2.5:7b"
    ollama_host: str = "http://localhost:11434"
    anthropic_model: str = "claude-sonnet-4-6"
    anthropic_api_key: str = ""
    # Gemini (Google AI Studio) : offre gratuite permanente, sans carte bancaire.
    # Clé à récupérer sur https://aistudio.google.com/apikey
    gemini_model: str = "gemini-2.5-flash"
    gemini_api_key: str = ""

    # --- Embeddings ---
    # Calculés localement via le modèle ONNX embarqué par ChromaDB
    # (voir app/services/vectorstore.py) — pas de réglage nécessaire ici.

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
