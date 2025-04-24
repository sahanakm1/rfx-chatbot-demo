from llm_calling import llm_calling


from prompts.qna_template import sections_create
from prompts.intro_gen_prompt import intro_gen_prompt

from agents.retriever_router import create_router
from agents.retrieval_grader import create_retrieval_grader
from agents.question_rewriter import question_rewriter_creator

from pydantic import BaseModel, Field
from typing import Literal, List

from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate
from langchain.prompts.prompt import PromptTemplate
from typing_extensions import TypedDict
from langchain.schema import Document
from langgraph.graph import END, StateGraph, START
from langgraph.types import Command, interrupt
from langgraph.checkpoint.memory import MemorySaver
from langchain_core.runnables.graph import CurveStyle, MermaidDrawMethod, NodeStyles

from pprint import pprint
from IPython.display import Image, display

def format_docs(docs):
    return "\n\n".join(doc.page_content for doc in docs)


class brief_intake():
    def __init__(self, un_retriever = None, us_retriever = None,model_name = "qwen2.5:7b"):
        self.un_retriever = un_retriever
        self.us_retriever = us_retriever
        self.model_name = model_name
        #self.question = question


    def run_brief_intake(self):

        retriever_input = self.un_retriever
        retriever_user = self.us_retriever
        #question = self.question

        llm = llm_calling(model_name=self.model_name).call_llm()

        question_router = create_router(llm=llm)
        retrieval_grader = create_retrieval_grader(llm=llm)
        question_rewriter = question_rewriter_creator(llm=llm)

        prompt=PromptTemplate(template=sections_create, input_variables=['question','context'])
# Chain
        rag_chain = prompt | llm | StrOutputParser()


        class GraphState(TypedDict):
            """
            Represents the state of our graph.

            Attributes:
                question: question
                generation: LLM generation
                documents: list of documents
            """

            question: str
            generation: str
            documents: List[str]


        def retrieve_universal(state):
            """
            Retrieve documents

            Args:
                state (dict): The current graph state

            Returns:
                state (dict): New key added to state, documents, that contains retrieved documents
            """
            print("---RETRIEVE UNIVERSAL---")
            question = state["question"]

            # Retrieval
            documents = retriever_input.invoke(question)
            return {"documents": documents, "question": question}

        def retrieve_user(state):
            """
            Retrieve documents

            Args:
                state (dict): The current graph state

            Returns:
                state (dict): New key added to state, documents, that contains retrieved documents
            """
            print("---RETRIEVE USER---")
            question = state["question"]

            # Retrieval
            documents = retriever_user.invoke(question)
            return {"documents": documents, "question": question}

        def generate(state):
            """
            Generate answer

            Args:
                state (dict): The current graph state

            Returns:
                state (dict): New key added to state, generation, that contains LLM generation
            """
            print("---GENERATE---")
            question = state["question"]
            documents = state["documents"]

            # RAG generation
            generation = rag_chain.invoke({"context": documents, "question": question})
            return {"documents": documents, "question": question, "generation": generation}


        def grade_documents(state):
            """
            Determines whether the retrieved documents are relevant to the question.

            Args:
                state (dict): The current graph state

            Returns:
                state (dict): Updates documents key with only filtered relevant documents
            """

            print("---CHECK DOCUMENT RELEVANCE TO QUESTION---")
            question = state["question"]
            documents = state["documents"]

            # Score each doc
            filtered_docs = []
            for d in documents:
                score = retrieval_grader.invoke(
                    {"question": question, "document": d.page_content}
                )
                grade = score.binary_score
                if grade == "yes":
                    print("---GRADE: DOCUMENT RELEVANT---")
                    filtered_docs.append(d)
                else:
                    print("---GRADE: DOCUMENT NOT RELEVANT---")
                    continue
            return {"documents": filtered_docs, "question": question}

        def transform_query(state):
            """
            Transform the query to produce a better question.

            Args:
                state (dict): The current graph state

            Returns:
                state (dict): Updates question key with a re-phrased question
            """

            print("---TRANSFORM QUERY---")
            question = state["question"]
            #documents = state["documents"]

            # Re-write question
            better_question = question_rewriter.invoke({"question": question})
            return {"question": better_question}


        def route_question(state):
            """
            Route question to web search or RAG.

            Args:
                state (dict): The current graph state

            Returns:
                str: Next node to call
            """

            print("---ROUTE QUESTION---")
            question = state["question"]
            source = question_router.invoke({"question": question})
            if source.datasource == "retrieve_universal":
                print("---ROUTE QUESTION TO UNIVERSAL VECTORSTORE---")
                return "retrieve_universal"
            elif source.datasource == "retrieve_user":
                print("---ROUTE QUESTION TO USER VECTORSTORE---")
                return "retrieve_user"


        def decide_to_generate(state):
            """
            Determines whether to generate an answer, or re-generate a question.

            Args:
                state (dict): The current graph state

            Returns:
                str: Binary decision for next node to call
            """

            print("---ASSESS GRADED DOCUMENTS---")
            state["question"]
            filtered_documents = state["documents"]

            if not filtered_documents:
                # All documents have been filtered check_relevance
                # We will re-generate a new query
                print(
                    "---DECISION: ALL DOCUMENTS ARE NOT RELEVANT TO QUESTION, TRANSFORM QUERY---"
                )
                return "human_interrupt"
            else:
                # We have relevant documents, so generate answer
                print("---DECISION: GENERATE---")
                return "generate"
    

        def human_interrupt(state):
            """
            Human interruption node."""

            print("---NEED HUMAN INPUT---")
            print("Question: "+state["question"])
            interrupt_text = f"""Please provide RELEVANT documents supporting the {state['question']} question:"""
            feedback = interrupt(interrupt_text)
            
            return {"documents": feedback}


        workflow = StateGraph(GraphState)

# Define the nodes
        workflow.add_node("retrieve_universal", retrieve_universal)  # web search
        workflow.add_node("retrieve_user", retrieve_user)  # retrieve
        workflow.add_node("grade_documents", grade_documents)  # grade documents
        workflow.add_node("generate", generate)  # generatae
        workflow.add_node("transform_query", transform_query)  # transform_query
        workflow.add_node("human_interrupt", human_interrupt)  # transform_query

        # Build graph
        workflow.add_edge(START, "transform_query")  # route question
        workflow.add_conditional_edges(
            "transform_query",
            route_question,
            {
                "retrieve_universal":"retrieve_universal",
                "retrieve_user":"retrieve_user",
            },
        )
        workflow.add_edge("retrieve_universal", "grade_documents")
        workflow.add_edge("retrieve_user", "grade_documents")
        workflow.add_conditional_edges(
            "grade_documents",
            decide_to_generate,
            {
                "human_interrupt": "human_interrupt",
                "generate": "generate",
            },
        )
        workflow.add_edge("human_interrupt", "generate")

        memory = MemorySaver()

        # Compile
        app = workflow.compile(checkpointer=memory)

        return app

        # Run
        # inputs = {
        #     "question": question
        # }
        # thread = {"configurable": {"thread_id": "1"}}
        # for output in app.stream(inputs,thread):
        #     for key, value in output.items():
        #         pprint(f"Node '{key}':")
        #     pprint("\n---\n")

        # return value["generation"]

