# DoChat

DoChat est un prototype d'assistant conversationnel basé sur le pattern **RAG** (*Retrieval-Augmented Generation*). Il lit un document PDF, le découpe en passages, recherche les passages pertinents pour une question, les reclasse, puis demande à un modèle local Ollama de générer une réponse fondée uniquement sur le contexte retrouvé.

Le projet contient actuellement un document d'exemple sur l'activation des avantages Epitech.

## Fonctionnement

Le pipeline principal, situé dans `ingest.py`, suit ces étapes :

1. Lecture du PDF avec `pypdf`.
2. Nettoyage et découpage du texte en chunks de 500 caractères, avec un chevauchement de 100 caractères.
3. Génération des embeddings avec `sentence-transformers/all-MiniLM-L6-v2`.
4. Recherche des 10 passages les plus proches par similarité cosinus.
5. Reclassement des résultats avec `cross-encoder/ms-marco-MiniLM-L-6-v2`.
6. Génération d'une réponse avec le modèle local `llama3.2:3b` via Ollama.
7. Vérification approximative de la fidélité de chaque affirmation par rapport au contexte récupéré.

## Prérequis

- Python 3.10 ou supérieur
- [Ollama](https://ollama.com/) installé et démarré
- Le modèle Ollama `llama3.2:3b`
- Une connexion Internet lors du premier lancement pour télécharger les modèles Sentence Transformers et CrossEncoder

## Installation sous Windows

Depuis PowerShell, à la racine du projet :

```powershell
python -m venv venv
.\venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

Si PowerShell bloque l'activation de l'environnement virtuel :

```powershell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy RemoteSigned
.\venv\Scripts\Activate.ps1
```

Installez ensuite le modèle utilisé par la génération :

```powershell
ollama pull llama3.2:3b
```

Ollama doit rester actif pendant l'exécution du programme. Pour vérifier son installation :

```powershell
ollama list
```

## Lancer l'assistant

Le document utilisé par défaut est :

```text
documents/Avantages_Epitech_Activation-1.pdf
```

Lancez le pipeline avec :

```powershell
python ingest.py
```

Après l'initialisation, saisissez une question. Par exemple :

```text
Comment activer Microsoft Azure for Students ?
```

Tapez `exit` pour quitter l'application.

Le programme affiche les étapes du pipeline, les scores de recherche et de reranking, la réponse générée ainsi qu'un score de fidélité indicatif.

## Utiliser un autre PDF

Le chemin du document est actuellement défini directement dans `ingest.py` avec la constante `DOCUMENT_PATH` :

```python
DOCUMENT_PATH = "./documents/Avantages_Epitech_Activation-1.pdf"
```

Pour analyser un autre document, placez-le dans `documents/`, puis modifiez cette constante. Le format PDF est le seul format pris en charge actuellement.

## Structure du projet

```text
.
├── documents/
│   └── Avantages_Epitech_Activation-1.pdf
├── chat.py          # Réservé à une future interface de chat
├── embedding.py     # Exemple minimal de génération d'embedding
├── ingest.py        # Pipeline RAG complet et interface interactive
├── llm.py           # Exemple minimal d'appel à Ollama
├── requirements.txt # Dépendances Python
└── README.md
```

## Scripts de démonstration

Générer un embedding pour une phrase :

```powershell
python embedding.py
```

Tester un appel direct à Ollama avec un contexte prédéfini :

```powershell
python llm.py
```

## Configuration principale

Les paramètres du pipeline sont regroupés au début de `ingest.py` :

| Paramètre | Valeur par défaut | Rôle |
|---|---:|---|
| `CHUNK_SIZE` | `500` | Taille maximale d'un passage |
| `CHUNK_OVERLAP` | `100` | Chevauchement entre passages |
| `RETRIEVAL_K` | `10` | Nombre de résultats issus de la recherche vectorielle |
| `FINAL_K` | `3` | Nombre de passages transmis au modèle |
| `FAITHFULNESS_THRESHOLD` | `0.75` | Seuil de validation d'une affirmation |
| `LLM_MODEL` | `llama3.2:3b` | Modèle utilisé par Ollama |
| `EMBEDDING_MODEL` | `sentence-transformers/all-MiniLM-L6-v2` | Modèle d'embeddings |
| `RERANKER_MODEL` | `cross-encoder/ms-marco-MiniLM-L-6-v2` | Modèle de reranking |

## Limites connues

- Le PDF et les modèles sont configurés en dur dans le code.
- La base vectorielle est construite en mémoire à chaque lancement ; elle n'est pas persistée entre deux exécutions.
- `chromadb` est listé dans les dépendances mais n'est pas encore utilisé par le pipeline actuel.
- La qualité dépend de l'extraction de texte du PDF et des modèles téléchargés.
- Le score de fidélité est une mesure heuristique, et ne constitue pas une garantie absolue de correction.
- Les PDF scannés nécessitant de l'OCR ne sont pas pris en charge directement.

## Dépannage

### `Document introuvable`

Vérifiez que le fichier existe bien dans `documents/` et que `DOCUMENT_PATH` correspond à son nom.

### `ollama` ne répond pas

Lancez Ollama, puis vérifiez que le modèle est disponible :

```powershell
ollama run llama3.2:3b
```

### Première exécution lente

Les modèles Sentence Transformers et CrossEncoder sont téléchargés et chargés au premier lancement. Les exécutions suivantes sont généralement plus rapides, selon la machine disponible.

## Licence

Aucune licence n'est définie dans le dépôt pour le moment.
