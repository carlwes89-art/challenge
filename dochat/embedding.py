from sentence_transformers import SentenceTransformer

model = SentenceTransformer("sentence-transformers/all-MiniLM-L6-v2")

texte = "Comment activer Microsoft Azure for Students ?"

embedding = model.encode(texte)

print("Nombre de dimensions :", len(embedding))
print("Embedding :")
print(embedding)