# agents/brief_intake_agent.py

from typing import Dict, Tuple, List

# Define all required top-level and sub-sections
REQUIRED_STRUCTURE = {
    "A": ["A.1", "A.2"],
    "B": ["B.1", "B.2", "B.3", "B.4"],
    "C": ["C.1", "C.2", "C.3"],
    "D": ["D.1", "D.2"],
    "E": []  # E is a single block, not sub-divided
}

def run_brief_intake(rfx_type: str, user_input: str, uploaded_text: str = "") -> Tuple[Dict, List[str]]:
    """
    Builds a nested brief structure.
    If no document is provided, marks all subsections (or section 'E') as missing.
    """
    brief = {}
    missing_sections = []

    for section, subkeys in REQUIRED_STRUCTURE.items():
        if uploaded_text.strip():
            if subkeys:
                brief[section] = {sub: None for sub in subkeys}  # Placeholder for extracted content
            else:
                brief[section] = None
        else:
            # Add either full section or subsections to missing list
            if subkeys:
                missing_sections.extend(subkeys)
                brief[section] = {sub: None for sub in subkeys}
            else:
                missing_sections.append(section)
                brief[section] = None

    return brief, missing_sections

def update_brief_with_user_response(brief: Dict, section: str, content: str) -> Dict:
    """
    Updates a specific section or subsection of the brief with user-provided content.
    Automatically handles nested structure.
    """
    # Handle full section like "E"
    if section in brief:
        brief[section] = content
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
