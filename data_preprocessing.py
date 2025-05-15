import json
import logging
from pathlib import Path

from langchain_community.document_loaders import PyMuPDFLoader
from docling.backend.pypdfium2_backend import PyPdfiumDocumentBackend
from docling.datamodel.base_models import InputFormat
from docling.document_converter import (
    DocumentConverter,
    PdfFormatOption,
    WordFormatOption,
)
from docling.pipeline.simple_pipeline import SimplePipeline
from docling.pipeline.standard_pdf_pipeline import StandardPdfPipeline
from typing import List

doc_converter = (
        DocumentConverter(  # all of the below is optional, has internal defaults.
            allowed_formats=[
                InputFormat.PDF,
                InputFormat.IMAGE,
                InputFormat.DOCX,
                InputFormat.HTML,
                InputFormat.PPTX,
                InputFormat.ASCIIDOC,
                InputFormat.CSV,
                InputFormat.MD,
            ],  # whitelist formats, non-matching files are ignored.
            format_options={
                InputFormat.PDF: PdfFormatOption(
                    pipeline_cls=StandardPdfPipeline, backend=PyPdfiumDocumentBackend
                ),
                InputFormat.DOCX: WordFormatOption(
                    pipeline_cls=SimplePipeline  # , backend=MsWordDocumentBackend
                ),
            },
        )
    )




class data_preprocessing:
    def __init__(self, file_path):
      self.file_path = file_path

    def load_data(self):
      loader = PyMuPDFLoader(self.file_path)
      data = loader.load()
      return data
    

class DocumentConverter:
    def __init__(self, input_path:List):
        self.input_path = input_path

    def convert_pdf_to_md(self):
       conv_results = doc_converter.convert_all(self.input_path)

       output_files = []
       for res in conv_results:
          out_path = Path("Scratch")
          out_path.mkdir(parents=True, exist_ok=True)
          print(
             f"Document {res.input.file.name} converted."
             f"\nSaved markdown output to: {out_path!s}"
          ) 
          try:
             with(out_path / f"{res.input.file.stem}.md").open("w") as fp:
                fp.write(res.document.export_to_markdown())
          except:
             with(out_path / f"{res.input.file.stem}.md").open("w",encoding="utf-8") as fp:
                fp.write(res.document.export_to_markdown())

          output_files.append(out_path / f"{res.input.file.stem}.md")
       return output_files