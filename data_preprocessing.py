import json
import logging
from pathlib import Path
import pandas as pd

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
from langchain_text_splitters import MarkdownHeaderTextSplitter
from typing import List


headers_to_split_on = [
    ("#", "Header 1"),
    ("##", "Header 2"),
    ("###", "Header 3"),
]

def md_chunk_strat(headers_to_split_on,markdown_document):
    markdown_splitter = MarkdownHeaderTextSplitter(headers_to_split_on)
    md_header_splits = markdown_splitter.split_text(markdown_document)
    return md_header_splits
    

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
                InputFormat.XLSX,
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


def doc_converter_for_excel(conv_res,output_dir,conv_file_names,md_tables):
    doc_filename = conv_res.input.file.stem

    # Export tables
    for table_ix, table in enumerate(conv_res.document.tables):
        table_df: pd.DataFrame = table.export_to_dataframe()
        #print(f"## Table {table_ix}")
        #print(table_df.to_markdown())

        with (output_dir / f"{doc_filename}-table-{table_ix + 1}.md").open("w",encoding="utf-8") as fp:
            fp.write(table_df.to_markdown())
        
        conv_file_names.append(f"{doc_filename}-table-{table_ix + 1}.md")

        chunks = md_chunk_strat(headers_to_split_on,table_df.to_markdown())
        for c in chunks:
            md_tables.append(c)
    
    return conv_file_names,md_tables

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

       conv_file_names=[]
       md_docs=[]

       
       for res in conv_results:
          out_path = Path("Scratch")
          out_path.mkdir(parents=True, exist_ok=True)
          print(
             f"Document {res.input.file.name} converted."
             f"\nSaved markdown output to: {out_path!s}"
          ) 

          if res.input.file.name.endswith(".xlsx"):
             conv_file_names,md_docs = doc_converter_for_excel(res,out_path,conv_file_names,md_docs)
          else:
              with (out_path / f"{res.input.file.stem}.md").open("w",encoding = "utf-8") as fp:
                 fp.write(res.document.export_to_markdown())
              conv_file_names.append(f"{res.input.file.stem}.md")
        
              chunks = md_chunk_strat(headers_to_split_on,res.document.export_to_markdown())
              for c in chunks:
                 md_docs.append(c)

       return md_docs