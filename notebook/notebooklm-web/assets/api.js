/*
 * Client API — équivalent JS de streamlit_app/utils/api_client.py
 * Toutes les pages passent par ce module pour parler au backend FastAPI.
 */
const Api = (() => {
  function url(path) {
    return `${getApiBaseUrl()}${path}`;
  }

  async function request(path, options = {}) {
    const res = await fetch(url(path), {
      headers: options.body instanceof FormData ? {} : { "Content-Type": "application/json" },
      ...options,
    });
    if (!res.ok) {
      let detail = res.statusText;
      try {
        const data = await res.json();
        detail = data.detail || JSON.stringify(data);
      } catch (_) {
        /* réponse non-JSON, on garde statusText */
      }
      throw new Error(detail || `Erreur HTTP ${res.status}`);
    }
    if (res.status === 204) return null;
    return res.json();
  }

  return {
    async healthCheck(timeoutMs = 4000) {
      try {
        const res = await fetch(url("/"), { signal: AbortSignal.timeout(timeoutMs) });
        return res.ok;
      } catch (_) {
        return false;
      }
    },

    /*
     * Certaines plateformes gratuites (ex. Render) mettent le backend en
     * veille après une période d'inactivité : la première requête peut
     * prendre 30 à 60 secondes à réveiller le service. On tente d'abord un
     * check rapide, puis on retente avec un délai long en prévenant
     * l'utilisateur, plutôt que d'afficher "API injoignable" à tort.
     */
    async healthCheckWithWakeup(onWaking) {
      const quick = await this.healthCheck(4000);
      if (quick) return true;
      if (onWaking) onWaking();
      return this.healthCheck(75000);
    },

    // ---------- Notebooks ----------
    getNotebooks() {
      return request("/notebooks");
    },
    createNotebook(name, description = "") {
      return request("/notebooks", { method: "POST", body: JSON.stringify({ name, description }) });
    },
    deleteNotebook(id) {
      return request(`/notebooks/${id}`, { method: "DELETE" });
    },

    // ---------- Documents ----------
    listDocuments(notebookId) {
      return request(`/notebooks/${notebookId}/documents`);
    },
    uploadDocument(notebookId, file) {
      const form = new FormData();
      form.append("file", file, file.name);
      return request(`/notebooks/${notebookId}/documents`, { method: "POST", body: form });
    },
    deleteDocument(notebookId, documentId) {
      return request(`/notebooks/${notebookId}/documents/${documentId}`, { method: "DELETE" });
    },

    // ---------- Chat ----------
    askQuestion(notebookId, question) {
      return request(`/notebooks/${notebookId}/chat`, { method: "POST", body: JSON.stringify({ question }) });
    },
    getChatHistory(notebookId) {
      return request(`/notebooks/${notebookId}/chat`);
    },
    compareProviders(notebookId, question) {
      return request(`/notebooks/${notebookId}/chat/compare`, { method: "POST", body: JSON.stringify({ question }) });
    },

    // ---------- Stats ----------
    getStatsOverview() {
      return request("/stats/overview");
    },
    getRecentQueries(limit = 50) {
      return request(`/stats/queries?limit=${limit}`);
    },
    getProviderStats() {
      return request("/stats/providers");
    },
    getNotebookStats() {
      return request("/stats/notebooks");
    },
  };
})();
