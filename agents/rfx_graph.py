from langgraph.graph import StateGraph
from langgraph.graph.message import add_messages
from typing import TypedDict, Optional
from agents.classification_agent import classify_rfx

class GraphState(TypedDict):
    user_input: str
    uploaded_text: Optional[str]
    rfx_type: Optional[str]
    output_message: Optional[str]

# Node: Classify RFx type
def classification_node(state: GraphState) -> GraphState:
    rfx_type = classify_rfx(text=state.get("uploaded_text", ""), user_input=state.get("user_input", ""))
    return {
        **state,
        "rfx_type": rfx_type
    }

# Node: Generate confirmation message
def confirmation_node(state: GraphState) -> GraphState:
    message = f"Thanks! Based on what you've shared, this looks like a {state['rfx_type']}. I’ll now guide you through the rest."
    return {
        **state,
        "output_message": message
    }

# LangGraph definition
builder = StateGraph(GraphState)
builder.add_node("classify", classification_node)
builder.add_node("respond", confirmation_node)
builder.set_entry_point("classify")
builder.add_edge("classify", "respond")
builder.set_finish_point("respond")

rfx_graph = builder.compile()