import time
from typing import List, Dict, Tuple
from langchain_core.documents import Document
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_community.vectorstores import Qdrant
from langchain.chains import RetrievalQA
from langchain_ollama import OllamaEmbeddings, OllamaLLM
from langchain_huggingface import HuggingFaceEmbeddings

from prompts.brief_structure import REQUIRED_STRUCTURE

retrieval_context = {
    "retriever": None,
    "qa_chain": None
}

def run_brief_intake(rfx_type: str, user_input: str, uploaded_texts: List[Dict[str, str]] = None, log_callback=None) -> Tuple[Dict, List[Tuple[str, str]], str]:
    if log_callback is None:
        log_callback = print

    log_callback("[STEP] Running brief intake agent")
    start_total = time.time()

    brief = {}
    missing_sections = []
    disclaimer_msg = None

    qa_chain = None
    if uploaded_texts:
        try:
            all_text = "\n\n".join([doc["content"] for doc in uploaded_texts])
            log_callback("[STEP] Splitting and preparing text chunks")
            start = time.time()
            splitter = RecursiveCharacterTextSplitter.from_tiktoken_encoder(chunk_size=1000, chunk_overlap=50)
            chunks = splitter.split_text(all_text)
            log_callback(f"[TIMING] Text splitting took {round((time.time() - start)/60, 2)} min")

            log_callback("[STEP] Creating documents and embeddings")
            start = time.time()
            docs = [Document(page_content=c) for c in chunks]

            log_callback(f"[DEBUG] Number of chunks: {len(docs)}")

            #embeddings = OllamaEmbeddings(model="nomic-embed-text")
            embeddings = HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2")
            
            vectordb = Qdrant.from_documents(docs, embedding=embeddings, location=":memory:", collection_name="brief_temp")
            retriever = vectordb.as_retriever()
            retriever.search_kwargs["k"] = 2

            log_callback(f"[TIMING] Embedding + vectorstore creation took {round((time.time() - start)/60, 2)} min")

            log_callback("[STEP] Warming up LLM")
            start = time.time()
            llm = OllamaLLM(model="mistral")
            qa_chain = RetrievalQA.from_chain_type(llm=llm, retriever=retriever, chain_type="stuff")

            retrieval_context["retriever"] = retriever
            retrieval_context["qa_chain"] = qa_chain

            log_callback(f"[TIMING] LLM warm-up took {round((time.time() - start)/60, 2)} min")

        except Exception as e:
            log_callback(f"[WARNING] Document processing failed, skipping RAG: {e}")
            qa_chain = None
    else:
        log_callback("[INFO] No uploaded documents. Skipping RAG.")
        disclaimer_msg = "Since no supporting documents were uploaded, I'll ask a few questions to help fill in the brief."

    
    # Build all sections without answering yet
    log_callback("[STEP] Initializing brief structure without QA")
    for section_key, sub_dict in REQUIRED_STRUCTURE.items():
        brief[section_key] = {}
        for sub_key, sub_content in sub_dict.items():
            question = sub_content["question"]
            title = sub_content["title"]

            # Leave answer empty for now, and mark as missing
            brief[section_key][sub_key] = {
                "title": title,
                "question": question,
                "answer": ""
            }
            missing_sections.append((section_key, sub_key))
    
    
    # Add final geography question
    final_section = "Z"
    final_sub = "Z.1"
    final_question = "I see you are based in Spain. Is this the expected geography for this engagement?"
    brief[final_section] = {
        final_sub: {
            "title": "Engagement Geography",
            "question": final_question,
            "answer": ""
        }
    }
    missing_sections.append((final_section, final_sub))

    log_callback(f"[TIMING] Total brief generation took {round((time.time() - start_total)/60, 2)} min")

    return brief, missing_sections, disclaimer_msg

def try_auto_answer(state: Dict) -> str:
    """Tries to auto-answer the pending question using RAG. Returns the next question or final message."""
    pending = state.get("pending_question")
    if not pending:
        return ""

    section = pending["section"]
    sub = pending["sub"]
    question = state["brief"][section][sub]["question"]

    if retrieval_context["qa_chain"]:
        try:
            answer = retrieval_context["qa_chain"].invoke({"query": f"""
                                                                You are a procurement analyst expert in preparing RFx documents.

                                                                Your task is to answer the following question using only the content retrieved from the provided documents.

                                                                If the documents do not contain enough information to answer with confidence, or if you are uncertain, respond with exactly: 'N/A'.

                                                                Do not make assumptions. Do not answer based on prior knowledge.

                                                                Question:
                                                                {question}

                                                            """})
            if isinstance(answer, str):
                answer = answer.strip()
            elif isinstance(answer, dict):
                answer = answer.get("result", "").strip()
            else:
                answer = str(answer).strip()

            if "N/A" in answer:
                state["brief"][section][sub]["answer"] = "N/A"
            else:
                state["brief"][section][sub]["answer"] = answer
            
        except Exception as e:
            state["brief"][section][sub]["answer"] = "N/A"
            state["logs"].append(f"Retrieval failed for {section}.{sub}: {e}")
    else:
        state["brief"][section][sub]["answer"] = "N/A"

    
    if state["brief"][section][sub]["answer"] != "N/A":
        # Avanzar
        state["missing_sections"] = [pair for pair in state["missing_sections"] if pair != (section, sub)]
        state["pending_question"] = None

        if state["missing_sections"]:
            next_section, next_sub = state["missing_sections"][0]
            next_question = state["brief"][next_section][next_sub]["question"]
            state["pending_question"] = {
                "section": next_section,
                "sub": next_sub,
                "question": next_question,
            }
        return state["brief"][section][sub]["answer"]

    return "N/A"

def update_brief_with_user_response(state, user_input: str):
    section = state["pending_question"]["section"]
    sub = state["pending_question"]["sub"]

    if user_input.strip():
        state["brief"][section][sub]["answer"] = user_input.strip()
    else:
        state["brief"][section][sub]["answer"] = "N/A"

    state["missing_sections"] = [pair for pair in state["missing_sections"] if pair != (section, sub)]
    state["pending_question"] = None

    if state["missing_sections"]:
        next_section, next_sub = state["missing_sections"][0]
        next_question = state["brief"][next_section][next_sub]["question"]
        state["pending_question"] = {
            "section": next_section,
            "sub": next_sub,
            "question": next_question,
        }
        return next_question
    else:
        state["pending_question"] = None
        return "Thanks! All required inputs have been collected."
