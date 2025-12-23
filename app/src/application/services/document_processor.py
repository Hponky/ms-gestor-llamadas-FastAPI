import io
import pandas as pd
from abc import ABC, abstractmethod
from typing import Dict, Type
from pypdf import PdfReader
from PIL import Image
import pytesseract
from pdf2image import convert_from_bytes
from src.core.logger import logger

class IDocumentHandler(ABC):
    """Abstract Strategy for handling different document types."""
    @abstractmethod
    def extract_text(self, content: bytes) -> str:
        pass

class TextHandler(IDocumentHandler):
    def extract_text(self, content: bytes) -> str:
        return content.decode('utf-8', errors='ignore')

class CsvHandler(IDocumentHandler):
    def extract_text(self, content: bytes) -> str:
        df = pd.read_csv(io.BytesIO(content))
        return df.to_string()

class ExcelHandler(IDocumentHandler):
    def extract_text(self, content: bytes) -> str:
        df = pd.read_excel(io.BytesIO(content))
        return df.to_string()

class PdfHandler(IDocumentHandler):
    def extract_text(self, content: bytes) -> str:
        text = ""
        try:
            reader = PdfReader(io.BytesIO(content))
            for page in reader.pages:
                text += (page.extract_text() or "") + "\n"
            
            if not text.strip():
                logger.info("PDF appears to be scanned. Starting OCR...")
                images = convert_from_bytes(content)
                for image in images:
                    text += pytesseract.image_to_string(image) + "\n"
        except Exception as e:
            logger.error("Error processing PDF", error=str(e))
        return text

class ImageHandler(IDocumentHandler):
    def extract_text(self, content: bytes) -> str:
        try:
            image = Image.open(io.BytesIO(content))
            return pytesseract.image_to_string(image)
        except Exception as e:
            logger.error("Error processing image with OCR", error=str(e))
            return ""

class DocumentProcessor:
    """
    Service to extract text from various file formats using the Strategy Pattern.
    """
    _handlers: Dict[str, Type[IDocumentHandler]] = {
        'txt': TextHandler,
        'csv': CsvHandler,
        'xlsx': ExcelHandler,
        'xls': ExcelHandler,
        'pdf': PdfHandler,
        'png': ImageHandler,
        'jpg': ImageHandler,
        'jpeg': ImageHandler,
        'tiff': ImageHandler,
        'bmp': ImageHandler,
    }

    @classmethod
    def extract_text(cls, file_content: bytes, filename: str) -> str:
        ext = filename.split('.')[-1].lower()
        handler_class = cls._handlers.get(ext)
        
        if not handler_class:
            logger.warning(f"Unsupported file extension: {ext}")
            return ""
        
        handler = handler_class()
        return handler.extract_text(file_content)
