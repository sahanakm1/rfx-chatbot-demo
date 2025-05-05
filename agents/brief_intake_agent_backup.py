import time
from typing import Dict, Tuple, List
from langchain_community.llms import Ollama
from langchain_community.embeddings import OllamaEmbeddings
from langchain_community.vectorstores import Qdrant
from langchain.chains import RetrievalQA
from langchain_core.documents import Document
from langchain_text_splitters import RecursiveCharacterTextSplitter
from prompts.brief_structure import REQUIRED_STRUCTURE


def run_brief_intake(rfx_type: str, user_input: str, uploaded_texts: List[Dict]) -> Tuple[Dict, List[Tuple[str, str]]]:
    print("[STEP] Running brief intake agent")
    start = time.time()

    full_text = "\n\n".join(doc["content"] for doc in uploaded_texts) if uploaded_texts else ""
    if not full_text.strip():
        print("[WARNING] No text provided. Skipping RAG and returning empty brief.")
        return _empty_brief(), list(REQUIRED_STRUCTURE.keys())

    # Step 1: Split text
    print("[STEP] Splitting and preparing text chunks")
    split_start = time.time()
    splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=200)
    chunks = splitter.split_text(full_text)
    print(f"[TIMING] Text splitting took {round(time.time() - split_start, 2)}s")

    # Step 2: Embed & index
    print("[STEP] Creating documents and embeddings")
    embed_start = time.time()
    docs = [Document(page_content=c) for c in chunks]
    embeddings = OllamaEmbeddings(model="mistral")
    vectordb = Qdrant.from_documents(docs, embedding=embeddings, location=":memory:", collection_name="brief_temp")
    retriever = vectordb.as_retriever()
    print(f"[TIMING] Embedding + vectorstore creation took {round(time.time() - embed_start, 2)}s")

    # Step 3: Warm up LLM
    print("[STEP] Warming up LLM")
    llm_start = time.time()
    ollama_model = Ollama(model="mistral")
    qa_chain = RetrievalQA.from_chain_type(llm=ollama_model, retriever=retriever)
    print(f"[TIMING] LLM warm-up took {round(time.time() - llm_start, 2)}s")

    # Step 4: Loop over brief structure
    print("[STEP] Starting section-wise brief generation")
    brief = {}
    missing_sections = []

    for section, subqs in REQUIRED_STRUCTURE.items():
        brief[section] = {}
        for sub, question in subqs.items():
            print(f"[STEP] Processing {section}.{sub}")
            section_prompt = f"Answer the following RFx question as completely and professionally as possible.\n\nQuestion: {question}"
            try:
                result = qa_chain.invoke({"query": section_prompt})

                if isinstance(result, dict):
                    answer = result.get("result")
                else:
                    answer = result

                if not isinstance(answer, str) or len(answer.strip()) < 10:
                    raise ValueError("Answer too short or invalid.")

            except Exception as e:
                print(f"[WARNING] RAG failed for {section}.{sub}: {e}")
                answer = None

            finally:
                brief[section][sub] = {"question": question, "answer": answer}
                if not answer:
                    missing_sections.append((section, sub))
                print(f"[TIMING] {section}.{sub} took {round(time.time() - llm_start, 2)}s")
                llm_start = time.time()

    print(f"[TIMING] Total brief generation took {round(time.time() - start, 2)}s")
    return brief, missing_sections


def _empty_brief() -> Dict:
    brief = {}
    for section, subqs in REQUIRED_STRUCTURE.items():
        brief[section] = {sub: {"question": q, "answer": None} for sub, q in subqs.items()}
    return brief


def update_brief_with_user_response(brief: Dict, section: str, sub: str, content: str) -> Dict:
    if section in brief and sub in brief[section]:
        brief[section][sub]["answer"] = content
    return brief