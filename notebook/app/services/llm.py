"""
Couche d'abstraction LLM.

Le reste de l'app (rag.py) appelle uniquement generate(system, user_prompt)
sans jamais savoir si ça part vers Ollama (local), Gemini ou l'API Anthropic.
Changer de moteur = changer LLM_PROVIDER dans .env, zéro ligne de code à toucher.
"""
import requests

from app.config import settings


def generate(system_prompt: str, user_prompt: str, provider_override: str | None = None) -> str:
    """
    provider_override permet de forcer un moteur précis pour une requête donnée,
    indépendamment du réglage global LLM_PROVIDER. Utilisé par l'outil de
    comparaison de l'espace développeur pour interroger plusieurs moteurs
    sur la même question.
    """
    provider = provider_override or settings.llm_provider
    if provider == "ollama":
        return _generate_ollama(system_prompt, user_prompt)
    if provider == "gemini":
        return _generate_gemini(system_prompt, user_prompt)
    if provider == "anthropic":
        return _generate_anthropic(system_prompt, user_prompt)
    raise ValueError(f"Provider inconnu : {provider}")


def available_providers() -> list[str]:
    """Liste des providers utilisables avec la config actuelle (pour l'UI dev)."""
    providers = ["ollama"]  # toujours listé : configuré par défaut, même si le serveur Ollama n'est pas lancé
    if settings.gemini_api_key:
        providers.append("gemini")
    if settings.anthropic_api_key:
        providers.append("anthropic")
    return providers


def _generate_ollama(system_prompt: str, user_prompt: str) -> str:
    import ollama

    client = ollama.Client(host=settings.ollama_host)
    response = client.chat(
        model=settings.ollama_model,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
        options={"temperature": 0.2},  # basse température : on veut des réponses fidèles aux sources
    )
    return response["message"]["content"]


def _generate_gemini(system_prompt: str, user_prompt: str) -> str:
    """
    Appel direct à l'API REST Gemini (Google AI Studio) plutôt qu'au SDK,
    pour éviter tout risque de dérive de version du SDK : le format REST
    ci-dessous est le contrat public stable de l'API.
    Clé gratuite (sans carte bancaire) : https://aistudio.google.com/apikey
    """
    if not settings.gemini_api_key:
        raise ValueError("GEMINI_API_KEY non configurée")

    url = (
        f"https://generativelanguage.googleapis.com/v1beta/models/"
        f"{settings.gemini_model}:generateContent"
    )
    response = requests.post(
        url,
        params={"key": settings.gemini_api_key},
        json={
            "systemInstruction": {"parts": [{"text": system_prompt}]},
            "contents": [{"role": "user", "parts": [{"text": user_prompt}]}],
            "generationConfig": {"temperature": 0.2, "maxOutputTokens": 1024},
        },
        timeout=60,
    )
    if response.status_code != 200:
        raise RuntimeError(f"Erreur Gemini ({response.status_code}) : {response.text[:300]}")

    data = response.json()
    candidates = data.get("candidates") or []
    if not candidates:
        block_reason = data.get("promptFeedback", {}).get("blockReason")
        raise RuntimeError(f"Gemini n'a renvoyé aucune réponse (block_reason={block_reason})")

    parts = candidates[0].get("content", {}).get("parts", [])
    return "".join(p.get("text", "") for p in parts).strip()


def _generate_anthropic(system_prompt: str, user_prompt: str) -> str:
    import anthropic

    client = anthropic.Anthropic(api_key=settings.anthropic_api_key)
    response = client.messages.create(
        model=settings.anthropic_model,
        max_tokens=1024,
        temperature=0.2,
        system=system_prompt,
        messages=[{"role": "user", "content": user_prompt}],
    )
    return response.content[0].text
