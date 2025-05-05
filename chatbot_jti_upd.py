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
import prompts.sample_questions_rfp_rfi_rfq as sq

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


state = st.session_state.conversation_state

# Step 0: Greet
if state["step"] == 0:
    print("prerit 0")
    
    retriever_input = oc.load_universal_retrieval()

    welcome = "Hi! I’m your RFx assistant. How can I help you today?"
    st.chat_message("assistant").write(welcome)
    st.session_state.chat_history.append({"role": "assistant", "content": welcome})
    state["un_retriever"] = retriever_input
    state["step"] = 1
    


# Step 1: Wait for user RFx input
if state["step"] == 1:
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
            state["user_input"] = user_input
            state["step"] = 2
            #st.rerun()


if state["step"] == 2:
    print("prerit 2")

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
        
        file_name = uploaded_file.name.split(".")[0]
        file_name = file_name.replace(" ","_")
        
        state["user_filename"] = file_name
        
        with fitz.open(stream=uploaded_file.read(), filetype="pdf") as doc:
            text = []
            text = [Document(page_content=page.get_text()) for page in doc]
        content = text

        state["uploaded_text"] = content
        print(file_name)
        
        add_txt = "From the uploaded document, "
        state["add_txt"] = add_txt
        state["step"] = 3    

    if uploaded_file is None and user_input is not None:
        st.chat_message("user").write(user_input)
        st.session_state.chat_history.append({"role": "user", "content": user_input})
        
        add_txt = ""
        state["add_txt"] = add_txt
        state["user_input"] = user_input
        state["step"] = 4
        st.rerun()


if state["step"] == 3:
    print("prerit 3")
    
    with st.spinner("Classifying the document. Please Wait..."):
        result = classify_rfx(text=state.get("uploaded_text", ""),model_name="mistral:latest").classify_rfx_solve()
        
    state["rfx_type"] = result.get("rfx_type")
    rfx_type = result.get("rfx_type")
    full_label = RFX_TYPE_LABELS.get(rfx_type, "")
    
    msg = f"This looks like a **{rfx_type} ({full_label})**. Do you want to proceed?"
    st.chat_message("assistant").write(msg)
    st.session_state.chat_history.append({"role": "assistant", "content": msg})
    
    state["step"] = 15



if state["step"] == 4:
    user_input = state["user_input"]
    
    with st.spinner("Classifying Your Request into RFP/RFQ/RFI. Please Wait..."):
        result = rag_classifier(chat_context=user_input).classify_with_rag()

    print(result)
    state["rfx_type"] = result
    rfx_type = result
    full_label = RFX_TYPE_LABELS.get(rfx_type, "")

    msg = f"This looks like a **{rfx_type} ({full_label})** request. Do you want to proceed?"
    st.chat_message("assistant").write(msg)
    st.session_state.chat_history.append({"role": "assistant", "content": msg})

    state["step"] = 15


if state["step"] == 15:

    user_input = st.chat_input("Please type 'yes' to proceed or 'no' to change the RFx type.")
    content = state["uploaded_text"]
    file_name = state["user_filename"]


    if user_input is not None and user_input.lower() in ["yes","yeah","yep"]: #and user_input.strip().lower() in ["yes","yeah","yep"]:
        st.chat_message("user").write(user_input)
        st.session_state.chat_history.append({"role": "user", "content": user_input})

        print("prerit 15_1")

        if content is not None:
            retriever_user = oc.load_user_retrieval(file_name=file_name,content=content)
            state["us_retriever"] = retriever_user


        state["step"] = 6

    if user_input is not None and user_input.lower() in ["no","nope","nay"]: #and user_input.strip().lower() in ["yes","yeah","yep"]:
        st.chat_message("user").write(user_input)
        st.session_state.chat_history.append({"role": "user", "content": user_input})

        print("prerit 15_2")
        state["step"] = 16
        #st.rerun()

if state["step"] == 16:
    st.chat_message("assistant").write("What type of RFx would you like to proceed with?")
    col1, col2, col3 = st.columns(3)
    selected = None
    
    if col1.button("📄 Request for Proposal", key="button_1"):
        selected = "RFP"
    elif col2.button("💰 Request for Quotation", key="button_2"):
        selected = "RFQ"
    elif col3.button("📚 Request for Information", key="button_3"):
        selected = "RFI"

    
    if selected:
        state["rfx_type"] = selected
        
        st.chat_message("assistant").write(f"You selected {selected}")
        st.session_state.chat_history.append({
            "role": "assistant",
            "content": f"User selected {selected}. {msg}"
        })
    
        content = state["uploaded_text"]
        file_name = state["user_filename"]

        if content is not None:
            retriever_user = oc.load_user_retrieval(file_name=file_name,content=content)
            state["us_retriever"] = retriever_user
            state["step"] = 6
            st.rerun()


if state["step"] == 6:
    
    print("prerit 6")
    
    rfx_type = state["rfx_type"]
    
    msg = f"""Let's create an {rfx_type}."""
    st.chat_message("assistant").write(msg)
    st.session_state.chat_history.append({"role": "assistant", "content": msg})
    
    retriever_input = state["un_retriever"]
    retriever_user = state["us_retriever"]
    add_txt = state["add_txt"]
    

    if rfx_type == "RFP":
        question = add_txt + sq.RFP["A"]["A.1"]
        state["question"] = sq.RFP["A"]["A.1"]
    elif rfx_type == "RFI":
        question = add_txt + sq.RFI["A"]["A.1"]
        state["question"] = sq.RFI["A"]["A.1"]
    else:
        question = add_txt + sq.RFQ["A"]["A.1"]
        state["question"] = sq.RFQ["A"]["A.1"]

    print(question)

    st.chat_message("assistant").write(f"""Generating response to the question: {state["question"]} 
                                       Proceed to generate the response or skip this question?""")
    col1, col2 = st.columns(2)
    selected = None
    if col1.button("📄 Generate", key="button_4"):
        selected = "Generate"
    elif col2.button("⏭️ Skip", key="button_5"):
        selected = "Skip"
    
    if selected == "Skip":
        state["step"] = 8
        st.rerun()
    
    elif selected == "Generate":

        app = brief_intake(un_retriever=retriever_input,us_retriever=retriever_user,model_name="qwen2.5:7b").run_brief_intake()

        inputs = {
        "question": question
        }
        thread = {"configurable": {"thread_id": "1"}}
        with st.spinner(f"""Generating the response to the question: '{state["question"]}'. Please Wait..."""):
            key,value = oc.generate_without_interrupt(inputs, thread, app)
    
        if key == '__interrupt__':
            
            msg = f"""Don't have enough information on the question: '{state["question"]}'. Please provide more details."""
            st.chat_message("assistant").write(msg) 
            st.session_state.chat_history.append({"role": "assistant", "content": msg})
            
            state["app"] = app
            state["thread"] = thread
            state["step"] = 7
            st.rerun()
        
        else:
            state['a.1']=value["generation"]#{"A":value["generation"]}
            state["step"] = 8


if st.session_state.conversation_state["step"] == 7:
    print("prerit 7")
    app = state["app"]
    thread = state["thread"]
    #section = state["section"]
    question = state["question"]
    user_input = st.chat_input("Please provide more details.")

    if user_input is not None:
        st.chat_message("user").write(user_input)
        st.session_state.chat_history.append({"role": "user", "content": user_input})
        with st.spinner(f"""Generating the content for the question. Please Wait..."""):
            value = oc.generate_with_interrupt(user_input=user_input, app=app, thread=thread)


        state['a.1']=value["generation"]#{"A":value["generation"]}
        state["step"] = 8
        st.rerun()



if state["step"] == 8:
    
    print("prerit 8")

    rfx_type = state["rfx_type"]
    add_txt = state["add_txt"]
    retriever_input = state["un_retriever"]
    retriever_user = state["us_retriever"]

    if rfx_type == "RFP":
        question = add_txt + sq.RFP["A"]["A.2"]
        state["question"] = sq.RFP["A"]["A.2"]
    elif rfx_type == "RFI":
        question = add_txt + sq.RFI["A"]["A.2"]
        state["question"] = sq.RFI["A"]["A.2"]
    else:
        question = add_txt + sq.RFQ["A"]["A.2"]
        state["question"] = sq.RFQ["A"]["A.2"]

    msg = f"""Generating response for the question: '{state["question"]} 
    Proceed to generate the response or skip this question?'"""
    st.chat_message("assistant").write(msg)
    st.session_state.chat_history.append({"role": "assistant", "content": msg})
    
    col1, col2 = st.columns(2)
    selected = None
    if col1.button("📄 Generate", key="button_6"):
        selected = "Generate"
    elif col2.button("⏭️ Skip", key="button_7"):
        selected = "Skip"
    
    if selected == "Skip":
        state["step"] = 10
        st.rerun()

    elif selected == "Generate":
        app = brief_intake(un_retriever=retriever_input,us_retriever=retriever_user,model_name="qwen2.5:7b").run_brief_intake()

        inputs = {
        "question": question
        }
        
        thread = {"configurable": {"thread_id": "1"}}
        with st.spinner(f"""Generating the response to the question: '{state["question"]}'. Please Wait..."""):
            key,value = oc.generate_without_interrupt(inputs, thread, app)
        
        if key == '__interrupt__':
            
            msg = f"""Don't have enough information on the question. Please provide more details."""
            st.chat_message("assistant").write(msg) 
            st.session_state.chat_history.append({"role": "assistant", "content": msg})

            
            state["app"] = app
            state["thread"] = thread
            state["step"] = 9
        
        else:
            state['a.2']=value["generation"]#{"A":value["generation"]}
            state["step"] = 10


if st.session_state.conversation_state["step"] == 9:
    print("prerit 9")
    app = state["app"]
    thread = state["thread"]
    question = state["question"]
    user_input = st.chat_input("Please provide more details.")

    if user_input is not None:
        st.chat_message("user").write(user_input)
        st.session_state.chat_history.append({"role": "user", "content": user_input})
        
        with st.spinner(f"""Generating the response to the question. Please Wait..."""):
            value = oc.generate_with_interrupt(user_input=user_input, app=app, thread=thread)
            

        state['response']=value["generation"]#{"A":value["generation"]}
        state["step"] = 10
        st.rerun()



if st.session_state.conversation_state["step"] == 10:
    
    print("prerit 10")

    rfx_type = state["rfx_type"]
    retriever_input = state["un_retriever"]
    retriever_user = state["us_retriever"]
    add_txt = state["add_txt"]
    
    if rfx_type == "RFP":
        question = add_txt + sq.RFP["B"]["B.1"]
        state["question"] = sq.RFP["B"]["B.1"]
    elif rfx_type == "RFI":
        question = add_txt + sq.RFI["B"]["B.1"]
        state["question"] = sq.RFI["B"]["B.1"]
    else:
        question = add_txt + sq.RFQ["B"]["B.1"]
        state["question"] = sq.RFQ["B"]["B.1"]


    msg = f"""Generating response for the question: '{state["question"]}'
    Proceed to generate the response or skip this question?"""
    st.chat_message("assistant").write(msg)
    st.session_state.chat_history.append({"role": "assistant", "content": msg})
    
    col1, col2 = st.columns(2)
    selected = None
    if col1.button("📄 Generate", key="button_8"):
        selected = "Generate"
    elif col2.button("⏭️ Skip", key="button_9"):
        selected = "Skip"
    
    if selected == "Skip":
        state["step"] = 12
        st.rerun()

    elif selected=="Generate":


        app = brief_intake(un_retriever=retriever_input,us_retriever=retriever_user,model_name="qwen2.5:7b").run_brief_intake()

        inputs = {
        "question": question
        }
        thread = {"configurable": {"thread_id": "1"}}
        with st.spinner(f"""Generating the response to the question. Please Wait..."""):
            key,value = oc.generate_without_interrupt(inputs, thread, app)
        
        if key == '__interrupt__':
            
            msg = f"""Don't have enough information on the previous question. Please provide more details."""
            st.chat_message("assistant").write(msg) 
            st.session_state.chat_history.append({"role": "assistant", "content": msg})

            
            state["app"] = app
            state["thread"] = thread
            state["step"] = 11
            st.rerun()
        
        else:
            state['b.1']=value["generation"]#{"A":value["generation"]}
            state["step"] = 12
        


if st.session_state.conversation_state["step"] == 11:
    print("prerit 11")
    app = state["app"]
    thread = state["thread"]
    question = state["question"]
    user_input = st.chat_input("Please provide more details.")

    if user_input is not None:
        st.chat_message("user").write(user_input)
        st.session_state.chat_history.append({"role": "user", "content": user_input})
        
        with st.spinner(f"""Generating the response to the question. Please Wait..."""):
            value = oc.generate_with_interrupt(user_input=user_input, app=app, thread=thread)
            

        state['b.1']=value["generation"]#{"A":value["generation"]}
        state["step"] = 12
        st.rerun()


if st.session_state.conversation_state["step"] == 12:
    
    print("prerit 12")

    rfx_type = state["rfx_type"]
    retriever_input = state["un_retriever"]
    retriever_user = state["us_retriever"]
    add_txt = state["add_txt"]
    
    if rfx_type == "RFP":
        question = add_txt + sq.RFP["B"]["B.2"]
        state["question"] = sq.RFP["B"]["B.2"]
    elif rfx_type == "RFI":
        question = add_txt + sq.RFI["B"]["B.2"]
        state["question"] = sq.RFI["B"]["B.2"]
    else:
        question = add_txt + sq.RFQ["B"]["B.2"]
        state["question"] = sq.RFQ["B"]["B.2"]


    msg = f"""Generating response for the question: '{state["question"]}'
    Proceed to generate the response or skip this question?"""
    st.chat_message("assistant").write(msg)
    st.session_state.chat_history.append({"role": "assistant", "content": msg})
    
    col1, col2 = st.columns(2)
    selected = None
    if col1.button("📄 Generate", key="button_10"):
        selected = "Generate"
    elif col2.button("⏭️ Skip", key="button_11"):
        selected = "Skip"
    
    if selected == "Skip":
        state["step"] = 17
        st.rerun()

    elif selected=="Generate":


        app = brief_intake(un_retriever=retriever_input,us_retriever=retriever_user,model_name="qwen2.5:7b").run_brief_intake()

        inputs = {
        "question": question
        }
        thread = {"configurable": {"thread_id": "1"}}
        with st.spinner(f"""Generating the response to the question. Please Wait..."""):
            key,value = oc.generate_without_interrupt(inputs, thread, app)
        
        if key == '__interrupt__':
            
            msg = f"""Don't have enough information on the previous question. Please provide more details."""
            st.chat_message("assistant").write(msg) 
            st.session_state.chat_history.append({"role": "assistant", "content": msg})

            
            state["app"] = app
            state["thread"] = thread
            state["step"] = 13
            st.rerun()
        
        else:
            state['b.2']=value["generation"]#{"A":value["generation"]}
            state["step"] = 17
        


if st.session_state.conversation_state["step"] == 13:
    print("prerit 13")
    app = state["app"]
    thread = state["thread"]
    question = state["question"]
    user_input = st.chat_input("Please provide more details.")

    if user_input is not None:
        st.chat_message("user").write(user_input)
        st.session_state.chat_history.append({"role": "user", "content": user_input})
        
        with st.spinner(f"""Generating the response to the question. Please Wait..."""):
            value = oc.generate_with_interrupt(user_input=user_input, app=app, thread=thread)
            

        state['b.2']=value["generation"]#{"A":value["generation"]}
        state["step"] = 17
        st.rerun()


if st.session_state.conversation_state["step"] == 17:
    
    print("prerit 17")

    rfx_type = state["rfx_type"]
    retriever_input = state["un_retriever"]
    retriever_user = state["us_retriever"]
    add_txt = state["add_txt"]
    
    if rfx_type == "RFP":
        question = add_txt + sq.RFP["C"]["C.1"]
        state["question"] = sq.RFP["C"]["C.1"]
    elif rfx_type == "RFI":
        question = add_txt + sq.RFI["C"]["C.1"]
        state["question"] = sq.RFI["C"]["C.1"]
    else:
        question = add_txt + sq.RFQ["C"]["C.1"]
        state["question"] = sq.RFQ["C"]["C.1"]


    msg = f"""Generating response for the question: '{state["question"]}'
    Proceed to generate the response or skip this question?"""
    st.chat_message("assistant").write(msg)
    st.session_state.chat_history.append({"role": "assistant", "content": msg})
    
    col1, col2 = st.columns(2)
    selected = None
    if col1.button("📄 Generate", key="button_12"):
        selected = "Generate"
    elif col2.button("⏭️ Skip", key="button_13"):
        selected = "Skip"
    
    if selected == "Skip":
        state["step"] = 19
        st.rerun()

    elif selected=="Generate":


        app = brief_intake(un_retriever=retriever_input,us_retriever=retriever_user,model_name="qwen2.5:7b").run_brief_intake()

        inputs = {
        "question": question
        }
        thread = {"configurable": {"thread_id": "1"}}
        with st.spinner(f"""Generating the response to the question. Please Wait..."""):
            key,value = oc.generate_without_interrupt(inputs, thread, app)
        
        if key == '__interrupt__':
            
            msg = f"""Don't have enough information on the previous question. Please provide more details."""
            st.chat_message("assistant").write(msg) 
            st.session_state.chat_history.append({"role": "assistant", "content": msg})

            
            state["app"] = app
            state["thread"] = thread
            state["step"] = 18
            st.rerun()
        
        else:
            state['c.1']=value["generation"]#{"A":value["generation"]}
            state["step"] = 19
        


if st.session_state.conversation_state["step"] == 18:
    print("prerit 18")
    app = state["app"]
    thread = state["thread"]
    question = state["question"]
    user_input = st.chat_input("Please provide more details.")

    if user_input is not None:
        st.chat_message("user").write(user_input)
        st.session_state.chat_history.append({"role": "user", "content": user_input})
        
        with st.spinner(f"""Generating the response to the question. Please Wait..."""):
            value = oc.generate_with_interrupt(user_input=user_input, app=app, thread=thread)
            

        state['c.1']=value["generation"]#{"A":value["generation"]}
        state["step"] = 19
        st.rerun()


if st.session_state.conversation_state["step"] == 19:
    
    print("prerit 19")

    rfx_type = state["rfx_type"]
    retriever_input = state["un_retriever"]
    retriever_user = state["us_retriever"]
    add_txt = state["add_txt"]
    
    if rfx_type == "RFP":
        question = add_txt + sq.RFP["C"]["C.2"]
        state["question"] = sq.RFP["C"]["C.2"]
    elif rfx_type == "RFI":
        question = add_txt + sq.RFI["C"]["C.2"]
        state["question"] = sq.RFI["C"]["C.2"]
    else:
        question = add_txt + sq.RFQ["C"]["C.2"]
        state["question"] = sq.RFQ["C"]["C.2"]


    msg = f"""Generating response for the question: '{state["question"]}'
    Proceed to generate the response or skip this question?"""
    st.chat_message("assistant").write(msg)
    st.session_state.chat_history.append({"role": "assistant", "content": msg})
    
    col1, col2 = st.columns(2)
    selected = None
    if col1.button("📄 Generate", key="button_14"):
        selected = "Generate"
    elif col2.button("⏭️ Skip", key="button_15"):
        selected = "Skip"
    
    if selected == "Skip":
        state["step"] = 21
        st.rerun()

    elif selected=="Generate":


        app = brief_intake(un_retriever=retriever_input,us_retriever=retriever_user,model_name="qwen2.5:7b").run_brief_intake()

        inputs = {
        "question": question
        }
        thread = {"configurable": {"thread_id": "1"}}
        with st.spinner(f"""Generating the response to the question. Please Wait..."""):
            key,value = oc.generate_without_interrupt(inputs, thread, app)
        
        if key == '__interrupt__':
            
            msg = f"""Don't have enough information on the previous question. Please provide more details."""
            st.chat_message("assistant").write(msg) 
            st.session_state.chat_history.append({"role": "assistant", "content": msg})

            
            state["app"] = app
            state["thread"] = thread
            state["step"] = 20
            st.rerun()
        
        else:
            state['c.2']=value["generation"]#{"A":value["generation"]}
            state["step"] = 21
        


if st.session_state.conversation_state["step"] == 20:
    print("prerit 18")
    app = state["app"]
    thread = state["thread"]
    question = state["question"]
    user_input = st.chat_input("Please provide more details.")

    if user_input is not None:
        st.chat_message("user").write(user_input)
        st.session_state.chat_history.append({"role": "user", "content": user_input})
        
        with st.spinner(f"""Generating the response to the question. Please Wait..."""):
            value = oc.generate_with_interrupt(user_input=user_input, app=app, thread=thread)
            

        state['c.2']=value["generation"]#{"A":value["generation"]}
        state["step"] = 21
        st.rerun()



if st.session_state.conversation_state["step"] == 21:
    print("Last Prerit")

    rfx_type = state["rfx_type"]

    if (state["a.1"]!="") | (state["a.2"]!="") | (state["b.1"]!="") | (state["b.2"]!="") | (state["c.1"]!="") | (state["c.2"]!="") :

        final_doc = {
            "A": {"A.1": state['a.1'], "A.2": state['a.2']},
            "B": {"B.1": state['b.1'], "B.2": state['b.2']},
            "C": {"C.1": state['c.1'], "C.2": state['c.2']}
        }

        output_path = build_doc_from_json(data_json=final_doc)
    
        with open(output_path, "rb") as file:
            if st.download_button("📄 Download RFx Draft", file, file_name=f"""{rfx_type}_draft.docx"""):
                st.session_state.conversation_state["step"] = 1
                st.rerun()
    
    else:
        msg = f"""There is no information available for me to create {rfx_type}. Please provide more information"""
        st.chat_message("assistant").write(msg)
        st.session_state.chat_history.append({"role": "user", "content": msg})
        state["step"] = 1
        st.rerun()
    
    


#    ##Created by Prerit Jain