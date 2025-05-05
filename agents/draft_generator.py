import json
from docx import Document
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.shared import Pt
from docx.enum.text import WD_ALIGN_PARAGRAPH

TOC = {
    "A. INTRODUCTION": ["A.1 Goal of RFP", "A.2 About Organization"],
    "B. PROJECT": ["B.1 Details", "B.2 Goals of Project"],
    "C. SCOPE": ["C.1 Schedule", "C.2 Evaluation Criteria"]
}

def add_heading(doc, text, level):
    p = doc.add_heading(text, level=level)
    p.alignment = WD_ALIGN_PARAGRAPH.LEFT

def add_paragraph(doc, text):
    p = doc.add_paragraph(text)
    p.style.font.size = Pt(11)
    return p

def insert_toc(paragraph):
    """Insert a field code for TOC that Word will convert into a clickable TOC"""
    fldChar1 = OxmlElement('w:fldChar')
    fldChar1.set(qn('w:fldCharType'), 'begin')
    instrText = OxmlElement('w:instrText')
    instrText.set(qn('xml:space'), 'preserve')
    instrText.text = 'TOC \\o "1-3" \\h \\z \\u'
    fldChar2 = OxmlElement('w:fldChar')
    fldChar2.set(qn('w:fldCharType'), 'separate')
    fldChar3 = OxmlElement('w:fldChar')
    fldChar3.set(qn('w:fldCharType'), 'end')
    r = paragraph.add_run()
    r._r.append(fldChar1)
    r._r.append(instrText)
    r._r.append(fldChar2)
    r._r.append(fldChar3)

def build_doc_from_json(data_json, output_path="drafts/Generated_Document.docx"):
    doc = Document()
    doc.add_heading("Generated Proposal", level=0)
    
    # Insert TOC Placeholder
    toc_paragraph = doc.add_paragraph()
    insert_toc(toc_paragraph)
    doc.add_page_break()
    
    for section_title, subsections in TOC.items():
        section_key = section_title.split(".")[0]
        add_heading(doc, section_title, level=1)
        if subsections:
            for subsection in subsections:
                subsection_key = subsection.split()[0]
                heading_text = subsection
                content = data_json.get(section_key, {}).get(subsection_key, "(No content provided)")
                add_heading(doc, heading_text, level=2)
                add_paragraph(doc, content)
        else:
            content = data_json.get(section_key, "(No content provided)")
            add_paragraph(doc, content)
    
    doc.save(output_path)
    print(f"Document saved as {output_path}")
    print("Open the document in Word and press F9 to update the TOC!")
    
    return output_path