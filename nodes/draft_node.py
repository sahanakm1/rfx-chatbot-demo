# draft_node.py
# Generates a document from the completed brief.

from agents.draft_generator import build_doc_from_json
import os
import zipfile

def draft_node(state):
    brief = state.get("brief", {})
    section_content = state.get("section_content", {})

    if not brief:
        state.setdefault("logs", []).append("[Warning] No brief found. Document generation skipped.")
        state["document_path"] = ""
        state["document_generated"] = False
        return state

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

    try:
        # output directory
        output_folder = "drafts"
        os.makedirs(output_folder, exist_ok=True)

        # Save the generated document inside that folder
        docx_path = os.path.join(output_folder, "Generated_RFx_document.docx")
        zip_path = os.path.join(output_folder, "RFx_Brief_Package.zip")

        # Inject appendix filenames into E.1 section of the brief
        if "E" in formatted and "E.1" in formatted["E"]:
            appendix_files = state.get("appendix_files", [])
            if appendix_files:
                filenames_list = "\n".join(f"- {f.name}" for f in appendix_files)
                formatted["E"]["E.1"] = f"The following supporting documents are attached:\n{filenames_list}"


         # ✅ First generate the DOCX file
        build_doc_from_json(formatted, output_path=docx_path)

        # Handle appendix files
        appendix_files = state.get("appendix_files", [])
        appendix_paths = []

        # Deduplicate appendix files by filename
        unique_appendices = {}
        for file in appendix_files:
            if file.name not in unique_appendices:
                unique_appendices[file.name] = file

        appendix_paths = []
        for file_name, file in unique_appendices.items():
            file_path = os.path.join(output_folder, file_name)
            with open(file_path, "wb") as f:
                f.write(file.getbuffer())
            appendix_paths.append(file_path)

        # Create a final ZIP archive
        zip_path = os.path.join(output_folder, "RFx_Brief_Package.zip")

        with zipfile.ZipFile(zip_path, "w") as zipf:
            zipf.write(docx_path, arcname="Generated_RFx_document.docx")
            for path in appendix_paths:
                zipf.write(path, arcname=os.path.basename(path))

        # Update state
        state["document_path"] = zip_path
        state["docx_path"] = docx_path
        state["zip_path"] = zip_path

        state["document_generated"] = True
        state["brief_updated"] = True
        state["next_action"] = ""

        state["chat_history"].append({
        "role": "assistant",
        "content": "✅ Great! I will now proceed to generate the final document."
        })

        state["chat_history"].append({
            "role": "assistant",
            "content": "✅ Your RFx brief is ready and available for download in the right panel."
        })
        
        state["chat_history"].append({
        "role": "assistant",
        "content": (
            "📎 If you'd like to attach any additional supporting documents, you can upload them in the left panel.\n\n"
            "The uploaded documents will be included in the final ZIP package."
            )
        })

        # Detect if ZIP now includes any appendix files
        if appendix_paths:  # Only show this message if appendices are present
            if not any("final zipped file" in msg["content"] for msg in state["chat_history"] if msg["role"] == "assistant"):
                state["chat_history"].append({
                    "role": "assistant",
                    "content": "📦 The final zipped package with the RFx brief and supporting documents is now ready for download in the right panel."
                })

    except Exception as e:
        state.setdefault("logs", []).append(f"[Error] Document generation failed: {e}")
        state["document_path"] = ""
        state["document_generated"] = False

    return state