# nodes/autorefine_node.py
from agents.autorefine_agent import refine_question

def autorefinement_agent_node(state):
    print("[autorefinement_agent_node] Refining question due to inconsistency")
    new_question = refine_question(state)

    state["chat_history"].append({"role": "assistant", "content": new_question})
    state["llm_response"] = new_question
    state["user_input"] = None
    #if state.get("pending_question"):
    #    state["pending_question"]["asked"] = False
    state["next_action"] = "consistency_checker_agent"  # check new response
    return state