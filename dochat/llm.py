import ollama

question = "Comment activer Microsoft Azure for Students ?"

context = """
Microsoft Azure for Students
Avantage : Crédit cloud gratuit.
Activation :
1. Aller sur azure.microsoft.com/students
2. Se connecter avec email étudiant
3. Vérifier statut étudiant
4. Activer le crédit
"""

prompt = f"""
Tu es un assistant qui répond uniquement à partir du contexte fourni.

CONTEXTE :
{context}

QUESTION :
{question}

Réponds uniquement avec les informations présentes dans le contexte.
"""

response = ollama.chat(
    model="llama3.2:3b",
    messages=[
        {
            "role": "user",
            "content": prompt
        }
    ]
)

print(response["message"]["content"])