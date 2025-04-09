import streamlit as st
from agents import category_identifier, rfx_type_decider, document_summarizer, draft_generator
import base64
 
st.set_page_config(page_title="RFx Chatbot", layout="centered")
st.title("RFx Assistant Chatbot")
 
def get_base64(bin_file):
    with open(bin_file, 'rb') as f:
        data = f.read()
    return base64.b64encode(data).decode()
 
 
def set_png_as_page_bg(png_file):
    bin_str = get_base64(png_file)
    page_bg_img = '''
    <style>
    .stApp {
    background-image: url("data:image/png;base64,%s");
    background-size: contain;
    background-repeat: no-repeat;
    background-attachment: scroll; # doesn't work
    }
    </style>
    ''' % bin_str
    st.markdown(page_bg_img, unsafe_allow_html=True)
    return
 
set_png_as_page_bg('./assets/background.png')
 
# Initialize session state
if "step" not in st.session_state:
    st.session_state.step = 0
    st.session_state.category = ""
    st.session_state.rfx_type = ""
    st.session_state.summary = ""
    st.session_state.draft_path = ""
    st.session_state.prompt_loaded = False
    with open("prompts/initial_prompt.txt") as f:
        st.session_state.prompt = f.read()
 
user_input = st.chat_input("Say something...")
 
if user_input:
    st.chat_message("user").write(user_input)
 
    if not st.session_state.prompt_loaded:
        # Silent system prompt load (for future LLM integration)
        st.session_state.prompt_loaded = True
 
    # Step 0: Greet and ask for product category
    if st.session_state.step == 0:
        if user_input.lower() in ["hi", "hello", "hey"]:
            st.chat_message("assistant").write("Hello! I’m here to help you create an RFx document. 😊")
        st.chat_message("assistant").write(category_identifier.ask_for_category())
        st.session_state.step = 1
 
    # Step 1: User provides product category
    elif st.session_state.step == 1:
        st.session_state.category = user_input
        response = category_identifier.use_category(user_input)
        st.chat_message("assistant").write(response)
        st.chat_message("assistant").write("What type of RFx do you need? (RFI, RFQ, or RFP)")
        st.session_state.step = 2
 
    # Step 2: Decide RFx type and summarize documents
    elif st.session_state.step == 2:
        st.session_state.rfx_type = user_input.upper()
        response = rfx_type_decider.decide_rfx_type(user_input)
        st.chat_message("assistant").write(response)
        st.chat_message("assistant").write("Now reading previous documents and generating a summary...")
        st.session_state.summary = document_summarizer.summarize_documents()
        st.chat_message("assistant").write(st.session_state.summary)
        st.session_state.step = 3
 
    # Step 3: Generate and download draft
    elif st.session_state.step == 3:
        st.chat_message("assistant").write("Generating your Word draft...")
        path = draft_generator.create_draft(st.session_state.summary, st.session_state.category, st.session_state.rfx_type)
        st.session_state.draft_path = path
        with open(path, "rb") as file:
            st.download_button("📄 Download RFx Draft", file, file_name="rfx_draft.docx")
        st.session_state.step = 4
