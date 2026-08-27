# RAG Notebook Chatbot

Chatbot RAG (Retrieval-Augmented Generation) sur documents, façon **NotebookLM** :
tu crées un "notebook", tu y déposes des documents (PDF, DOCX, TXT, MD) sur
n'importe quel sujet, et tu poses des questions. Les réponses sont générées
**uniquement à partir de ces documents**, avec citations précises des sources.

API REST (FastAPI) + deux interfaces Streamlit accessibles depuis une page
d'accueil commune :
- **Espace Utilisateur** : upload de documents et chat, pour tester simplement.
- **Espace Développeur** : statistiques d'usage, comparaison Ollama vs Claude
  en direct, visualisation du pipeline RAG étape par étape.

## Pourquoi ce projet répond au brief

- **N'importe quel sujet** : rien n'est codé en dur sur un domaine particulier. Un notebook peut contenir des cours de droit, un rapport financier ou une thèse de biologie — le pipeline est générique.
- **Isolation par notebook** : comme NotebookLM, les sources d'un notebook ne contaminent jamais les réponses d'un autre.
- **Réponses vérifiables** : chaque réponse cite ses sources ([1], [2]...) avec l'extrait exact utilisé, pour éviter les hallucinations et permettre la vérification.
- **Fonctionne offline et gratuitement** (Ollama + modèle local), avec bascule possible vers l'API Claude pour une meilleure qualité.

## Architecture

```
Client HTTP
    │
    ▼
FastAPI (app/main.py)
    │
    ├── /notebooks            → CRUD des espaces de travail
    ├── /notebooks/{id}/documents → upload, liste, suppression de documents
    └── /notebooks/{id}/chat      → question/réponse + historique
            │
            ▼
    app/services/rag.py  (orchestration RAG)
            │
    ┌───────┴────────┐
    ▼                ▼
ingestion.py      vectorstore.py ──► ChromaDB (persistant, 1 collection / notebook)
(extraction +          │                     embeddings via sentence-transformers (local)
 chunking)              │
                        ▼
                    llm.py ──► Ollama (local, Qwen) OU API Anthropic (au choix)

Métadonnées (notebooks, documents, historique de chat, logs de requêtes) → SQLite (app/db_models.py)
```

### Observabilité (espace développeur)

Chaque exécution du pipeline (via le chat normal ou l'outil de comparaison)
est tracée dans une table `QueryLog` (temps de retrieval, temps de génération,
provider utilisé, nombre de sources). C'est ce qui alimente :

- `GET /stats/overview` — compteurs globaux et latences moyennes
- `GET /stats/providers` — latences moyennes groupées par moteur LLM (Ollama vs Anthropic)
- `GET /stats/notebooks` — répartition documents/chunks/requêtes par notebook
- `GET /stats/queries` — historique brut des requêtes
- `POST /notebooks/{id}/chat/compare` — exécute la même question sur tous les moteurs disponibles en parallèle logique, utile pour comparer qualité/vitesse sans changer de config

### Pipeline RAG en détail

1. **Ingestion** (`services/ingestion.py`) : extraction du texte brut (PyPDF pour les PDF, python-docx pour Word, lecture directe pour TXT/MD), puis découpage en chunks de ~1000 caractères avec 150 caractères de chevauchement (`RecursiveCharacterTextSplitter`), pour ne jamais couper une idée en plein milieu.
2. **Indexation** (`services/vectorstore.py`) : chaque chunk est vectorisé (embeddings `all-MiniLM-L6-v2`, local, gratuit) et stocké dans une collection ChromaDB dédiée au notebook, avec ses métadonnées (nom de fichier, index du chunk).
3. **Retrieval** (`services/rag.py`) : à chaque question, on récupère les *k* chunks les plus proches sémantiquement (similarité cosinus).
4. **Augmentation + génération** : les chunks sont numérotés et injectés dans le prompt système, qui instruit le modèle à ne répondre qu'à partir d'eux et à citer ses sources par numéro. Si aucun chunk pertinent n'est trouvé, le système le dit explicitement plutôt que de laisser le LLM halluciner.
5. **Citations** : les numéros cités par le modèle dans sa réponse sont remappés vers les vraies métadonnées (fichier, extrait) et renvoyés au client.

### Choix techniques (et pourquoi)

| Choix | Alternative écartée | Raison |
|---|---|---|
| ChromaDB | FAISS, Pinecone | Persistant nativement, pas de service externe à gérer, collections isolées faciles |
| sentence-transformers (local) | Embeddings OpenAI/Anthropic | Gratuit, pas de clé API requise, fonctionne offline |
| Ollama + Qwen par défaut | API cloud uniquement | Zéro coût, zéro dépendance réseau pour la démo ; bascule vers Anthropic en une variable d'env si besoin de meilleure qualité |
| SQLite | PostgreSQL | Zéro setup, largement suffisant pour des métadonnées (pas de charge concurrente à gérer ici) |
| RAG orchestré à la main (pas de chaîne LangChain opaque) | `RetrievalQA` LangChain tout-en-un | Contrôle total sur le prompt et les citations, plus facile à expliquer et déboguer |

## Installation

```bash
python -m venv venv
source venv/bin/activate          # Windows : venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env
```

### Option A — LLM local avec Ollama (par défaut, recommandé)

```bash
# Installer Ollama : https://ollama.com/download
ollama pull qwen2.5:7b
ollama serve                       # dans un terminal séparé
```

### Option B — API Anthropic (Claude)

Dans `.env` :
```
LLM_PROVIDER=anthropic
ANTHROPIC_API_KEY=sk-ant-...
```

### Lancer l'API

```bash
uvicorn app.main:app --reload
```

Documentation interactive : http://localhost:8000/docs

### Avec Docker (API + Ollama ensemble)

```bash
docker compose up --build
docker compose exec ollama ollama pull qwen2.5:7b
```

Avec Docker, les deux interfaces Streamlit sont aussi lancées automatiquement
(service `streamlit` dans `docker-compose.yml`).

## Interfaces Streamlit

Deux interfaces, accessibles depuis une page d'accueil commune (`Home.py`),
qui reste disponible dans la barre latérale à tout moment.

```bash
pip install -r requirements-streamlit.txt
cd streamlit_app
streamlit run Home.py
```

Ouvre http://localhost:8501 — le backend (`uvicorn`) doit tourner en parallèle
sur le port 8000 (voir section Installation ci-dessus). Pour pointer vers une
API sur une autre URL/port : `API_BASE_URL=http://localhost:8000 streamlit run Home.py`.

- **🧑 Espace Utilisateur** (`pages/1_Espace_Utilisateur.py`) : créer un
  notebook, uploader des documents, poser des questions dans une interface de
  chat classique avec citations des sources.
- **🛠️ Espace Développeur** (`pages/2_Espace_Developpeur.py`) :
  - vue d'ensemble (notebooks, documents, chunks, requêtes, latences moyennes)
  - comparaison Ollama vs Anthropic (latence moyenne agrégée + test en direct sur une question de ton choix)
  - visualisation du pipeline RAG étape par étape (chunks récupérés, puis réponse générée)
  - répartition par notebook et historique brut des requêtes

## Utilisation

```bash
# 1. Créer un notebook
curl -X POST http://localhost:8000/notebooks \
  -H "Content-Type: application/json" \
  -d '{"name": "Cours de Chimie", "description": "Notes de S3"}'
# -> {"id": "abc-123", ...}

# 2. Ajouter un document
curl -X POST http://localhost:8000/notebooks/abc-123/documents \
  -F "file=@cours_chimie.pdf"

# 3. Poser une question
curl -X POST http://localhost:8000/notebooks/abc-123/chat \
  -H "Content-Type: application/json" \
  -d '{"question": "Quelle est la définition d une réaction exothermique ?"}'
# -> {"answer": "Une réaction exothermique... [1]", "sources": [...]}

# 4. Consulter l'historique
curl http://localhost:8000/notebooks/abc-123/chat
```

## Tests

```bash
pip install pytest httpx
pytest tests/ -v
```

11 tests couvrent : CRUD notebooks, gestion des erreurs (404, format non
supporté), extraction et découpage de texte.

## Limites connues et pistes d'amélioration

- Traitement des documents synchrone : pour de très gros fichiers ou un usage à
  plusieurs utilisateurs, ce traitement partirait en tâche de fond (Celery,
  BackgroundTasks FastAPI) avec un statut `processing` interrogeable.
- Pas d'OCR : les PDF scannés sans couche texte ne sont pas extractibles en l'état
  (ajout possible via Tesseract).
- Pas d'authentification : à ajouter (JWT, comme sur mes projets précédents)
  avant tout déploiement multi-utilisateurs.
- Évaluation qualité : un jeu de questions/réponses de référence avec RAGAS
  permettrait de mesurer objectivement la pertinence du retrieval.
