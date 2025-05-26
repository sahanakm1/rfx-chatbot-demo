from agents.blob_storage import blob_storage

import os
import json
import io
import uuid
from docx import Document
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.shared import Pt
from docx.enum.text import WD_ALIGN_PARAGRAPH



TOC = {
    "A. INTRODUCTION": ["A.1 JTI", "A.2 Our Engagement"],
    "B. PURPOSE OF THE RFP": ["B.1 Responses", "B.2 Schedule", "B.3 Queries", "B.4 Evaluation Criteria"],
    "C. CONTEXT": ["C.1 Project Scope and Objective", "C.2 JTI Requirements", "C.3 Proposal evaluation criteria"],
    "D. RESPONSE": ["D.1 Executive Summary", "D.2 Additional proposal details"],
    "E. APPENDICES": ["E.1 Supporting Documents"]
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
    doc.add_paragraph("")
    
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
    
    # ✅ Create output directory if it doesn't exist
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    
    print(doc)
    doc.save(output_path)
    print(f"Document saved as {output_path}")
    print("Open the document in Word and press F9 to update the TOC!")

    output_path = os.path.abspath(output_path)
    file_name = os.path.basename(output_path)
    file_path = os.path.dirname(output_path)

    blob_storage().upload_blob_file(container_name="rfx-draft",file_path=file_path,file_name=file_name)
    return output_path