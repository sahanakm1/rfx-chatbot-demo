import streamlit as st
from pathlib import Path
import fitz
import os
import shutil
import time
from pprint import pprint

from agents.classification_agent import classify_rfx
from agents.rag_classifier import rag_classifier
from agents.brief_intake_agent import brief_intake
from agents.draft_generator import build_doc_from_json
from creating_retriever import universal_retrieval,user_retriever
import orchestrator.orchestrator as oc
from prompts.questions_for_sections import intro, pop_response,pop_schedule,scope

from langchain_community.document_loaders import PyMuPDFLoader
from langchain_core.documents import Document
from langchain_qdrant import QdrantVectorStore
from llm_calling import llm_calling
from langgraph.types import Command, interrupt

RFX_TYPE_LABELS = oc.RFX_TYPE_LABELS

st.set_page_config(page_title="RFx AI Builder Assistant", layout="centered")
st.title("RFx AI Builder Assistant")

# Session state
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []

if "conversation_state" not in st.session_state:
    st.session_state.conversation_state = oc.initialize_state()

# Show chat history
for msg in st.session_state.chat_history:
    st.chat_message(msg["role"]).write(msg["content"])

# Step 0: Greet
if st.session_state.conversation_state["step"] == 0:
    print("prerit 0")
    
    retriever_input = oc.load_universal_retrieval()

    welcome = "Hi! I’m your RFx assistant. How can I help you today?"
    st.chat_message("assistant").write(welcome)
    st.session_state.chat_history.append({"role": "assistant", "content": welcome})
    st.session_state.conversation_state["step"] = 1
    st.session_state.conversation_state["un_retriever"] = retriever_input


# Step 1: Wait for user RFx input
if st.session_state.conversation_state["step"] == 1:
    print("prerit 1")
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
    print("prerit 2")
    print(st.session_state.conversation_state["user_filename"])
    msg = "You can either upload a document or describe it."
    st.chat_message("assistant").write(msg)
    st.session_state.chat_history.append({"role": "assistant", "content": msg})
    
    selection = st.radio("Select an option:", ["Upload a document", "Describe it"], index=None, horizontal=True)
    uploaded_file = None
    user_input = None
    if selection == "Upload a document":
        uploaded_file = st.file_uploader("Upload a supporting RFx Document", type=["pdf", "docx", "txt"])
    elif selection == "Describe it":
        user_input = st.chat_input("Please type what type of RFx you want to build?",disabled=False)

    
    if uploaded_file and user_input is None:
        print("prerit")
        # user_input = "I have uploaded a document."
        # st.chat_message("user").write(user_input)
        # st.session_state.chat_history.append({"role": "user", "content": user_input})
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
        st.chat_message("user").write(user_input)
        st.session_state.chat_history.append({"role": "user", "content": user_input})
        st.session_state.conversation_state["step"] = 4
        add_txt = ""
        st.session_state.conversation_state["add_txt"] = add_txt
        st.session_state.conversation_state["user_input"] = user_input
        st.rerun()


if st.session_state.conversation_state["step"] == 4:
    user_input = st.session_state.conversation_state["user_input"]
    state = st.session_state.conversation_state

    with st.spinner("Classifying Your Request. Please Wait..."):
        result = rag_classifier(chat_context=user_input).classify_with_rag()

    print(result)
    state["rfx_type"] = result
    rfx_type = result
    full_label = RFX_TYPE_LABELS.get(rfx_type, "")

    msg = f"This looks like a **{rfx_type} ({full_label})**. Do you want to proceed?"
    st.chat_message("assistant").write(msg)
    st.session_state.chat_history.append({"role": "assistant", "content": msg})

    st.session_state.conversation_state["step"] = 15

if st.session_state.conversation_state["step"] == 15:

    user_input = st.chat_input("Please type 'yes' to proceed or 'no' to change the RFx type.")
    if user_input is not None: #and user_input.strip().lower() in ["yes","yeah","yep"]:
        st.chat_message("user").write(user_input)
        st.session_state.chat_history.append({"role": "user", "content": user_input})

        print("prerit 15")
        st.session_state.conversation_state["step"] = 6
        st.rerun()




if st.session_state.conversation_state["step"] == 3:
    print("prerit 3")
    state = st.session_state.conversation_state
    
    # msg = "Classifying the document uploaded as RFP/RFI/RFQ. Please Wait........"
    # st.chat_message("assistant").write(msg)
    # st.session_state.chat_history.append({"role": "assistant", "content": msg})
    
    with st.spinner("Classifying the document. Please Wait..."):
        # time.sleep(3)
        # result = {"rfx_type": "RFP"}
        result = classify_rfx(text=state.get("uploaded_text", ""),model_name="mistral:latest").classify_rfx_solve()
        
    
    state["rfx_type"] = result.get("rfx_type")
    rfx_type = result.get("rfx_type")
    full_label = RFX_TYPE_LABELS.get(rfx_type, "")
    
    msg = f"This looks like a **{rfx_type} ({full_label})**. Do you want to proceed?"
    st.chat_message("assistant").write(msg)
    st.session_state.chat_history.append({"role": "assistant", "content": msg})
    
    st.session_state.conversation_state["step"] = 5    

        

if st.session_state.conversation_state["step"] == 5:

    user_input = st.chat_input("Please type 'yes' to proceed or 'no' to change the RFx type.")
    if user_input is not None: #and user_input.strip().lower() in ["yes","yeah","yep"]:
        st.chat_message("user").write(user_input)
        st.session_state.chat_history.append({"role": "user", "content": user_input})

        print("prerit 5")
        with st.spinner("Converting the document into Embeddings and storing it in the DB. Please Wait..."):
        # msg = "Converting the document into Embeddings and storing it in the DB. Please Wait........"
        # st.chat_message("assistant").write(msg)
        # st.session_state.chat_history.append({"role": "assistant", "content": msg})

            content = st.session_state.conversation_state["uploaded_text"]
            file_name = st.session_state.conversation_state["user_filename"]
            
            retriever_user = oc.load_user_retrieval(file_name=file_name,content=content)

            st.session_state.conversation_state["us_retriever"] = retriever_user
        st.session_state.conversation_state["step"] = 6
        st.rerun()

if st.session_state.conversation_state["step"] == 6:
    
    print("prerit 6")
    section = "Introduction"
    st.session_state.conversation_state["section"] = section
    msg = f"""Let's create an RFP. First {section} Section will be created."""
    st.chat_message("assistant").write(msg)
    st.session_state.chat_history.append({"role": "assistant", "content": msg})
    
    retriever_input = st.session_state.conversation_state["un_retriever"]
    retriever_user = st.session_state.conversation_state["us_retriever"]
    add_txt = st.session_state.conversation_state["add_txt"]
    
    question = add_txt + intro.format(section=section)
    
    app = brief_intake(un_retriever=retriever_input,us_retriever=retriever_user,model_name="qwen2.5:7b").run_brief_intake()

    inputs = {
    "question": question
    }
    thread = {"configurable": {"thread_id": "1"}}
    with st.spinner("Generating the Introduction section. Please Wait..."):
        key,value = oc.generate_without_interrupt(inputs, thread, app)
    
    if key == '__interrupt__':
        
        msg = f"""Don't have enough information on {section} section. Please provide more details."""
        st.chat_message("assistant").write(msg) 
        st.session_state.chat_history.append({"role": "assistant", "content": msg})

        
        st.session_state.conversation_state["app"] = app
        st.session_state.conversation_state["thread"] = thread
        st.session_state.conversation_state["step"] = 7
    
    else:
        st.session_state.conversation_state['introduction']=value["generation"]#{"A":value["generation"]}
        st.session_state.conversation_state["step"] = 8


if st.session_state.conversation_state["step"] == 7:
    print("prerit 7")
    app = st.session_state.conversation_state["app"]
    thread = st.session_state.conversation_state["thread"]
    section = st.session_state.conversation_state["section"]
    user_input = st.chat_input("Please provide more details.")

    if user_input is not None:
        st.chat_message("user").write(user_input)
        st.session_state.chat_history.append({"role": "user", "content": user_input})
        with st.spinner(f"""Generating the {section} section. Please Wait..."""):
            value = oc.generate_with_interrupt(user_input=user_input, app=app, thread=thread)


        st.session_state.conversation_state['introduction']=value["generation"]#{"A":value["generation"]}
        st.session_state.conversation_state["step"] = 8
        st.rerun()


if st.session_state.conversation_state["step"] == 8:
    
    print("prerit 8")
    section = "Purpose of the RFP: Response"
    st.session_state.conversation_state["section"] = section

    msg = f"""Creating {section} Section."""
    st.chat_message("assistant").write(msg)
    st.session_state.chat_history.append({"role": "assistant", "content": msg})
    
    retriever_input = st.session_state.conversation_state["un_retriever"]
    retriever_user = st.session_state.conversation_state["us_retriever"]
    add_txt = st.session_state.conversation_state["add_txt"]
    
    question = add_txt + pop_response.format(section=section)
    
    app = brief_intake(un_retriever=retriever_input,us_retriever=retriever_user,model_name="qwen2.5:7b").run_brief_intake()

    inputs = {
    "question": question
    }
    thread = {"configurable": {"thread_id": "1"}}
    with st.spinner(f"""Generating the {section} section. Please Wait..."""):
        key,value = oc.generate_without_interrupt(inputs, thread, app)
    
    if key == '__interrupt__':
        
        msg = f"""Don't have enough information on {section} section. Please provide more details."""
        st.chat_message("assistant").write(msg) 
        st.session_state.chat_history.append({"role": "assistant", "content": msg})

        
        st.session_state.conversation_state["app"] = app
        st.session_state.conversation_state["thread"] = thread
        st.session_state.conversation_state["step"] = 9
    
    else:
        st.session_state.conversation_state['response']=value["generation"]#{"A":value["generation"]}
        st.session_state.conversation_state["step"] = 10


if st.session_state.conversation_state["step"] == 9:
    print("prerit 9")
    app = st.session_state.conversation_state["app"]
    thread = st.session_state.conversation_state["thread"]
    section = st.session_state.conversation_state["section"]
    user_input = st.chat_input("Please provide more details.")

    if user_input is not None:
        st.chat_message("user").write(user_input)
        st.session_state.chat_history.append({"role": "user", "content": user_input})
        
        with st.spinner(f"""Generating the {section} section. Please Wait..."""):
            value = oc.generate_with_interrupt(user_input=user_input, app=app, thread=thread)
            

        st.session_state.conversation_state['response']=value["generation"]#{"A":value["generation"]}
        st.session_state.conversation_state["step"] = 10
        st.rerun()



if st.session_state.conversation_state["step"] == 10:
    
    print("prerit 10")
    section = "Purpose of the RFP: Schedule"
    st.session_state.conversation_state["section"] = section
    msg = f"""Creating {section} Section."""
    st.chat_message("assistant").write(msg)
    st.session_state.chat_history.append({"role": "assistant", "content": msg})
    
    retriever_input = st.session_state.conversation_state["un_retriever"]
    retriever_user = st.session_state.conversation_state["us_retriever"]
    add_txt = st.session_state.conversation_state["add_txt"]
    
    question = add_txt+ pop_schedule.format(section=section)
    
    app = brief_intake(un_retriever=retriever_input,us_retriever=retriever_user,model_name="qwen2.5:7b").run_brief_intake()

    inputs = {
    "question": question
    }
    thread = {"configurable": {"thread_id": "1"}}
    with st.spinner(f"""Generating the {section} section. Please Wait..."""):
        key,value = oc.generate_without_interrupt(inputs, thread, app)
    
    if key == '__interrupt__':
        
        msg = f"""Don't have enough information on {section} section. Please provide more details."""
        st.chat_message("assistant").write(msg) 
        st.session_state.chat_history.append({"role": "assistant", "content": msg})

        
        st.session_state.conversation_state["app"] = app
        st.session_state.conversation_state["thread"] = thread
        st.session_state.conversation_state["step"] = 11
    
    else:
        st.session_state.conversation_state['schedule']=value["generation"]#{"A":value["generation"]}
        st.session_state.conversation_state["step"] = 12
        st.rerun()


if st.session_state.conversation_state["step"] == 11:
    print("prerit 11")
    app = st.session_state.conversation_state["app"]
    thread = st.session_state.conversation_state["thread"]
    section = st.session_state.conversation_state["section"]
    user_input = st.chat_input("Please provide more details.")

    if user_input is not None:
        st.chat_message("user").write(user_input)
        st.session_state.chat_history.append({"role": "user", "content": user_input})
        
        with st.spinner(f"""Generating the {section} section. Please Wait..."""):
            value = oc.generate_with_interrupt(user_input=user_input, app=app, thread=thread)
            

        st.session_state.conversation_state['schedule']=value["generation"]#{"A":value["generation"]}
        st.session_state.conversation_state["step"] = 12
        st.rerun()


if st.session_state.conversation_state["step"] == 12:
    
    print("prerit 12")
    section = "Project Scope"
    st.session_state.conversation_state["section"] = section
    msg = f"""Creating {section} Section."""
    st.chat_message("assistant").write(msg)
    st.session_state.chat_history.append({"role": "assistant", "content": msg})
    
    retriever_input = st.session_state.conversation_state["un_retriever"]
    retriever_user = st.session_state.conversation_state["us_retriever"]
    add_txt = st.session_state.conversation_state["add_txt"]
    
    question = add_txt + scope.format(section=section)
    
    app = brief_intake(un_retriever=retriever_input,us_retriever=retriever_user,model_name="qwen2.5:7b").run_brief_intake()

    inputs = {
    "question": question
    }
    thread = {"configurable": {"thread_id": "1"}}
    
    with st.spinner(f"""Generating the {section} section. Please Wait..."""):
        key,value = oc.generate_without_interrupt(inputs, thread, app)
        
    if key == '__interrupt__':
        
        msg = f"""Don't have enough information on {section} section. Please provide more details."""
        st.chat_message("assistant").write(msg) 
        st.session_state.chat_history.append({"role": "assistant", "content": msg})

        
        st.session_state.conversation_state["app"] = app
        st.session_state.conversation_state["thread"] = thread
        st.session_state.conversation_state["step"] = 13
    
    else:
        st.session_state.conversation_state['scope']=value["generation"]#{"A":value["generation"]}
        st.session_state.conversation_state["step"] = 14
        st.rerun()


if st.session_state.conversation_state["step"] == 13:
    print("prerit 13")
    app = st.session_state.conversation_state["app"]
    thread = st.session_state.conversation_state["thread"]
    section = st.session_state.conversation_state["section"]
    user_input = st.chat_input("Please provide more details.")

    if user_input is not None:
        st.chat_message("user").write(user_input)
        st.session_state.chat_history.append({"role": "user", "content": user_input})

        with st.spinner(f"""Generating the {section} section. Please Wait..."""):
            value = oc.generate_with_interrupt(user_input=user_input, app=app, thread=thread)

        st.session_state.conversation_state['scope']=value["generation"]#{"A":value["generation"]}
        st.session_state.conversation_state["step"] = 14
        st.rerun()

if st.session_state.conversation_state["step"] == 14:
    print("Last Prerit")

    final_doc = {
        "A": {"A.1": st.session_state.conversation_state['introduction']},
        "B": {"B.1": st.session_state.conversation_state['response'], "B.2": st.session_state.conversation_state['schedule']},
        "C": {"C.1": st.session_state.conversation_state['scope']}
    }

    output_path = build_doc_from_json(data_json=final_doc)
    
    with open(output_path, "rb") as file:
        if st.download_button("📄 Download RFx Draft", file, file_name="rfx_draft.docx"):
            st.session_state.conversation_state["step"] = 1
    st.rerun()


    ##Created by Prerit Jain