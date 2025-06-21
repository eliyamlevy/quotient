"""PDF text extraction using OCR and text parsing."""

import logging
from pathlib import Path
from typing import List, Optional
import fitz  # PyMuPDF
import pytesseract
from PIL import Image
import io

from ...core.config import QuotientConfig


class PDFExtractor:
    """Extract text from PDF documents using OCR and text parsing."""
    
    def __init__(self, config: QuotientConfig):
        """Initialize the PDF extractor.
        
        Args:
            config: Configuration object
        """
        self.config = config
        self.logger = logging.getLogger(__name__)
        
        # Configure tesseract path if needed
        if hasattr(config, 'tesseract_path'):
            pytesseract.pytesseract.tesseract_cmd = config.tesseract_path
    
    def extract_text(self, file_path: Path) -> str:
        """Extract text from PDF file.
        
        Args:
            file_path: Path to the PDF file
            
        Returns:
            Extracted text content
        """
        self.logger.info(f"Extracting text from PDF: {file_path}")
        
        try:
            # Try to extract text directly first
            text = self._extract_native_text(file_path)
            
            # If no text found, use OCR
            if not text.strip():
                self.logger.info("No native text found, using OCR")
                text = self._extract_ocr_text(file_path)
            
            return text
            
        except Exception as e:
            self.logger.error(f"Error extracting text from PDF {file_path}: {str(e)}")
            raise
    
    def _extract_native_text(self, file_path: Path) -> str:
        """Extract native text from PDF (no OCR needed).
        
        Args:
            file_path: Path to the PDF file
            
        Returns:
            Extracted text
        """
        text_parts = []
        
        try:
            doc = fitz.open(file_path)
            
            for page_num in range(doc.page_count):
                page = doc.load_page(page_num)
                
                # Extract text from page
                page_text = page.get_text()
                if page_text.strip():
                    text_parts.append(page_text)
            
            doc.close()
            
        except Exception as e:
            self.logger.warning(f"Failed to extract native text: {str(e)}")
        
        return "\n".join(text_parts)
    
    def _extract_ocr_text(self, file_path: Path) -> str:
        """Extract text using OCR.
        
        Args:
            file_path: Path to the PDF file
            
        Returns:
            Extracted text using OCR
        """
        text_parts = []
        
        try:
            doc = fitz.open(file_path)
            
            for page_num in range(doc.page_count):
                page = doc.load_page(page_num)
                
                # Convert page to image
                mat = fitz.Matrix(2, 2)  # Scale factor for better OCR
                pix = page.get_pixmap(matrix=mat)
                
                # Convert to PIL Image
                img_data = pix.tobytes("png")
                img = Image.open(io.BytesIO(img_data))
                
                # Perform OCR
                page_text = pytesseract.image_to_string(img)
                if page_text.strip():
                    text_parts.append(page_text)
            
            doc.close()
            
        except Exception as e:
            self.logger.error(f"OCR extraction failed: {str(e)}")
            raise
        
        return "\n".join(text_parts)
    
    def extract_tables(self, file_path: Path) -> List[List[List[str]]]:
        """Extract tables from PDF.
        
        Args:
            file_path: Path to the PDF file
            
        Returns:
            List of tables (each table is a list of rows, each row is a list of cells)
        """
        tables = []
        
        try:
            doc = fitz.open(file_path)
            
            for page_num in range(doc.page_count):
                page = doc.load_page(page_num)
                
                # Extract tables from page
                page_tables = page.get_tables()
                tables.extend(page_tables)
            
            doc.close()
            
        except Exception as e:
            self.logger.warning(f"Failed to extract tables: {str(e)}")
        
        return tables
    
    def get_page_count(self, file_path: Path) -> int:
        """Get the number of pages in the PDF.
        
        Args:
            file_path: Path to the PDF file
            
        Returns:
            Number of pages
        """
        try:
            doc = fitz.open(file_path)
            page_count = doc.page_count
            doc.close()
            return page_count
            
        except Exception as e:
            self.logger.error(f"Failed to get page count: {str(e)}")
            return 0 