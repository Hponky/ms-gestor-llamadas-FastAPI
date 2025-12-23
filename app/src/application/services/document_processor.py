import io
import pandas as pd
import numpy as np
from abc import ABC, abstractmethod
from typing import Dict, Type, List, Optional
from pypdf import PdfReader
from PIL import Image
from pdf2image import convert_from_bytes
from src.core.logger import logger

# Lazy import PaddleOCR to avoid heavy loading if not used
class OCRManager:
    _instance = None

    @classmethod
    def get_ocr(cls):
        if cls._instance is None:
            try:
                from paddleocr import PaddleOCR
                # use_angle_cls=True handles tilted text
                # lang='es' handles Spanish (ñ, tildes)
                cls._instance = PaddleOCR(use_angle_cls=True, lang='es', show_log=False)
                logger.info("PaddleOCR v4 initialized successfully with Spanish support.")
            except Exception as e:
                logger.error("Failed to initialize PaddleOCR", error=str(e))
                return None
        return cls._instance

    @classmethod
    def extract_from_image(cls, pil_image: Image.Image) -> str:
        ocr = cls.get_ocr()
        if not ocr:
            return ""
        
        try:
            # Convert PIL Image to RGB and then to numpy array for PaddleOCR
            img_array = np.array(pil_image.convert('RGB'))
            result = ocr.ocr(img_array, cls=True)
            
            if not result or not result[0]:
                return ""
                
            lines = []
            for line in result:
                for word_info in line:
                    # word_info structure: [[coords], (text, confidence)]
                    text = word_info[1][0]
                    lines.append(text)
            
            return " ".join(lines)
        except Exception as e:
            logger.error("Error during PaddleOCR extraction", error=str(e))
            return ""

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
                logger.info("PDF appears to be scanned. Starting PaddleOCR...")
                images = convert_from_bytes(content)
                for image in images:
                    text += OCRManager.extract_from_image(image) + "\n"
        except Exception as e:
            logger.error("Error processing PDF", error=str(e))
        return text

class ImageHandler(IDocumentHandler):
    def extract_text(self, content: bytes) -> str:
        try:
            image = Image.open(io.BytesIO(content))
            return OCRManager.extract_from_image(image)
        except Exception as e:
            logger.error("Error processing image with OCR", error=str(e))
            return ""

class DocumentProcessor:
    """
    Service to extract text from various file formats using the Strategy Pattern.
    Now powered by PaddleOCR v4 for maximum precision.
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
