from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.schema.document import Document

def split_text(text: str, chunk_size: int = 500, chunk_overlap: int = 50) -> list:
    """
    Splits raw document text into chunks for embedding and vector storage.
    """
    splitter = RecursiveCharacterTextSplitter(chunk_size=chunk_size, chunk_overlap=chunk_overlap)
    return splitter.split_documents([Document(page_content=text)])