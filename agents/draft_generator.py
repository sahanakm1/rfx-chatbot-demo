import os
from docx import Document
from datetime import datetime

def create_draft(summary, category, rfx_type):
    # Create folder if not exists
    os.makedirs("drafts", exist_ok=True)

    # Create a Word document
    doc = Document()
    doc.add_heading(f'{rfx_type} Document for {category}', 0)

    # Metadata section
    doc.add_paragraph(f"Date: {datetime.today().strftime('%Y-%m-%d')}")
    doc.add_paragraph(f"Procurement Category: {category}")
    doc.add_paragraph(f"Document Type: {rfx_type}")

    doc.add_paragraph("\n---\n")

    # Summary Section
    doc.add_heading("Summary of Existing Documents", level=1)
    doc.add_paragraph(summary)

    doc.add_paragraph("\n---\n")
    doc.add_heading("Next Steps", level=1)
    doc.add_paragraph("Please review the content and fill in any organization-specific details before sharing with vendors.")

    # Save the document
    file_path = f"drafts/{rfx_type}_{category.replace(' ', '_')}.docx"
    doc.save(file_path)

    return file_path