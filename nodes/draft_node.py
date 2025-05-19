# draft_node.py
# Generates a document from the completed brief.

from agents.draft_generator import build_doc_from_json

def draft_node(state):
    brief = state.get("brief", {})
    section_content = state.get("section_content", {})

    if not brief:
        state.setdefault("logs", []).append("[Warning] No brief found. Document generation skipped.")
        state["document_path"] = ""
        state["document_generated"] = False
        return state

    # Flatten section_content with cleaned keys
    section_lookup = {
        key.strip().lower(): value.get("text", "").strip()
        for key, value in section_content.items()
        if value.get("text", "").strip().upper() != "N/A"
    }

    formatted = {}

    for section, subs in brief.items():
        formatted[section] = {}
        for sub, val in subs.items():
            title = val.get("title", "").strip().lower()
            fallback = val.get("answer", "(No content provided)").strip()

            # Partial match logic (fuzzy match)
            best_match = next(
                (text for key, text in section_lookup.items() if title in key),
                None
            )
            formatted[section][sub] = best_match if best_match else fallback

    # Try to generate the document
    try:
        path = build_doc_from_json(formatted)
        state["document_path"] = path
        state["document_generated"] = True
        state["brief_updated"] = True
        state["next_action"] = ""
        
        state["chat_history"].append({
            "role": "assistant",
            "content": "✅ The RFx brief is now complete and ready for download in right panel. If you’d like to make edits or generate a new version, just let me know!"
        })
    except Exception as e:
        state.setdefault("logs", []).append(f"[Error] Document generation failed: {e}")
        state["document_path"] = ""
        state["document_generated"] = False

    return state