from langchain_community.document_loaders import PyMuPDFLoader

class data_preprocessing:
    def __init__(self, file_path):
      self.file_path = file_path

    def load_data(self):
      loader = PyMuPDFLoader(self.file_path)
      data = loader.load()
      return data
# def pdf_loader(file_path):
#     loader = PyMuPDFLoader(file_path,mode="page")