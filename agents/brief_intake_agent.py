
# brief_intake_agent.py
import hashlib
import time
from typing import List, Dict, Tuple
from concurrent.futures import ThreadPoolExecutor, as_completed

from langchain_community.vectorstores import Qdrant
from langchain.chains import RetrievalQA

from agents.vector_store import get_cached_vector_store
from agents.llm_calling import llm_calling

from prompts.brief_structure import REQUIRED_STRUCTURE

# Global context for reusing retriever and QA chain across calls
retrieval_context = {
    "retriever": None,
    "qa_chain": None
}

# Main entry point: generates the initial brief structure and optionally prepares a QA system
def run_brief_intake(
    rfx_type: str, 
    user_input: str, 
    uploaded_texts: List[Dict[str, str]] = None, 
    log_callback=None, 
    doc_name="TEMP", 
    collection_name=""
) -> Tuple[Dict, List[Tuple[str, str]], str]:

    if log_callback is None:
        log_callback = print

    log_callback("[STEP] Running brief intake agent")
    start_total = time.time()

    brief = {}
    missing_sections = []
    disclaimer_msg = None
    qa_chain = None

    # Try to initialize the retriever and QA system using the uploaded documents
    if uploaded_texts:
        print("uploaded_texts")
        try:
            start = time.time()
#            embed_model = llm_calling(model_name="mistral").call_embed_model()
            embed_model = llm_calling().call_embed_model()
            vectordb = get_cached_vector_store(
                collection_name=collection_name, 
                embeddings=embed_model, 
                ensure_exists=False
            )
            print("vector db")

            retriever = vectordb.as_retriever()
            retriever.search_kwargs["k"] = 5

            log_callback(f"[TIMING] Embedding + vectorstore creation took {round((time.time() - start)/60, 2)} min")

            log_callback("[STEP] Warming up LLM")
            start = time.time()

            # Calling gpt model
            llm = llm_calling().call_llm()
            qa_chain = RetrievalQA.from_chain_type(llm=llm, retriever=retriever, chain_type="stuff")
            print("qa_chain")

            retrieval_context["retriever"] = retriever
            retrieval_context["qa_chain"] = qa_chain

            log_callback(f"[TIMING] LLM warm-up took {round((time.time() - start)/60, 2)} min")

        except Exception as e:
            log_callback(f"[WARNING] Document processing failed, skipping RAG: {e}")
            qa_chain = None
    else:
        log_callback("[INFO] No uploaded documents. Skipping RAG.")
        disclaimer_msg = "Since no supporting documents were uploaded, I'll ask a few questions to help fill in the brief."

    # Initialize the full brief structure with unanswered fields
    log_callback("[STEP] Initializing brief structure without QA")
    for section_key, sub_dict in REQUIRED_STRUCTURE.items():
        brief[section_key] = {}
        for sub_key, sub_content in sub_dict.items():
            question = sub_content["question"]
            title = sub_content["title"]

            brief[section_key][sub_key] = {
                "title": title,
                "question": question,
                "answer": "N/A",
                "asked": False
            }
            missing_sections.append((section_key, sub_key))

    # initialize pending question
    pending_question = {}
    if missing_sections:
            next_section, next_sub = missing_sections[0]
            next_question = brief[next_section][next_sub]["question"]
            pending_question = {
                "section": next_section,
                "sub": next_sub,
                "question": next_question,
                "asked": False,
            }

    # Add final geography-related question
    final_section = "Z"
    final_sub = "Z.1"
    final_question = "I see you are based in Spain. Is this the expected geography for this engagement?"
    brief[final_section] = {
        final_sub: {
            "title": "Engagement Geography",
            "question": final_question,
            "answer": "N/A"
        }
    }
    missing_sections.append((final_section, final_sub))

    log_callback(f"[TIMING] Total brief generation took {round((time.time() - start_total)/60, 2)} min")

    return brief, missing_sections, pending_question, disclaimer_msg

# Attempt to answer a pending question using RAG (retriever + LLM)
def try_auto_answer(state: Dict) -> str:
    """Tries to auto-answer the pending question using RAG. Returns the next question or final message."""
    pending = state.get("pending_question")
    if not pending:
        return ""
    
    if state.get("uploaded_texts") and retrieval_context["qa_chain"] is None:
        # if there is not retrieval, for example in the case of some new documents are uploaded
        print("\n\n----> run_brief_intake ")
        print(state.get("uploaded_texts", []))
        print("\n\n----> run_brief_intake ")
        run_brief_intake(
            rfx_type=state.get("rfx_type"),
            user_input="",
            uploaded_texts=state.get("uploaded_texts", []),
            doc_name=state.get("doc_name", "TEMP"),
            collection_name=state.get("collection_name", "")
        )

    section = pending["section"]
    sub = pending["sub"]
    question = state["brief"][section][sub]["question"]

    if retrieval_context["qa_chain"]:
        try:
            print("\t\t---brief node--- trying auto-answer via RAG ---- answering")
            answer = retrieval_context["qa_chain"].invoke({"query": f"""
                You are a procurement analyst expert in preparing {state["rfx_type"]} documents.
                Your task is to answer the following question using the content retrieved from the provided documents.
                If the documents do not contain enough information to answer with confidence, or if you are uncertain, respond with exactly: 'N/A'.
                
                Question:
                {question}
                Make sure to answer 'N/A' in case there is not relevant information in the answer.
                Avoid to do references to the document, just elaborate the answer as best you can.
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

            print("\t\t---brief node--- trying auto-answer via RAG ---- answering: "+ answer[:100])

        except Exception as e:
            state["brief"][section][sub]["answer"] = "N/A"
            state["logs"].append(f"Retrieval failed for {section}.{sub}: {e}")
    else:
        state["brief"][section][sub]["answer"] = "N/A"

    # Progress to next question if applicable
    if state["brief"][section][sub]["answer"] != "N/A":
    
        state["missing_sections"] = [pair for pair in state["missing_sections"] if pair != (section, sub)]
        state["pending_question"] = None

        if state["missing_sections"]:
            next_section, next_sub = state["missing_sections"][0]
            next_question = state["brief"][next_section][next_sub]["question"]
            state["pending_question"] = {
                "section": next_section,
                "sub": next_sub,
                "question": next_question,
                "asked": False,
            }
        return state["brief"][section][sub]["answer"]
    

    return "N/A"


# Update the brief with the user's manual input
def update_brief_with_user_response(state, user_input: str):
    pending = state.get("pending_question")
    if not pending:
        return "No question was pending."

    section = pending.get("section")
    sub = pending.get("sub")

    if not section or not sub:
        return "Missing section/subsection in pending question."

    # Guarda la respuesta del usuario
    state["brief"][section][sub]["answer"] = user_input.strip() if user_input.strip() else "N/A"
    state["brief"][section][sub]["asked"] = True

    # Elimina esa sección del listado de secciones pendientes
    state["missing_sections"] = [pair for pair in state["missing_sections"] if pair != (section, sub)]
    state["pending_question"] = None

    # Si aún quedan preguntas, prepara la siguiente
    if state["missing_sections"]:
        next_section, next_sub = state["missing_sections"][0]
        next_question = state["brief"][next_section][next_sub]["question"]
        state["pending_question"] = {
            "section": next_section,
            "sub": next_sub,
            "question": next_question,
            "asked": False,
        }
        return next_question
    else:
        state["pending_question"] = None
        return ""



def try_auto_answer_batch(state: Dict, batch: List[Tuple[str, str]], max_workers: int = 5) -> Tuple[Dict[Tuple[str, str], str], List[Tuple[str, str]]]:
    """
    Tries to answer a batch of brief questions in parallel using threading.
    Prints retrieved chunks and uses them explicitly for answering.
    Returns a dict of resolved answers and a list of unresolved section/subsection pairs.
    """
    resolved = {}
    unresolved = []

    retriever = retrieval_context.get("retriever")
    if not retriever:
        if state.get("uploaded_texts") and retrieval_context["qa_chain"] is None:
            # if there is not retrieval, for example in the case of some new documents are uploaded
            print("\n\n----> run_brief_intake ")
            print(state.get("uploaded_texts", []))
            print("\n\n----> run_brief_intake ")
            run_brief_intake(
                rfx_type=state.get("rfx_type"),
                user_input="",
                uploaded_texts=state.get("uploaded_texts", []),
                doc_name=state.get("doc_name", "TEMP"),
                collection_name=state.get("collection_name", "")
            )
            retriever = retrieval_context.get("retriever")
        else:
            return resolved, batch

    def process_section(section, sub):
        question = state["brief"][section][sub]["question"]
        try:
            # Paso 1: Recuperar documentos
            retrieved_docs = retriever.get_relevant_documents(question)
            retrieved_text = "\n\n".join(doc.page_content for doc in retrieved_docs)

            # Paso 2: Imprimir los chunks recuperados
            #print(f"\n[Retrieved for {section} - {sub}]\n{retrieved_text}\n")

            # Paso 3: Llamar al modelo con los documentos recuperados
            llm = llm_calling().call_llm()
            prompt = f"""
                    You are a procurement analyst expert in preparing {state["rfx_type"]} documents.
                    Your task is to answer the following question using only the content provided below.
                    If the content does not contain enough information to answer with confidence, or if you are uncertain, respond with exactly: 'N/A'.
                    Do not make assumptions. Do not answer based on prior knowledge.

                    Context:
                    {retrieved_text}

                    Question:
                    {question}
                    """
            response = llm.invoke(prompt)
            
            if hasattr(response, "content"):
                answer = response.content.strip()                
            else:
                answer = str(response).strip()

            return (section, sub, answer)
        except Exception as e:
            print(f"Error processing {section} - {sub}: {e}")
            return (section, sub, "N/A")

    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        futures = {
            executor.submit(process_section, section, sub): (section, sub)
            for section, sub in batch
        }

        for future in as_completed(futures):
            section, sub, answer = future.result()
            if "N/A" in answer:
                unresolved.append((section, sub))
            else:
                resolved[(section, sub)] = answer
                state["brief"][section][sub]["answer"] = answer

    return resolved, unresolved