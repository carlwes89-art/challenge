"""
Important : DATA_DIR doit être défini AVANT le premier import de app.config
(la config est chargée une seule fois, à l'import). On le fait donc au
niveau module ici, car conftest.py est importé par pytest avant les
fichiers de test eux-mêmes.
"""
import os
import tempfile

os.environ["DATA_DIR"] = tempfile.mkdtemp(prefix="rag_test_")
