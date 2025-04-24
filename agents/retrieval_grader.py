from llm_calling import llm_calling
from prompts.retrieval_grade_prompt import retrieval_grade_prompt

from pydantic import BaseModel, Field
from typing import Literal, List

from langchain_core.prompts import ChatPromptTemplate

class GradeDocuments(BaseModel):
    """Binary score for relevance check on retrieved documents."""

    binary_score: str = Field(
        description="Documents are relevant to the question, 'yes' or 'no'"
    )


def create_retrieval_grader(llm):
    # LLM with function call
    structured_llm_grader = llm.with_structured_output(GradeDocuments)

    # Prompt
    system = retrieval_grade_prompt
    grade_prompt = ChatPromptTemplate.from_messages(
        [
            ("system", system),
            ("human", "Retrieved document: \n\n {document} \n\n User question: {question}"),
        ]
    )

    retrieval_grader = grade_prompt | structured_llm_grader
    return retrieval_grader