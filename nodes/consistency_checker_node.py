# nodes/consistency_checker_node.py
from agents.consistency_checker_agent import check_consistency

def consistency_checker_node(state):
    print("[consistency_checker_node] Checking if user response is valid")
    if not state.get("pending_question") or not state.get("user_input"):
        print("[consistency_checker_node] Skipping: no pending question or empty input")
        return state
    
    result = check_consistency(state)
    print("[consistency_checker_node] Result:", result)

    if result == "YES":
        state["consistency_check_result"] = "YES"
        state["next_action"] = "ask_brief_question" # next question
    else:
        state["next_action"] = "refine_question"
        state["consistency_check_result"] = "NO"
        state["next_action"] = "autorefinement_agent"
    
    return state
    
