
# draft_node.py
# Generates a document from the completed brief.

from agents.draft_generator import build_doc_from_json

def draft_node(state):
    brief = state.get("brief", {})

    if not brief:
        state.setdefault("logs", []).append("[Warning] No brief found. Document generation skipped.")
        state["document_path"] = ""
        state["document_generated"] = False
        return state

    # # Prepare brief answers for doc generation
    # formatted = {
    #     section: {
    #         sub: val.get("answer", "(No content provided)")
    #         for sub, val in subs.items()
    #     } for section, subs in brief.items()
    # }
    section_content = state.get("section_content", {})

    formatted = {}

    # Flatten section_content keys to lower-case for safer matching
    section_lookup = {
        key.strip().lower(): value.get("text", "").strip()
        for key, value in section_content.items()
        if value.get("text", "").strip().upper() != "N/A"
    }
    for section, subs in brief.items():
        formatted[section] = {}
        for sub, val in subs.items():
            title = val.get("title", "").strip().lower()
            fallback = val.get("answer", "(No content provided)").strip()

            # Use right panel content if it matches the title
            best_match = section_lookup.get(title)
            formatted[section][sub] = best_match if best_match else fallback

    try:
        path = build_doc_from_json(formatted)
        state["document_path"] = path
        state["document_generated"] = True
        state["brief_updated"] = True
    except Exception as e:
        state.setdefault("logs", []).append(f"[Error] Document generation failed: {e}")
        state["document_path"] = ""
        state["document_generated"] = False

    return state


    