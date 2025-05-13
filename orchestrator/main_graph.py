# graph/main_graph.py
# Defines and compiles the LangGraph workflow used to manage the RFx assistant logic flow.

from typing import Dict, Any
from langgraph.graph import StateGraph

from nodes.chat_node import chat_node
from nodes.classification_node import classification_node
from nodes.brief_node import brief_node
from nodes.draft_node import draft_node
from nodes.orchestrator_router import orchestrator_router

# Simple passthrough node used to evaluate external routing conditions
# This node delegates decision-making to `orchestrator_router`
def orchestrator_node(state):
    return state

# Build and return the LangGraph execution graph
def build_graph():
    graph = StateGraph(Dict[str, Any])

    # Register agent nodes
    graph.add_node("orchestrator", orchestrator_node)
    graph.add_node("chat_agent", chat_node)
    graph.add_node("classification_agent", classification_node)
    graph.add_node("brief_intake_agent", brief_node)
    graph.add_node("draft_generator", draft_node)

    # Add routing logic: dynamically determine the next node from state
    graph.add_conditional_edges("orchestrator", orchestrator_router, {
        "chat_agent": "chat_agent",
        "classification_agent": "classification_agent",
        "brief_intake_agent": "brief_intake_agent",
        "draft_generator": "draft_generator",
        "end": "__end__",
    })

    # Define the graph's entry point
    graph.set_entry_point("orchestrator")
    return graph.compile()
