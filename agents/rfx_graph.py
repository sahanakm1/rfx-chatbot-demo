# agents/rfx_graph.py
from langgraph.graph import StateGraph
from typing import TypedDict, Optional
from agents.classification_agent import classify_rfx

class GraphState(TypedDict):
    user_input: str
    uploaded_text: Optional[str]
    rfx_type: Optional[str]
    output_message: Optional[str]
    logs: list

def classification_node(state: GraphState) -> GraphState:
    result = classify_rfx(
        text=state.get("uploaded_text", ""),
        user_input=state.get("user_input", "")
    )

    return {
        **state,
        "rfx_type": result["rfx_type"],        
        "logs": result["logs"],              
        "output_message": f"Thanks! Based on what you've shared, this looks like a {result['rfx_type']}."
    }

# LangGraph build
builder = StateGraph(GraphState)
builder.add_node("classify", classification_node)
builder.set_entry_point("classify")
builder.set_finish_point("classify")

rfx_graph = builder.compile()