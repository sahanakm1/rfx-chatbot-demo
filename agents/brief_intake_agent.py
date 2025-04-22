def run_brief_intake(rfx_type: str, user_input: str = "", uploaded_text: str = "") -> str:
    log = f"[BIA] Processing started for type: {rfx_type}"
    print(log)
    if uploaded_text:
        return f"Brief Intake Agent is reviewing the uploaded document for your {rfx_type} request. Please hold on..."
    else:
        return f"Let’s go step by step and collect all necessary information to build your {rfx_type} draft."

