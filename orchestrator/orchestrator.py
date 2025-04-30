#import streamlit as st
from pathlib import Path

from llm_calling import llm_calling
from creating_retriever import universal_retrieval,user_retriever

from langgraph.types import Command, interrupt
from pprint import pprint


RFX_TYPE_LABELS = {
    "RFP": "Request for Proposal",
    "RFQ": "Request for Quotation",
    "RFI": "Request for Information"
}


def initialize_state():
    return {
        "step": 0,
        "user_input": "",
        "rfx_type": None,
        "uploaded_text": None,
        "output_message": "",
        "logs": [],
        "manual_selected": False,
        "un_retriever": None,
        "us_retriever": None,
        "add_txt":"",
        "user_filename":"",
        "introduction":"",
        "response":"",
        "schedule":"",
        "scope":"",
        "thread": None,
        "section":""
    }


def load_universal_retrieval(type_of_retrieval="dense"):

    embeddings = llm_calling(embedding_model="llama3.2:latest").call_embed_model()
    collection_name = f"""jti_rfp_{type_of_retrieval}"""
    path = f"""./tmp/langchain_qdrant_{type_of_retrieval}"""
    my_file = Path(path+f"""/collection/{collection_name}/storage.sqlite""")

    if my_file.is_file():
        print("DB Exists")
        retriever_input = universal_retrieval(collection_name=collection_name,embeddings=embeddings,path=path).load_existing_vdb_collection()
        return retriever_input
    else:
        print("DB does not exist")




def load_user_retrieval(type_of_retrieval="dense",file_name="",content=""):
    type_of_retrieval = "dense" #@param ["dense", "sparse", "hybrid"]
    collection_name = file_name
    path = f"""./tmp/langchain_qdrant_user_{type_of_retrieval}"""
    my_file = Path(path+f"""/collection/{collection_name}/storage.sqlite""")

    embeddings = llm_calling(embedding_model="llama3.2:latest").call_embed_model()


    if my_file.is_file():
        print("DB Exists")
        retriever_user = universal_retrieval(collection_name=collection_name,embeddings=embeddings,path=path).load_existing_vdb_collection()
    else:
        print("DB does not exist")
        retriever_user = user_retriever(collection_name=collection_name,embeddings=embeddings,path=path,doc_input=content,type_of_retrieval=type_of_retrieval).create_new_vdb()

    return retriever_user



def generate_without_interrupt(inputs, thread, app):
    for output in app.stream(inputs,thread):
        for key, value in output.items():
            # Node
            #print("prerit")
            pprint(f"Node '{key}':")
            # Optional: print full state at each node
            # pprint.pprint(value["keys"], indent=2, width=80, depth=None)
        #pprint("\n---\n")

    return key,value



def generate_with_interrupt(user_input, thread, app):
    for output in app.stream(Command(resume=user_input),thread, stream_mode="updates"):
        for key, value in output.items():
            # Node
            pprint(f"Node '{key}':")
            # Optional: print full state at each node
            # pprint.pprint(value["keys"], indent=2, width=80, depth=None)
        pprint("\n---\n")

    return value