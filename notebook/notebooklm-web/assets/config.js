/*
 * Résolution de l'URL du backend FastAPI.
 * Le frontend est un site statique (déployé sur Vercel) : il ne peut pas
 * embarquer d'URL "en dur" fiable puisque le backend tourne ailleurs
 * (Render, Railway, Fly.io, VM, etc). L'URL est donc :
 *   1. lue depuis ?api=... dans la query string (et mémorisée), sinon
 *   2. lue depuis le localStorage (réglée via la barre de config en haut de page), sinon
 *   3. la valeur par défaut ci-dessous.
 */
const DEFAULT_API_BASE_URL = "https://challenge-3-eme9.onrender.com";
const STORAGE_KEY = "notebooklm_api_base_url";

function getApiBaseUrl() {
  const params = new URLSearchParams(window.location.search);
  const fromQuery = params.get("api");
  if (fromQuery) {
    localStorage.setItem(STORAGE_KEY, fromQuery.replace(/\/+$/, ""));
  }
  const stored = localStorage.getItem(STORAGE_KEY);
  return (stored || DEFAULT_API_BASE_URL).replace(/\/+$/, "");
}

function setApiBaseUrl(url) {
  localStorage.setItem(STORAGE_KEY, url.trim().replace(/\/+$/, ""));
}

/* Barre de configuration réutilisable (affiche/édite l'URL du backend). */
function mountConfigBar(containerId) {
  const el = document.getElementById(containerId);
  if (!el) return;
  el.innerHTML = `
    <div class="config-bar">
      <span class="config-label">🔌 Backend</span>
      <input id="cfg-api-url" class="config-input" type="text" spellcheck="false" />
      <button id="cfg-api-save" class="btn btn-ghost btn-sm">Enregistrer</button>
      <span id="cfg-api-status" class="config-status"></span>
    </div>
  `;
  const input = document.getElementById("cfg-api-url");
  input.value = getApiBaseUrl();
  document.getElementById("cfg-api-save").addEventListener("click", () => {
    setApiBaseUrl(input.value || DEFAULT_API_BASE_URL);
    window.location.reload();
  });
  input.addEventListener("keydown", (e) => {
    if (e.key === "Enter") document.getElementById("cfg-api-save").click();
  });
}
