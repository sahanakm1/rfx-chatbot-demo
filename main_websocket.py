# main_websocket.py

import base64
import uuid
import json
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware

from app.state_handler import initialize_state, handle_uploaded_files
from orchestrator.main_graph import build_graph

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

graph = build_graph()
connections = {}

# ✅ Helper method to run the graph multiple times if needed
def run_graph_with_retries(state, max_runs=3):
    run_count = 0
    while run_count < max_runs:
        updated_state = graph.invoke(state)
        state.update(updated_state)
        run_count += 1

        if not (
            state.get("user_input") or
            state.get("next_action") or
            (state.get("pending_question") and not state["pending_question"].get("asked")) or
            state.get("intent")
        ):
            break
    return state

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()

    session_id = str(uuid.uuid4())
    state = initialize_state()
    connections[session_id] = state

    await websocket.send_text(json.dumps({
        "action": "new_session",
        "session_id": session_id
    }))

    try:
        while True:
            data = await websocket.receive_text()
            msg = json.loads(data)
            action = msg.get("action")

            if action == "reset_conversation":
                session_id = str(uuid.uuid4())
                state = initialize_state()
                connections[session_id] = state
                await websocket.send_text(json.dumps({
                    "action": "new_session",
                    "session_id": session_id
                }))
                continue

            session_id = msg.get("session_id", session_id)
            if session_id not in connections:
                connections[session_id] = initialize_state()
            state = connections[session_id]

            # 🧠 Track logs before graph runs
            previous_logs = list(state.get("logs", []))

            if action == "file_upload":
                files = msg.get("files", [])
                decoded_files = []
                for f in files:
                    content = base64.b64decode(f["content"])
                    file_like = type("UploadedFile", (), {
                        "name": f["filename"],
                        "read": lambda: content,
                        "content_type": f["mime_type"]
                    })()
                    decoded_files.append(file_like)

                handle_uploaded_files(state, decoded_files)

                await websocket.send_text(json.dumps({
                    "action": "files_ingested",
                    "session_id": session_id,
                    "message": f"{len(decoded_files)} document(s) uploaded and processed.",
                    "files": [f.name for f in decoded_files]
                }))

                # 🔁 Run graph after uploading files
                state = run_graph_with_retries(state)

            elif action in ["user_message", "ping"]:
                if action == "user_message":
                    user_message = msg["content"]
                    state["user_input"] = user_message
                    state.setdefault("chat_history", []).append({
                        "role": "user",
                        "content": user_message
                    })

                state = run_graph_with_retries(state)

            # ✅ Process messages from outbox if present
            outbox = state.pop("outbox", [])
            for out_msg in outbox:
                out_msg["session_id"] = session_id
                await websocket.send_text(json.dumps(out_msg))

                if out_msg.get("action") == "message" and out_msg.get("role") == "assistant":
                    state.setdefault("chat_history", []).append({
                        "role": "assistant",
                        "content": out_msg["content"],
                        "_sent": True
                    })

            # ✅ Send any new assistant messages not marked as sent
            for msg in state.get("chat_history", []):
                if msg.get("role") == "assistant" and not msg.get("_sent", False):
                    await websocket.send_text(json.dumps({
                        "action": "message",
                        "role": "assistant",
                        "content": msg["content"],
                        "session_id": session_id
                    }))
                    msg["_sent"] = True

            # 📤 Send any new logs to client
            current_logs = state.get("logs", [])
            new_logs = current_logs[len(previous_logs):]
            if new_logs:
                await websocket.send_text(json.dumps({
                    "action": "logs_update",
                    "logs": new_logs,
                    "session_id": session_id
                }))

            # ✅ Send brief_structure once if rfx_type exists and brief is still empty
            if state.get("rfx_type") and not state.get("brief") and not state.get("brief_structure_sent"):
                await websocket.send_text(json.dumps({
                    "action": "brief_structure",
                    "sections": [
                        {"id": "A", "title": "INTRODUCTION", "status": "pending"},
                        {"id": "B", "title": "PURPOSE & TIMELINE", "status": "pending"},
                        {"id": "C", "title": "PROJECT SCOPE", "status": "pending"},
                        {"id": "D", "title": "PROPOSAL DETAILS", "status": "pending"},
                        {"id": "E", "title": "GEOGRAPHY", "status": "pending"}
                    ],
                    "session_id": session_id
                }))
                state["brief_structure_sent"] = True

            

            brief = state.get("brief", {})
            state.setdefault("_sent_brief_subsections", {})  # dict of {section_id: set(sub_ids)}
            for section_id, section_data in brief.items():
                sent_subs = state["_sent_brief_subsections"].setdefault(section_id, set())
                new_content = []
                for sub_id, sub in section_data.items():
                    if sub.get("answer") and sub["answer"] != "N/A" and sub_id not in sent_subs:
                        new_content.append(f"### {sub['title']}\n{sub['answer']}")
                        sent_subs.add(sub_id)

                if new_content:
                    # Determine status of section
                    all_answered = all(s["answer"] != "N/A" for s in section_data.values())
                    none_answered = all(s["answer"] == "N/A" for s in section_data.values())
                    status = "completed" if all_answered else ("pending" if none_answered else "in_progress")

                    await websocket.send_text(json.dumps({
                        "action": "brief_section_update",
                        "section": {
                            "id": section_id,
                            "status": status,
                            "content": "\n\n".join(new_content)
                        },
                        "session_id": session_id
                    }))

            connections[session_id] = state

    except WebSocketDisconnect:
        connections.pop(session_id, None)
        print("🔌 Client disconnected")
