from typing import Dict, Tuple, List
from agents.llm_calling import llm_calling
from agents.retriever_router import create_router
from agents.retrieval_grader import create_retrieval_grader
from agents.question_rewriter import question_rewriter_creator
from langchain.prompts.prompt import PromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langchain_core.documents import Document
from prompts.qna_template import sections_create
from agents.vector_store import vector_store

# Define required structure
REQUIRED_STRUCTURE = {
    "A": ["A.1", "A.2"],
    "B": ["B.1", "B.2", "B.3", "B.4"],
    "C": ["C.1", "C.2", "C.3"],
    "D": ["D.1", "D.2"],
    "E": []
}

def run_brief_intake(rfx_type: str, user_input: str, uploaded_text=None,
                      retriever_input=None, retriever_user=None) -> Tuple[Dict, List[str]]:
    """
    Builds a nested brief structure with upgraded retrieval + grading.
    """
    brief = {}
    missing_sections = []

    llm = llm_calling().call_llm()
    router = create_router(llm)
    grader = create_retrieval_grader(llm)
    rewriter = question_rewriter_creator(llm)

    rag_prompt = PromptTemplate(template=sections_create, input_variables=["question", "context"])
    rag_chain = rag_prompt | llm | StrOutputParser()

    # Normalize uploaded_text
    if isinstance(uploaded_text, list):
        uploaded_text = "\n\n".join([d.page_content for d in uploaded_text])
    elif uploaded_text is None:
        uploaded_text = ""

    for section, subkeys in REQUIRED_STRUCTURE.items():
        if uploaded_text.strip():
            if subkeys:
                brief[section] = {sub: None for sub in subkeys}
            else:
                brief[section] = None
        else:
            if subkeys:
                missing_sections.extend(subkeys)
                brief[section] = {sub: None for sub in subkeys}
            else:
                missing_sections.append(section)
                brief[section] = None

    return brief, missing_sections

def generate_section_from_retrieval(question: str, retriever_input, retriever_user) -> str:
    """
    Rewrites question, routes to correct retriever, filters irrelevant docs, then generates response.
    """
    llm = llm_calling().call_llm()
    router = create_router(llm)
    grader = create_retrieval_grader(llm)
    rewriter = question_rewriter_creator(llm)

    # Rewrite the question
    rewritten_question = rewriter.invoke({"question": question})

    # Route
    route = router.invoke({"question": rewritten_question})
    if route.datasource == "retrieve_universal":
        docs = retriever_input.invoke(rewritten_question)
    else:
        docs = retriever_user.invoke(rewritten_question)

    # Grade
    filtered_docs = []
    for doc in docs:
        score = grader.invoke({"question": rewritten_question, "document": doc.page_content})
        if score.binary_score == "yes":
            filtered_docs.append(doc)

    # Generate
    context = "\n\n".join([doc.page_content for doc in filtered_docs])
    rag_prompt = PromptTemplate(template=sections_create, input_variables=["question", "context"])
    rag_chain = rag_prompt | llm | StrOutputParser()
    response = rag_chain.invoke({"question": rewritten_question, "context": context})
    return response

def update_brief_with_user_response(brief: Dict, section: str, content: str) -> Dict:
    if section in brief:
        brief[section] = content
        return brief

    for top_section, subsections in REQUIRED_STRUCTURE.items():
        if section in subsections:
            if top_section not in brief:
                brief[top_section] = {}
            brief[top_section][section] = content
            return brief

    return brief