# create_universal_vectorstore.py

from creating_retriever import file_names, langchain_doc_creation, vector_store
from agents.llm_calling import llm_calling

# 📁 Step 1: Location of reference PDFs
DOC_DIR = "./data/rfx_reference_docs/"
COLLECTION_NAME = "jti_rfp_dense"
PATH = "./tmp/langchain_qdrant_dense"

# 📄 Step 2: Load and preprocess PDFs into LangChain Documents
print("🔍 Loading reference documents...")
file_paths = file_names(DOC_DIR)
if not file_paths:
    raise FileNotFoundError(f"No PDFs found in {DOC_DIR}")
docs = langchain_doc_creation(file_paths)

# 🧠 Step 3: Load embedding model
print("🧠 Creating embedding model (llama3)...")
embed_model = llm_calling(embedding_model="llama3").call_embed_model()

# 🗃️ Step 4: Create vector store in Qdrant
print("📦 Creating Qdrant vector store...")
vs = vector_store(
    collection_name=COLLECTION_NAME,
    embeddings=embed_model,
    path=PATH
).vector_qdrant_dense(force_recreate=True)

vs.add_documents(docs)
print("✅ Universal vector store created successfully!")