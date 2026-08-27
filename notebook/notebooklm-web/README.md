# RAG Notebook Chatbot — Frontend statique (HTML/JS)

Ceci remplace l'interface Streamlit (`streamlit_app/`) par un site **100% statique**
(HTML + CSS + JS vanilla, sans build), déployable sur **Vercel** (ou Netlify, GitHub Pages, etc).

Le backend FastAPI (`app/`) n'est **pas concerné** : il continue de tourner tel quel
(Uvicorn, Docker...). Ce dossier ne contient que le frontend qui l'appelle en HTTP.

## Structure

```
notebooklm-web/
├── index.html                  Accueil
├── espace-utilisateur.html     Chat + gestion des notebooks/documents
├── espace-developpeur.html     Stats, comparaison de moteurs, pipeline RAG
├── assets/
│   ├── style.css                Design (thème "carnet", carte-index)
│   ├── config.js                 Résolution de l'URL du backend (voir plus bas)
│   └── api.js                    Client API (équivalent de streamlit_app/utils/api_client.py)
└── vercel.json                  Config de déploiement Vercel
```

## Pourquoi une config d'URL backend au runtime, et pas en dur ?

Un site Vercel est **statique** : il ne peut pas exécuter FastAPI, SQLite, ChromaDB, etc.
Il faut donc héberger `app/` séparément (Render, Railway, Fly.io, un VPS, Docker...),
puis dire au frontend où le trouver.

Trois façons de régler l'URL du backend, par ordre de priorité :

1. **Paramètre d'URL** (pratique pour partager un lien) : `https://ton-site.vercel.app/?api=https://ton-backend.example.com`
   → mémorisé automatiquement dans le navigateur pour les visites suivantes.
2. **Barre "🔌 Backend"** en haut de chaque page : tape l'URL et clique "Enregistrer".
3. **Valeur par défaut** dans `assets/config.js` (`DEFAULT_API_BASE_URL`, actuellement
   `http://localhost:8000` pour le dev local) — modifie-la si tu veux une valeur par défaut
   différente une fois ton backend déployé.

## Déployer sur Vercel

1. Pousse le dossier `notebooklm-web/` (celui-ci) dans un repo Git, ou utilise
   directement `vercel deploy` depuis ce dossier avec la CLI Vercel.
2. Dans Vercel : **New Project** → sélectionne le repo → *Root Directory* =
   `notebooklm-web` si le reste du projet (backend inclus) est dans le même repo.
   Aucune commande de build n'est nécessaire (site statique).
3. Une fois déployé, ouvre le site et règle l'URL de ton backend dans la barre
   "🔌 Backend" (ou via `?api=...`).

## Déployer le backend séparément

Le backend (`app/`) doit tourner quelque part d'accessible en HTTPS (Render, Railway,
Fly.io, un VPS avec le `Dockerfile` fourni à la racine du projet...). Le CORS est déjà
ouvert (`allow_origins=["*"]`) dans `app/main.py`, donc n'importe quel domaine Vercel
peut l'appeler sans configuration supplémentaire.

## Développement local

Comme il n'y a pas de build, un simple serveur statique suffit :

```bash
cd notebooklm-web
python -m http.server 5500
# puis ouvre http://localhost:5500 (le backend doit tourner sur http://localhost:8000)
```

## Ce qui a changé par rapport à Streamlit

- Les 3 pages Streamlit (`Home.py`, `1_Espace_Utilisateur.py`, `2_Espace_Developpeur.py`)
  sont devenues `index.html`, `espace-utilisateur.html`, `espace-developpeur.html`.
- `utils/api_client.py` est devenu `assets/api.js` (mêmes endpoints, même logique).
- Les graphiques Plotly sont remplacés par **Chart.js** (chargé via CDN).
- Le thème visuel est un thème "carnet / fiche index" sombre (`assets/style.css`),
  au lieu du thème par défaut de Streamlit.
- `requirements-streamlit.txt`, `Dockerfile.streamlit` et `streamlit_app/` ne sont plus
  nécessaires et peuvent être supprimés si tu ne gardes pas la version Streamlit.
