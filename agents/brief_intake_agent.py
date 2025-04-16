# agents/brief_intake_agent.py

import streamlit as st

# Load initial prompt text to guide Q&A
with open("prompts/initial_prompt.txt", "r") as f:
    INITIAL_GUIDANCE = f.read()

def process_document_intake(file_obj, rfx_type):
    """
    Process the uploaded document:
    - Extract fields using RAG
    - Detect missing fields
    - Trigger adaptive Q&A for missing info
    - Return final structured brief
    """
    extracted_fields = extract_fields_with_rag(file_obj, rfx_type)
    structured_brief = run_adaptive_qa(extracted_fields, rfx_type)
    return structured_brief

def process_chat_intake(user_text, rfx_type):
    """
    Process no-document flow:
    - Load reference content
    - Use Q&A to gather required data
    - Return structured brief
    """
    base_fields = load_reference_template(rfx_type)
    structured_brief = run_adaptive_qa(base_fields, rfx_type)
    return structured_brief

def run_adaptive_qa(initial_fields, rfx_type):
    """
    Adaptive Q&A based on missing fields using the general prompt guidance.
    """
    final_brief = initial_fields.copy()
    st.chat_message("assistant").write("I'll ask a few questions to complete your RFx based on the type: {}.".format(rfx_type))
    st.chat_message("assistant").write("Guidance for responses:\n" + INITIAL_GUIDANCE)

    for field in ["background", "objectives", "scope", "timeline", "budget", "evaluation_criteria", "contact_info"]:
        if not final_brief.get(field):
            user_input = st.chat_input(f"Please provide details for: {field.replace('_', ' ').title()}")
            if user_input:
                final_brief[field] = user_input
    return final_brief

def extract_fields_with_rag(file_obj, rfx_type):
    try:
        text = file_obj.read().decode("utf-8")
    except UnicodeDecodeError:
        text = file_obj.read().decode("latin-1")  # fallback encoding

    return {
        "background": text[:200],
        "objectives": None,
        "scope": None,
        "timeline": None,
        "budget": None,
        "evaluation_criteria": None,
        "contact_info": None
    }

def load_reference_template(rfx_type):
    try:
        with open(f"docs/{rfx_type.lower()}_template.txt", "r") as f:
            background = f.read()
    except FileNotFoundError:
        background = ""

    return {
        "background": background,
        "objectives": None,
        "scope": None,
        "timeline": None,
        "budget": None,
        "evaluation_criteria": None,
        "contact_info": None
    }