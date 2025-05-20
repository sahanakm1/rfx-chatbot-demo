# nodes/autorefine_node.py
from agents.autorefine_agent import refine_question, refine_user_answer
from agents.brief_intake_agent import update_brief_with_user_response

def autorefinement_agent_node(state):
    print("[autorefinement_agent_node] Refining input based on consistency result")
    
    consistency = state.get("consistency_check_result", "")
    
    if consistency == "REFINE":
        print("[autorefinement_agent_node] Refining user answer")
        refined_answer = refine_user_answer(state)
        #print("[autorefinement_agent_node] refined answer: "+refined_answer)


        if refined_answer:
            section = state["pending_question"]["section"]
            sub = state["pending_question"]["sub"]
            state["chat_history"].append({
                "role": "assistant",
                "content": f"""✏️ Updated section **{section}.{sub}** with a refined version of your answer.  
                <br>  
                After a review — we made it clearer and more aligned with the question, based on the feedback from our internal agents: `Consistency Checker Agent` and  `Refinement Agent`."""
            })
        
            # Guardar la respuesta refinada en el brief
            update_brief_with_user_response(state, refined_answer)
            state["brief_updated"] = True
            state["user_input"] = None

        
        
        # Continuar con la siguiente pregunta
        state["next_action"] = "ask_brief_question"
    
    elif consistency == "NO":
        print("[autorefinement_agent_node] Reformulating question")
        new_question = refine_question(state)

        state["chat_history"].append({"role": "assistant", "content": new_question})
        state["llm_response"] = new_question
        state["user_input"] = None
        state["next_action"] = "consistency_checker_agent"  # re-evaluate new user input

    else:
        print("[autorefinement_agent_node] Unexpected state: defaulting to ask_brief_question")
        state["next_action"] = "ask_brief_question"

    return state