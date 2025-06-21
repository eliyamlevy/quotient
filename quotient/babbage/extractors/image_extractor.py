"""Image text extraction using OCR."""

import logging
from pathlib import Path
from typing import List, Optional
import pytesseract
from PIL import Image
import cv2
import numpy as np

from ...core.config import QuotientConfig


class ImageExtractor:
    """Extract text from images using OCR."""
    
    def __init__(self, config: QuotientConfig):
        """Initialize the image extractor.
        
        Args:
            config: Configuration object
        """
        self.config = config
        self.logger = logging.getLogger(__name__)
        
        # Configure tesseract path if needed
        if hasattr(config, 'tesseract_path'):
            pytesseract.pytesseract.tesseract_cmd = config.tesseract_path
    
    def extract_text(self, file_path: Path) -> str:
        """Extract text from image file.
        
        Args:
            file_path: Path to the image file
            
        Returns:
            Extracted text content
        """
        self.logger.info(f"Extracting text from image: {file_path}")
        
        try:
            # Load and preprocess image
            image = self._load_and_preprocess_image(file_path)
            
            # Extract text using OCR
            text = pytesseract.image_to_string(image)
            
            return text.strip()
            
        except Exception as e:
            self.logger.error(f"Error extracting text from image {file_path}: {str(e)}")
            raise
    
    def _load_and_preprocess_image(self, file_path: Path) -> np.ndarray:
        """Load and preprocess image for better OCR results.
        
        Args:
            file_path: Path to the image file
            
        Returns:
            Preprocessed image as numpy array
        """
        # Load image
        image = cv2.imread(str(file_path))
        
        if image is None:
            raise ValueError(f"Could not load image: {file_path}")
        
        # Convert to grayscale
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        
        # Apply preprocessing techniques for better OCR
        processed = self._enhance_image_for_ocr(gray)
        
        return processed
    
    def _enhance_image_for_ocr(self, gray_image: np.ndarray) -> np.ndarray:
        """Enhance image for better OCR results.
        
        Args:
            gray_image: Grayscale image
            
        Returns:
            Enhanced image
        """
        # Apply noise reduction
        denoised = cv2.medianBlur(gray_image, 3)
        
        # Apply thresholding to get binary image
        _, binary = cv2.threshold(denoised, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
        
        # Apply morphological operations to clean up
        kernel = np.ones((1, 1), np.uint8)
        cleaned = cv2.morphologyEx(binary, cv2.MORPH_CLOSE, kernel)
        
        return cleaned
    
    def extract_text_with_confidence(self, file_path: Path) -> List[dict]:
        """Extract text with confidence scores.
        
        Args:
            file_path: Path to the image file
            
        Returns:
            List of dictionaries with text and confidence
        """
        try:
            image = self._load_and_preprocess_image(file_path)
            
            # Get detailed OCR data
            data = pytesseract.image_to_data(image, output_type=pytesseract.Output.DICT)
            
            results = []
            for i in range(len(data['text'])):
                if data['conf'][i] > 0:  # Filter out low confidence results
                    results.append({
                        'text': data['text'][i],
                        'confidence': data['conf'][i] / 100.0,
                        'bbox': (
                            data['left'][i],
                            data['top'][i],
                            data['width'][i],
                            data['height'][i]
                        )
                    })
            
            return results
            
        except Exception as e:
            self.logger.error(f"Error extracting text with confidence: {str(e)}")
            return []
    
    def extract_tables(self, file_path: Path) -> List[List[List[str]]]:
        """Extract tables from image.
        
        Args:
            file_path: Path to the image file
            
        Returns:
            List of tables
        """
        try:
            image = self._load_and_preprocess_image(file_path)
            
            # Extract table structure
            tables = pytesseract.image_to_data(
                image, 
                output_type=pytesseract.Output.DICT,
                config='--psm 6'
            )
            
            # Process table data
            # This is a simplified implementation
            # For more complex tables, consider using specialized libraries
            
            return []
            
        except Exception as e:
            self.logger.warning(f"Failed to extract tables: {str(e)}")
            return []
    
    def get_image_info(self, file_path: Path) -> dict:
        """Get basic information about the image.
        
        Args:
            file_path: Path to the image file
            
        Returns:
            Dictionary with image information
        """
        try:
            with Image.open(file_path) as img:
                return {
                    'format': img.format,
                    'mode': img.mode,
                    'size': img.size,
                    'width': img.width,
                    'height': img.height
                }
                
        except Exception as e:
            self.logger.error(f"Failed to get image info: {str(e)}")
            return {} 