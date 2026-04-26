from typing import List
from langchain_community.document_loaders import PyPDFLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_core.documents import Document
from app.core.config import settings

class PDFService:
    @staticmethod
    def extract_and_chunk(file_path: str) -> List[Document]:
        """
        Loads a PDF and splits it into chunks with metadata.
        """
        loader = PyPDFLoader(file_path)
        documents = loader.load()
        
        text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=settings.CHUNK_SIZE,
            chunk_overlap=settings.CHUNK_OVERLAP,
            length_function=len,
            add_start_index=True,
        )
        
        chunks = text_splitter.split_documents(documents)
        return chunks
