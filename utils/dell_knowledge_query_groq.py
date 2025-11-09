import os
os.environ["TOKENIZERS_PARALLELISM"] = "false"
import sys
from docx import Document as DocxDocument
from groq import Groq
from chromadb.utils import embedding_functions
from chromadb import Client

# -----------------------------
# Simple Document class
# -----------------------------
class Document:
    def __init__(self, page_content, metadata=None):
        self.page_content = page_content
        self.metadata = metadata or {}

# -----------------------------
# Configuration
# -----------------------------
BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
DOCS_DIR = os.path.join(BASE_DIR, "docs", "dell-data")
CHROMA_DB_DIR = os.path.join(BASE_DIR, "chroma_dell_db")
MODEL_NAME = "sentence-transformers/all-MiniLM-L6-v2"

# Initialize Groq client
GROQ_KEY = os.getenv("GROQ_API_KEY")
if not GROQ_KEY:
    print("❌ Error: GROQ_API_KEY not set in environment.")
    sys.exit(1)
client = Groq(api_key=GROQ_KEY)

# -----------------------------
# Helper Functions
# -----------------------------
def read_docx(filepath):
    """Read .docx and return text"""
    doc = DocxDocument(filepath)
    return "\n".join([p.text.strip() for p in doc.paragraphs if p.text.strip()])

def chunk_text(text, chunk_size=800, chunk_overlap=100):
    """Simple character-based chunking"""
    chunks = []
    start = 0
    text_len = len(text)
    while start < text_len:
        end = min(start + chunk_size, text_len)
        chunks.append(text[start:end])
        start += chunk_size - chunk_overlap
    return chunks

# -----------------------------
# Chroma Vectorstore
# -----------------------------
def create_vectorstore():
    """Create Chroma vectorstore from .docx files"""
    if not os.path.exists(DOCS_DIR) or not os.listdir(DOCS_DIR):
        print(f"❌ No .docx files found in {DOCS_DIR}")
        sys.exit(1)

    documents = []
    for file in sorted(os.listdir(DOCS_DIR)):
        if file.lower().endswith(".docx"):
            filepath = os.path.join(DOCS_DIR, file)
            text = read_docx(filepath)
            if not text:
                continue
            chunks = chunk_text(text)
            for idx, chunk in enumerate(chunks):
                documents.append(Document(page_content=chunk, metadata={"source": file, "chunk": idx}))
            print(f"✅ {len(chunks)} chunks created for {file}")

    # Create embeddings
    embedding_func = embedding_functions.SentenceTransformerEmbeddingFunction(model_name=MODEL_NAME)
    client_chroma = Client()
    vectordb = client_chroma.create_collection(
        name="dell_kb",
        embedding_function=embedding_func
    )
    vectordb.add(
        documents=[doc.page_content for doc in documents],
        metadatas=[doc.metadata for doc in documents],
        ids=[str(i) for i in range(len(documents))]
    )

    print(f"🎉 Vectorstore created with {len(documents)} chunks")
    return vectordb

def load_vectorstore():
    """Load existing Chroma collection or create if not exists"""
    client_chroma = Client()
    try:
        return client_chroma.get_collection(name="dell_kb")
    except Exception:
        print("ℹ️ Chroma DB not found. Creating from docs...")
        return create_vectorstore()

# -----------------------------
# Groq AI Response
# -----------------------------
def get_ai_response(query, docs):
    """Send query + context to Groq"""
    context = "\n\n".join(docs)
    prompt = f"""
You are a Dell technical support assistant.
Use the following Dell documentation context to answer the question accurately.

Context:
{context}

Question: {query}

Answer in a clear and helpful way for a Dell customer.
"""
    try:
        response = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.3,
        )
        # ✅ Fixed line: use attribute access
        return response.choices[0].message.content.strip()
    except Exception as e:
        return f"⚠️ Error generating AI response: {e}"

# -----------------------------
# Interactive Query Loop
# -----------------------------
def interactive_query(vectordb):
    print("🔎 Dell Knowledge Base — Interactive Query (Groq AI Enabled)\n")
    while True:
        query = input("Q: ").strip()
        if not query or query.lower() in ("exit", "quit"):
            print("Bye 👋")
            break

        # Retrieve top 4 docs
        results = vectordb.query(query_texts=[query], n_results=4)
        docs = results["documents"][0] if results else []

        if not docs:
            print("No results found.\n")
            continue

        print("\n📄 Top Matching Documents:")
        for i, doc in enumerate(docs, 1):
            snippet = doc[:200].replace("\n", " ")
            print(f" {i}. {snippet}...\n")

        print("🤖 Generating AI response via Groq...")
        ai_answer = get_ai_response(query, docs)
        print("\n💬 AI Answer:\n")
        print(ai_answer)
        print("\n" + "-" * 50 + "\n")

# -----------------------------
# Main Entry Point
# -----------------------------
if __name__ == "__main__":
    vectordb = load_vectorstore()
    interactive_query(vectordb)
