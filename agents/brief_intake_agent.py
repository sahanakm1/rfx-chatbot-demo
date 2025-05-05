import time
from typing import List, Dict, Tuple
from langchain_core.documents import Document
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_community.vectorstores import Qdrant
from langchain.chains import RetrievalQA
from langchain_ollama import OllamaEmbeddings, OllamaLLM
from prompts.brief_structure import REQUIRED_STRUCTURE


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
            splitter = RecursiveCharacterTextSplitter.from_tiktoken_encoder(chunk_size=500, chunk_overlap=50)
            chunks = splitter.split_text(all_text)
            log_callback(f"[TIMING] Text splitting took {round((time.time() - start)/60, 2)} min")

            log_callback("[STEP] Creating documents and embeddings")
            start = time.time()
            docs = [Document(page_content=c) for c in chunks]
            embeddings = OllamaEmbeddings(model="mistral")
            vectordb = Qdrant.from_documents(docs, embedding=embeddings, location=":memory:", collection_name="brief_temp")
            retriever = vectordb.as_retriever()
            retriever.search_kwargs["k"] = 5
            log_callback(f"[TIMING] Embedding + vectorstore creation took {round((time.time() - start)/60, 2)} min")

            log_callback("[STEP] Warming up LLM")
            start = time.time()
            llm = OllamaLLM(model="mistral")
            qa_chain = RetrievalQA.from_chain_type(llm=llm, retriever=retriever)
            log_callback(f"[TIMING] LLM warm-up took {round((time.time() - start)/60, 2)} min")

        except Exception as e:
            log_callback(f"[WARNING] Document processing failed, skipping RAG: {e}")
            qa_chain = None
    else:
        log_callback("[INFO] No uploaded documents. Skipping RAG.")
        disclaimer_msg = "Since no supporting documents were uploaded, I'll ask a few questions to help fill in the brief."

    log_callback("[STEP] Starting section-wise brief generation")
    for section_key, sub_dict in REQUIRED_STRUCTURE.items():
        brief[section_key] = {}
        for sub_key, sub_content in sub_dict.items():
            question = sub_content["question"]
            title = sub_content["title"]

            answer = "N/A"
            if qa_chain:
                prompt = f"""You are helping prepare a response to a {rfx_type}. Based on the content in the provided documents, answer the following:

{question}

If no answer is found, just return 'N/A'.
"""
                log_callback(f"[STEP] Processing {section_key}.{sub_key}")
                start = time.time()
                try:
                    docs = qa_chain.retriever.get_relevant_documents(prompt)
                    log_callback(f"[DEBUG] Top docs for {section_key}.{sub_key}:\n{docs[:2]}")
                    answer = qa_chain.invoke({"query": prompt})
                except Exception as e:
                    log_callback(f"[WARNING] RAG failed for {section_key}.{sub_key}: {e}")
                log_callback(f"[TIMING] {section_key}.{sub_key} took {round((time.time() - start)/60, 2)} min")

            brief[section_key][sub_key] = {
                "title": title,
                "question": question,
                "answer": answer.strip() if isinstance(answer, str) else "N/A"
            }

            if brief[section_key][sub_key]["answer"].lower() in ["", "n/a", "na"]:
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

def update_brief_with_user_response(state, user_input: str):
    section = state["pending_question"]["section"]
    sub = state["pending_question"]["sub"]

    # Update the brief with the user's answer
    state["brief"][section][sub]["answer"] = user_input.strip() if user_input.strip() else "N/A"

    # Remove the answered question from missing_sections
    state["missing_sections"] = [
        pair for pair in state["missing_sections"] if pair != (section, sub)
    ]

    # If more questions remain, queue the next one
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
