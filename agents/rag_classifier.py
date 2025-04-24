from agents.llm_calling import llm_calling
import time
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from prompts.classification_prompt import classification_prompt


class rag_classifier:
    def __init__(self, chat_context=None, model_name: str = "mistral"):
        self.chat_context = chat_context
        #self.log_callback = log_callback
        self.model_name = model_name

    def normalize_rfx_type(self, value: str) -> str:
        val = value.strip().lower()
        if "rfp" in val or "proposal" in val:
            return "RFP"
        elif "rfq" in val or "quotation" in val or "quote" in val:
            return "RFQ"
        elif "rfi" in val or "information" in val:
            return "RFI"
        return "Unknown"


    def classify_with_rag(self) -> str:
        system_prompt = classification_prompt

        llm = llm_calling(model_name=self.model_name).call_llm()
        
        context = self.chat_context

        messages = ChatPromptTemplate.from_messages(
        [
            ("system", system_prompt),
            (
                "human","This is the document: \n\n {context}. \n What type of RFx is this document? \n\n Please classify it as RFP, RFQ, or RFI. \n\n If you are not sure, please say 'Unknown'.",
            ),
        ]
    )

        start = time.time()
        response = messages | llm | StrOutputParser()
        response = response.invoke({"context": context})
        print(f"[TIMING] RAG classification took {time.time() - start:.2f}s")

        result = self.normalize_rfx_type(response)
        return result