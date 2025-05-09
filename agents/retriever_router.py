from agents.llm_calling import llm_calling
from prompts.router_prompt import router_prompt

from pydantic import BaseModel, Field
from typing import Literal, List

from langchain_core.prompts import ChatPromptTemplate



    

class RouteQuery(BaseModel):
    """Route a user query to the most relevant datasource."""

    datasource: Literal["retrieve_universal", "retrieve_user"] = Field(
        ...,
        description="There are two vectorstores. Given a user question choose to route it to the vectorstore for Input Files or a vectorstore for User Files.",
    )


def create_router(llm):
    # Initialize the LLM and router prompt
    #llm = llm_calling(model_name=model_name).call_llm()
    structured_llm_router = llm.with_structured_output(RouteQuery)
    system = router_prompt
    route_prompt = ChatPromptTemplate.from_messages(
        [
            ("system", system),
            ("human", "{question}"),
        ]
    )

    question_router = route_prompt | structured_llm_router
    return question_router