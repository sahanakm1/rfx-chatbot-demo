from agents.draft_generator import build_doc_from_json
import zipfile
import io
import os

def draft_node(state):
    brief = state.get("brief", {})
    section_content = state.get("section_content", {})

    if not brief:
        state.setdefault("logs", []).append("[Warning] No brief found. Document generation skipped.")
        state["document_path"] = ""
        state["document_generated"] = False
        return state

    # 🔚 Prevent ZIP regeneration
    if state.get("zip_announced"):
        print("[draft_node] ✅ ZIP already announced — exiting.")
        return state

    # Flatten section content for fuzzy mapping
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
            best_match = next((text for key, text in section_lookup.items() if title in key), None)
            formatted[section][sub] = best_match if best_match else fallback

    # ✅ Generate the base Word doc
    try:
        path = build_doc_from_json(formatted)
        state["document_path"] = path
        state["document_generated"] = True
        state["brief_updated"] = True
        state["chat_history"].append({
            "role": "assistant",
            "content": "✅ The RFx brief is now complete and ready for download in the right panel."
        })
        state["chat_history"].append({
            "role": "assistant",
            "content": "🤖 Would you like to make any changes to the brief, or are you happy with the content?"
        })
        state["awaiting_brief_confirm"] = True
    except Exception as e:
        state.setdefault("logs", []).append(f"[Error] Document generation failed: {e}")
        state["document_path"] = ""
        state["document_generated"] = False
        return state

    # ✅ If user responds to confirmation question, move forward with additional doc upload step
    user_input = (state.get("user_input") or "").lower() if state.get("awaiting_brief_confirm") else ""
    if state.get("awaiting_brief_confirm") and user_input:
        state["chat_history"].append({"role": "user", "content": user_input})
        state["user_input"] = None
        state["awaiting_brief_confirm"] = False
        state["upload_stage"] = "final"
        state["appendix_files"] = []
        state["chat_history"].append({
            "role": "assistant",
            "content": "📎 If you'd like to attach any additional supporting documents, you can upload them now using the panel on the left. These will be added as appendices in the final ZIP package."
        })
        return state

    # ✅ Now process ZIP only if final files exist
    appendix_files = state.get("appendix_files", [])
    print("📦 DEBUG: appendix_files =", [f['name'] for f in appendix_files])
    if not appendix_files:
        print("[draft_node] ⏸ No appendix files uploaded — skipping ZIP.")
        return state

    # ✅ Inject appendix section into the brief
    appendix_list = "\n".join(f"- {f['name']}" for f in appendix_files)
    if "E" not in formatted:
        formatted["E"] = {}
    formatted["E"]["E.1"] = f"The following supporting documents are attached:\n{appendix_list}"

    try:
        path = build_doc_from_json(formatted)
        state["document_path"] = path
    except Exception as e:
        state.setdefault("logs", []).append(f"[Error] Document regeneration for ZIP failed: {e}")
        return state

    zip_buffer = io.BytesIO()
    with zipfile.ZipFile(zip_buffer, "w", zipfile.ZIP_DEFLATED) as zipf:
        zipf.write(path, arcname="RFx_Brief.docx")
        for file in appendix_files:
            zipf.writestr(file["name"], file["data"])

    zip_path = "zip_outputs/Final_RFx_Package.zip"
    os.makedirs(os.path.dirname(zip_path), exist_ok=True)
    with open(zip_path, "wb") as f:
        f.write(zip_buffer.getvalue())

    state["zip_path"] = zip_path
    state["zip_announced"] = True
    state["next_action"] = ""
    state.setdefault("logs", []).append(f"[STEP] Final package zipped with {len(appendix_files)} appendix files.")
    state["chat_history"].append({
        "role": "assistant",
        "content": "✅ The final zipped file with the RFx brief and supporting documents is now ready for download in the right panel."
    })

    return state