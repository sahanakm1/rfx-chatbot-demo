import streamlit as st
from agents.rfx_graph import rfx_graph

# Page setup
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
        "uploaded_text": "",
        "output_message": "",
        "logs": []
    }

# Display chat history
for msg in st.session_state.chat_history:
    st.chat_message(msg["role"]).write(msg["content"])

# Step 0: Show greeting
if st.session_state.conversation_state["step"] == 0:
    welcome = "Hi! I’m your RFx assistant. How can I help you"
    st.chat_message("assistant").write(welcome)
    st.session_state.chat_history.append({"role": "assistant", "content": welcome})
    st.session_state.conversation_state["step"] = 1

# Step 1: Wait for meaningful input
if st.session_state.conversation_state["step"] == 1:
    user_input = st.chat_input("What would you like help with today?")
    if user_input:
        st.chat_message("user").write(user_input)
        st.session_state.chat_history.append({"role": "user", "content": user_input})
        
        if user_input.strip().lower() in ["hi", "hello", "hey"]:
            st.chat_message("assistant").write("Hi there! Could you describe what you're looking to build today?")
            st.session_state.chat_history.append({"role": "assistant", "content": "Please describe your RFx need (e.g. request details or document)."})
        else:
            st.session_state.conversation_state["user_input"] = user_input
            st.session_state.conversation_state["logs"].append("Received user input.")
            st.session_state.conversation_state["step"] = 2

# Step 2: Optional document upload + trigger classification
if st.session_state.conversation_state["step"] == 2:
    uploaded_file = st.file_uploader("Upload an RFx Document (optional)", type=["pdf", "docx", "txt"])
    if uploaded_file is not None:
        content = uploaded_file.read().decode("utf-8", errors="ignore")
        st.session_state.conversation_state["uploaded_text"] = content
        st.session_state.conversation_state["logs"].append(f"Document '{uploaded_file.name}' uploaded.")

    if st.button("Start Building RFx"):
        state = st.session_state.conversation_state

        with st.spinner("🔎 Classifying request type..."):
            result = rfx_graph.invoke(state)

        response = result.get("output_message", "Something went wrong.")
        st.chat_message("assistant").write(response)
        st.session_state.chat_history.append({"role": "assistant", "content": response})

        if "logs" in result:
            with st.expander("🔍 See classification steps"):
                for log in result["logs"]:
                    st.markdown(f"- {log}")

        st.session_state.conversation_state.update(result)
        st.session_state.conversation_state["step"] = 3


# Step 3: Ask for classification confirmation
if st.session_state.conversation_state["step"] == 3:
    rfx_type = st.session_state.conversation_state.get("rfx_type")
    if rfx_type:
        st.chat_message("assistant").write(f"This looks like a {rfx_type}. Is that correct?")
        col1, col2 = st.columns(2)
        with col1:
            if st.button("Yes, proceed"):
                from agents.brief_intake_agent import run_brief_intake
                msg = run_brief_intake(
                    rfx_type,
                    st.session_state.conversation_state.get("user_input", ""),
                    st.session_state.conversation_state.get("uploaded_text", "")
                )
                st.chat_message("assistant").write(msg)
                st.session_state.chat_history.append({"role": "assistant", "content": msg})
        with col2:
            if st.button("No, let me choose"):
                st.session_state.conversation_state["step"] = 4

# Step 4: Let user select RFP/RFQ/RFI manually
if st.session_state.conversation_state["step"] == 4:
    from agents.brief_intake_agent import run_brief_intake
    st.chat_message("assistant").write("What type of RFx would you like to proceed with?")
    col1, col2, col3 = st.columns(3)
    selected = None
    if col1.button("RFP"):
        selected = "RFP"
    elif col2.button("RFQ"):
        selected = "RFQ"
    elif col3.button("RFI"):
        selected = "RFI"

    if selected:
        st.session_state.conversation_state["rfx_type"] = selected
        msg = run_brief_intake(
            selected,
            st.session_state.conversation_state.get("user_input", ""),
            st.session_state.conversation_state.get("uploaded_text", "")
        )
        st.chat_message("assistant").write(f"You selected {selected}. {msg}")
        st.session_state.chat_history.append({"role": "assistant", "content": f"User selected {selected}. {msg}"})