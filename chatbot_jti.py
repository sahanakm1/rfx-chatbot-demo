import streamlit as st
from pathlib import Path
import fitz
import os
import shutil

from agents.classification_agent import classify_rfx
from agents.brief_intake_agent import run_brief_intake
from creating_retriever import universal_retrieval,user_retriever


from langchain_community.document_loaders import PyMuPDFLoader
from langchain_core.documents import Document
from langchain_qdrant import QdrantVectorStore
from llm_calling import llm_calling


RFX_TYPE_LABELS = {
    "RFP": "Request for Proposal",
    "RFQ": "Request for Quotation",
    "RFI": "Request for Information"
}

st.set_page_config(page_title="RFx AI Builder Assistant", layout="centered")
st.title("RFx AI Builder Assistant")

# Session state
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []

if "conversation_state" not in st.session_state:
    st.session_state.conversation_state = {
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

    }

# Show chat history
for msg in st.session_state.chat_history:
    st.chat_message(msg["role"]).write(msg["content"])

# Step 0: Greet
if st.session_state.conversation_state["step"] == 0:
    embeddings = llm_calling(embedding_model="llama3.2:latest").call_embed_model()

    ## Universal Retrieval
    type_of_retrieval = "dense" #@param ["dense", "sparse", "hybrid"]
    collection_name = f"""jti_rfp_{type_of_retrieval}"""
    path = f"""./tmp/langchain_qdrant_{type_of_retrieval}"""
    my_file = Path(path+f"""/collection/{collection_name}/storage.sqlite""")
    #directory = "./Input_Files"

    if my_file.is_file():
        print("DB Exists")
        retriever_input = universal_retrieval(collection_name=collection_name,embeddings=embeddings,path=path).load_existing_vdb_collection()
    else:
        print("DB does not exist")

    ## Universal Retrieval Ends

    welcome = "Hi! I’m your RFx assistant. How can I help you today?"
    st.chat_message("assistant").write(welcome)
    st.session_state.chat_history.append({"role": "assistant", "content": welcome})
    st.session_state.conversation_state["step"] = 1
    st.session_state.conversation_state["un_retriever"] = retriever_input

# Step 1: Wait for user RFx input
if st.session_state.conversation_state["step"] == 1:
    #user_input = st.chat_input("Please describe your RFx need (e.g. request details or document).")
    user_input = st.chat_input("Please ask your questions")
    if user_input:
        st.chat_message("user").write(user_input)
        st.session_state.chat_history.append({"role": "user", "content": user_input})

        if user_input.strip().lower() in ["hi", "hello", "hey"]:
            msg = "Hi! Could you please describe what you're looking to build?"
            st.chat_message("assistant").write(msg)
            st.session_state.chat_history.append({"role": "assistant", "content": msg})
        else:
            st.session_state.conversation_state["user_input"] = user_input
            st.session_state.conversation_state["step"] = 2
            st.rerun()


if st.session_state.conversation_state["step"] == 2:
    print(st.session_state.conversation_state["user_filename"])
    msg = "You can either upload a document or describe it."
    st.chat_message("assistant").write(msg)
    st.session_state.chat_history.append({"role": "assistant", "content": msg})
    
    uploaded_file = st.file_uploader("Upload a supporting RFx Document", type=["pdf", "docx", "txt"])
    user_input = st.chat_input("Please type what type of RFx you want to build?")

    
    if uploaded_file and user_input is None:
        print("prerit")
        file_name = uploaded_file.name.split(".")[0]
        file_name = file_name.replace(" ","_")
        st.session_state.conversation_state["user_filename"] = file_name
        with fitz.open(stream=uploaded_file.read(), filetype="pdf") as doc:
            text = []
            text = [Document(page_content=page.get_text()) for page in doc]
        content = text

        st.session_state.conversation_state["uploaded_text"] = content
        print(file_name)
        st.session_state.conversation_state["step"] = 3    
        add_txt = "From the uploaded document, "
        st.session_state.conversation_state["add_txt"] = add_txt

    if uploaded_file is None and user_input is not None:
        st.session_state.conversation_state["user_input"] = user_input
        st.session_state.chat_history.append({"role": "user", "content": user_input})
        st.session_state.conversation_state["step"] = 4
        add_txt = ""

        st.session_state.conversation_state["add_txt"] = add_txt


if st.session_state.conversation_state["step"] == 3:
    state = st.session_state.conversation_state
    
    msg = "Classifying the document uploaded as RFP/RFI/RFQ. Please Wait........"
    st.chat_message("assistant").write(msg)
    st.session_state.chat_history.append({"role": "assistant", "content": msg})
    
    result = classify_rfx(text=state.get("uploaded_text", ""),model_name="qwen2.5:7b").classify_rfx_solve()
    
    state["rfx_type"] = result.get("rfx_type")
    rfx_type = result.get("rfx_type")
    full_label = RFX_TYPE_LABELS.get(rfx_type, "")
    
    msg = f"This looks like a **{rfx_type} ({full_label})**. Do you want to proceed?"
    st.chat_message("assistant").write(msg)
    st.session_state.chat_history.append({"role": "assistant", "content": msg})
    
    user_input = st.chat_input("Please type 'yes' to proceed or 'no' to change the RFx type.")
    
    if user_input and user_input.strip().lower() in ["yes","yeah","yep"]:
        st.chat_message("user").write(user_input)
        st.session_state.chat_history.append({"role": "user", "content": user_input})
        st.session_state.conversation_state["step"] = 5

        

if st.session_state.conversation_state["step"] == 5:
    

    msg = "Converting the document into Embeddings and storing it in the DB. Please Wait........"
    st.chat_message("assistant").write(msg)
    st.session_state.chat_history.append({"role": "assistant", "content": msg})

    content = st.session_state.conversation_state["uploaded_text"]
    file_name = st.session_state.conversation_state["user_filename"]
    
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

    st.session_state.conversation_state["us_retriever"] = retriever_user
    st.session_state.conversation_state["step"] = 6