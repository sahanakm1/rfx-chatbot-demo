# agents/brief_intake_agent.py

from typing import Dict, Tuple, List

# Define all required top-level and sub-sections
REQUIRED_STRUCTURE = {
    "A": {'A.1': "What is the main goal or objective of issuing this RFI?", 
          'A.2': "Please provide a brief background or context of the project or business need."},
    "B": {'B.1': "What specific types of information are you seeking from vendors?", 
          'B.2': "What key criteria will be used to evaluate vendor responses?"},
    "C": {'C.1': "What areas of functionality or service are most critical to your needs?", 
          'C.2': "Are there any existing systems or processes the solution should integrate with?"},
    "D": {'D.1': 'I see you are based in Spain. Is this the geography for which the RFI or the document you want to generate is? <span style="color:green">Based on this it can search for the specific strategy document in your geography.</span>'}
}


def run_brief_intake(rfx_type: str, user_input: str, uploaded_text: str = "") -> Tuple[Dict, List[str]]:
    """
    Builds a nested brief structure.
    If no document is provided, marks all subsections (or section 'E') as missing.
    """
    brief = {}
    missing_sections = []

    for section, subkeys in REQUIRED_STRUCTURE.items():
        brief[section] = {}
        for sub, question in subkeys.items():
            brief[section][sub] = {
                "question": question,
                "answer": None  # TODO: here must go the answer from the model
            }
            if not brief[section][sub]["answer"]:  # if the model does not provide answer then this section is marked as missing
                missing_sections.append((section,sub))

    return brief, missing_sections

def update_brief_with_user_response(brief: Dict, section: str, sub: str, content: str) -> Dict:
    """
    Updates a specific section or subsection of the brief with user-provided content.
    Automatically handles nested structure.
    """
    # Handle full section like "E"
    print("---------")
    print(section)
    print("\n")
    print(brief)
    print("\n")
    print(content)
    if section in brief:
        brief[section][sub] = content
        return brief

    # Handle subsection like "A.1", "B.2", etc.
    for top_section, subsections in REQUIRED_STRUCTURE.items():
        if section in subsections:
            if top_section not in brief:
                brief[top_section] = {}
            brief[top_section][section] = content
            return brief

    # If section is unrecognized, return unchanged
    return brief
