# agents/classification_agent.py
from agents.embedding_utils import split_text
from agents.vector_store import vector_store
from agents.rag_classifier import rag_classifier
from agents.intent_classifier import classify_by_intent
from agents.llm_calling import llm_calling
from langchain_core.documents import Document
import hashlib

class classify_rfx:
    def __init__(self, text, model_name: str = "mistral",log_callback=None):
        self.text = text
        self.log_callback = log_callback
        self.model_name = model_name

    
    _doc_cache = {}

    def classify_rfx_solve(self):
        log_msgs = []

        def log(msg):
            if msg not in log_msgs:
                log_msgs.append(msg)
                if self.log_callback and "[TIMING]" not in msg:
                    clean_msg = msg.replace("[INFO]", "").replace("[STEP]", "").strip()
                    self.log_callback(clean_msg)

        if self.text is None:
            log("[INFO] No user input or document provided. Skipping classification.")
            return {"rfx_type": "Unknown", "logs": log_msgs}

        rfx_type = rag_classifier(self.text, model_name=self.model_name).classify_with_rag()
        return {"rfx_type": rfx_type}