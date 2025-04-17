import streamlit as st
from agents.classification_agent import classify_rfx
from agents.brief_intake_agent import run_brief_intake

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
        "uploaded_text": "",
        "output_message": "",
        "logs": [],
        "manual_selected": False
    }

# Sidebar
log_placeholder = None
if st.session_state.conversation_state["step"] >= 2:
    with st.sidebar:
        st.markdown("## 📄 Document Upload (Optional)")
        uploaded_file = st.file_uploader("Upload a supporting RFx Document", type=["pdf", "docx", "txt"])
        if uploaded_file:
            content = uploaded_file.read().decode("utf-8", errors="ignore")
            st.session_state.conversation_state["uploaded_text"] = content
            doc_msg = f"Document '{uploaded_file.name}' uploaded."
            if doc_msg not in st.session_state.conversation_state["logs"]:
                st.session_state.conversation_state["logs"].append(doc_msg)

        st.markdown("## 🧾 RFx Information")
        rfx = st.session_state.conversation_state.get("rfx_type")
        if rfx:
            label = RFX_TYPE_LABELS.get(rfx, "")
            st.success(f"Detected Type: {rfx} ({label})")
        else:
            st.info("No classification yet")

        # One unified log section
        log_placeholder = st.empty()
        if st.session_state.conversation_state["logs"]:
            with log_placeholder:
                st.markdown("## 📚 Processing Log")
                with st.expander("View log steps", expanded=True):
                    for log in st.session_state.conversation_state["logs"]:
                        st.markdown(f"- {log}")

        if st.button("🔁 Reset Chat"):
            st.session_state.chat_history = []
            st.session_state.conversation_state = {
                "step": 0,
                "user_input": "",
                "rfx_type": None,
                "uploaded_text": "",
                "output_message": "",
                "logs": [],
                "manual_selected": False
            }
            st.rerun()

# Show chat history
for msg in st.session_state.chat_history:
    st.chat_message(msg["role"]).write(msg["content"])

# Step 0: Greet
if st.session_state.conversation_state["step"] == 0:
    welcome = "Hi! I’m your RFx assistant. How can I help you today?"
    st.chat_message("assistant").write(welcome)
    st.session_state.chat_history.append({"role": "assistant", "content": welcome})
    st.session_state.conversation_state["step"] = 1

# Step 1: Wait for user RFx input
if st.session_state.conversation_state["step"] == 1:
    user_input = st.chat_input("Please describe your RFx need (e.g. request details or document).")
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

# Step 2: Trigger classification
if st.session_state.conversation_state["step"] == 2:
    if st.button("Start Building RFx"):
        state = st.session_state.conversation_state
        state["logs"] = []

        def update_sidebar_log(msg):
            if msg not in state["logs"]:
                state["logs"].append(msg)
                if log_placeholder:
                    with log_placeholder:
                        st.markdown("## 📚 Processing Log")
                        with st.expander("View log steps", expanded=True):
                            for log in state["logs"]:
                                st.markdown(f"- {log}")

        with st.spinner("🔎 Classifying your request..."):
            result = classify_rfx(
                text=state.get("uploaded_text", ""),
                user_input=state.get("user_input", ""),
                log_callback=update_sidebar_log
            )

        state["rfx_type"] = result.get("rfx_type")
        state["logs"] = result.get("logs", [])
        rfx_type = result.get("rfx_type")
        full_label = RFX_TYPE_LABELS.get(rfx_type, "")
        msg = f"This looks like a **{rfx_type} ({full_label})**. Do you want to proceed?"

        st.chat_message("assistant").write(msg)
        st.session_state.chat_history.append({"role": "assistant", "content": msg})
        st.session_state.conversation_state["step"] = 3

# Step 3: Ask for confirmation
if st.session_state.conversation_state["step"] == 3:
    rfx_type = st.session_state.conversation_state.get("rfx_type")
    if rfx_type:
        col1, col2 = st.columns(2)
        with col1:
            if st.button("✅ Yes, proceed"):
                msg = run_brief_intake(
                    rfx_type,
                    st.session_state.conversation_state.get("user_input", ""),
                    st.session_state.conversation_state.get("uploaded_text", "")
                )
                st.chat_message("assistant").write(msg)
                st.session_state.chat_history.append({"role": "assistant", "content": msg})
        with col2:
            if st.button("❌ No, change type"):
                st.session_state.conversation_state["step"] = 4

# Step 4: Manual type select (one-time)
if st.session_state.conversation_state["step"] == 4 and not st.session_state.conversation_state.get("manual_selected"):
    st.chat_message("assistant").write("What type of RFx would you like to proceed with?")
    col1, col2, col3 = st.columns(3)
    selected = None
    if col1.button("📄 Request for Proposal"):
        selected = "RFP"
    elif col2.button("💰 Request for Quotation"):
        selected = "RFQ"
    elif col3.button("📚 Request for Information"):
        selected = "RFI"

    if selected:
        st.session_state.conversation_state["rfx_type"] = selected
        st.session_state.conversation_state["manual_selected"] = True

        msg = run_brief_intake(
            selected,
            st.session_state.conversation_state.get("user_input", ""),
            st.session_state.conversation_state.get("uploaded_text", "")
        )

        st.chat_message("assistant").write(f"You selected {selected}. {msg}")
        st.session_state.chat_history.append({
            "role": "assistant",
            "content": f"User selected {selected}. {msg}"
        })

        st.rerun()