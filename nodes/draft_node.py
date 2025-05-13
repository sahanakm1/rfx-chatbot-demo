
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

    # Prepare brief answers for doc generation
    formatted = {
        section: {
            sub: val.get("answer", "(No content provided)")
            for sub, val in subs.items()
        } for section, subs in brief.items()
    }

    try:
        path = build_doc_from_json(formatted)
        state["document_path"] = path
        state["document_generated"] = True
    except Exception as e:
        state.setdefault("logs", []).append(f"[Error] Document generation failed: {e}")
        state["document_path"] = ""
        state["document_generated"] = False

    return state