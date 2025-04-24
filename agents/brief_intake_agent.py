# agents/brief_intake_agent.py

from typing import Dict, Tuple, List

REQUIRED_SECTIONS = ["context", "goals", "deliverables", "dates"]

def run_brief_intake(rfx_type: str, user_input: str, uploaded_text: str = "") -> Tuple[Dict, List[str]]:
    """
    Build initial brief structure from either uploaded text or user input.
    If no uploaded document is provided, mark all sections as missing.
    """
    brief = {}
    missing_sections = []

    for section in REQUIRED_SECTIONS:
        if uploaded_text.strip():
            # Placeholder – real implementation would extract section from text
            brief[section] = None
        else:
            missing_sections.append(section)
    
    return brief, missing_sections

def update_brief_with_user_response(brief: Dict, section: str, content: str) -> Dict:
    """
    Updates a specific section of the brief with user-provided content.
    """
    brief[section] = content
    return brief
