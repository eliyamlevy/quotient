"""Babbage Service: Data Ingestion and Structure."""

import logging
import time
from pathlib import Path
from typing import List, Dict, Any, Optional, Union

from ..core.config import QuotientConfig
from ..utils.data_models import InventoryItem, ProcessingResult, DataSource, ItemStatus
from ..utils.validators import (
    validate_file_type, validate_file_size, validate_pdf_content,
    validate_image_content, validate_spreadsheet_content
)
from ..utils.formatters import (
    parse_currency, parse_quantity, format_part_number, format_vendor_name,
    extract_contact_info, clean_text_for_processing
)
from .extractors.pdf_extractor import PDFExtractor
from .extractors.image_extractor import ImageExtractor
from .extractors.spreadsheet_extractor import SpreadsheetExtractor
from .processors.entity_extractor import EntityExtractor
from .normalizers.data_normalizer import DataNormalizer
from .preproc import PreprocPipeline


class Babbage:
    """Babbage Service: Handles data ingestion from various sources and extracts structured information."""
    
    def __init__(self, config: QuotientConfig):
        """Initialize the Babbage service.
        
        Args:
            config: Configuration object
        """
        self.config = config
        self.logger = logging.getLogger(__name__)
        
        # Initialize extractors
        self.pdf_extractor = PDFExtractor(config)
        self.image_extractor = ImageExtractor(config)
        self.spreadsheet_extractor = SpreadsheetExtractor(config)
        
        # Initialize processors
        self.entity_extractor = EntityExtractor(config)
        self.data_normalizer = DataNormalizer(config)
        
        # Initialize preprocessing pipeline (will be set up after entity_extractor is ready)
        self.preproc = None
        
        # Statistics
        self.stats = {
            "total_processed": 0,
            "total_items": 0,
            "successful_extractions": 0,
            "failed_extractions": 0
        }
    
        self.logger.info("Babbage Service initialized successfully")
    
    def _setup_preproc(self):
        """Setup preprocessing pipeline with LLM prompt function."""
        if self.preproc is None:
            self.preproc = PreprocPipeline(llm_prompt_func=self.entity_extractor.prompt_llm)
            self.logger.info("Preprocessing pipeline initialized")
    
    def process_documents(self, document_paths: List[Path]) -> ProcessingResult:
        """Process multiple documents and extract inventory information.
        
        Args:
            document_paths: List of document paths to process
            
        Returns:
            ProcessingResult containing extracted items and metadata
        """
        if not document_paths:
            return ProcessingResult(items=[], extraction_confidence=0.0, processing_time=0.0)
        
        # For now, process the first document
        # In the future, this could process multiple documents and merge results
        return self.process_document(document_paths[0])
    
    def process_document(self, file_path: Union[str, Path]) -> ProcessingResult:
        """Process a document and extract inventory information.
        
        Args:
            file_path: Path to the document to process
            
        Returns:
            ProcessingResult containing extracted items and metadata
        """
        start_time = time.time()
        file_path = Path(file_path)
        
        self.logger.info(f"Babbage processing document: {file_path}")
        
        # Create result object
        result = ProcessingResult(
            source_path=str(file_path),
            source_type=self._determine_source_type(file_path)
        )
        
        try:
            # Validate file
            self._validate_file(file_path, result)
            
            # Extract text content
            raw_text = self._extract_text(file_path, result)
            result.raw_text = raw_text
            
            if not raw_text:
                result.add_error("No text content extracted from document")
                return result
            
            # Setup preprocessing pipeline if not already done
            self._setup_preproc()
            
            # Preprocess text using the 3-layer pipeline
            preproc_results = None
            if self.preproc is not None:
                try:
                    preproc_results = self.preproc.run_pipeline(raw_text)
                    preprocessed_text = preproc_results['layer3']  # Use final layer output
                    self.logger.info("Text preprocessing completed successfully")
                except Exception as e:
                    self.logger.warning(f"Preprocessing failed, using original text: {str(e)}")
                    preprocessed_text = raw_text
            else:
                self.logger.warning("Preprocessing pipeline not available, using original text")
                preprocessed_text = raw_text
            
            # Extract entities using AI
            extracted_data = self.entity_extractor.extract_entities(preprocessed_text)
            
            # Create inventory items
            items = self._create_inventory_items(extracted_data, str(file_path))
            
            # Normalize data
            normalized_items = self.data_normalizer.normalize_inventory_items(items)
            
            # Add items to result
            for item in normalized_items:
                result.add_item(item)
            
            # Update statistics
            self.stats["total_processed"] += 1
            self.stats["total_items"] += len(normalized_items)
            self.stats["successful_extractions"] += 1
            
            # Calculate confidence
            result.extraction_confidence = self._calculate_confidence(normalized_items)
            
        except Exception as e:
            self.logger.error(f"Error processing {file_path}: {str(e)}")
            result.add_error(f"Processing failed: {str(e)}")
            self.stats["failed_extractions"] += 1
        
        finally:
            result.processing_time = time.time() - start_time
            result.layer1_result = {
                "service": "babbage",
                "extraction_method": self._get_extraction_method(file_path),
                "text_length": len(result.raw_text) if result.raw_text else 0,
                "items_extracted": len(result.items),
                "preprocessing": {
                    "enabled": self.preproc is not None,
                    "results": preproc_results if preproc_results else None,
                    "preprocessed_text_length": len(preprocessed_text) if 'preprocessed_text' in locals() else len(result.raw_text) if result.raw_text else 0
                }
            }
        
        return result
    
    def get_supported_formats(self) -> List[str]:
        """Get list of supported file formats.
        
        Returns:
            List of supported file extensions
        """
        return ['.pdf', '.png', '.jpg', '.jpeg', '.tiff', '.bmp', '.xlsx', '.xls', '.csv', '.txt']
    
    def validate_document(self, document_path: Path) -> Dict[str, Any]:
        """Validate if a document can be processed.
        
        Args:
            document_path: Path to the document
            
        Returns:
            Validation result dictionary
        """
        try:
            file_path = Path(document_path)
            
            # Check if file exists
            if not file_path.exists():
                return {
                    'valid': False,
                    'error': 'File does not exist',
                    'supported': False
                }
            
            # Check file type
            supported_formats = [fmt.lstrip('.') for fmt in self.config.supported_formats]
            is_valid, error_msg = validate_file_type(str(file_path), supported_formats)
            if not is_valid:
                return {
                    'valid': False,
                    'error': error_msg,
                    'supported': False,
                    'file_type': file_path.suffix.lower()
                }
            
            # Check file size
            is_size_valid, size_error = validate_file_size(str(file_path), self.config.max_file_size_mb)
            if not is_size_valid:
                return {
                    'valid': False,
                    'error': size_error,
                    'supported': True,
                    'file_size_mb': file_path.stat().st_size / (1024 * 1024)
                }
            
            return {
                'valid': True,
                'supported': True,
                'file_type': file_path.suffix.lower(),
                'file_size_mb': file_path.stat().st_size / (1024 * 1024)
            }
            
        except Exception as e:
            return {
                'valid': False,
                'error': str(e),
                'supported': False
            }
    
    def get_service_status(self) -> Dict[str, Any]:
        """Get Babbage service status and health information.
        
        Returns:
            Dictionary with service status information
        """
        return {
            "service": "babbage",
            "status": "healthy",
            "version": "1.0.0",
            "statistics": self.stats.copy(),
            "extractors": {
                "pdf": "available",
                "image": "available", 
                "spreadsheet": "available"
            },
            "processors": {
                "entity_extractor": "available",
                "data_normalizer": "available"
            }
        }
    
    def _determine_source_type(self, file_path: Path) -> DataSource:
        """Determine the source type based on file extension.
        
        Args:
            file_path: Path to the file
            
        Returns:
            DataSource enum value
        """
        extension = file_path.suffix.lower()
        
        if extension == '.pdf':
            return DataSource.PDF
        elif extension in ['.png', '.jpg', '.jpeg', '.tiff', '.bmp']:
            return DataSource.IMAGE
        elif extension in ['.xlsx', '.xls']:
            return DataSource.EXCEL
        elif extension == '.csv':
            return DataSource.CSV
        else:
            return DataSource.TEXT
    
    def _validate_file(self, file_path: Path, result: ProcessingResult):
        """Validate the file before processing.
        
        Args:
            file_path: Path to the file
            result: ProcessingResult to add errors to
        """
        if not file_path.exists():
            result.add_error(f"File not found: {file_path}")
            return
        
        # Get supported formats from config
        supported_formats = [fmt.lstrip('.') for fmt in self.config.supported_formats]
        
        is_valid, error_msg = validate_file_type(str(file_path), supported_formats)
        if not is_valid:
            result.add_error(error_msg)
            return
        
        if not validate_file_size(str(file_path), self.config.max_file_size_mb):
            result.add_error(f"File too large: {file_path.stat().st_size / (1024 * 1024):.2f} MB")
            return
    
    def _extract_text(self, file_path: Path, result: ProcessingResult) -> str:
        """Extract text content from the file.
        
        Args:
            file_path: Path to the file
            result: ProcessingResult to add errors to
            
        Returns:
            Extracted text content
        """
        try:
            source_type = self._determine_source_type(file_path)
            
            if source_type == DataSource.PDF:
                return self.pdf_extractor.extract_text(file_path)
            elif source_type == DataSource.IMAGE:
                return self.image_extractor.extract_text(file_path)
            elif source_type in [DataSource.EXCEL, DataSource.CSV]:
                return self.spreadsheet_extractor.extract_text(file_path)
            else:
                # Try to read as text file
                with open(file_path, 'r', encoding='utf-8') as f:
                    return f.read()
                    
        except Exception as e:
            result.add_error(f"Text extraction failed: {str(e)}")
            return ""
    
    def _create_inventory_items(self, extracted_data: List[Dict[str, Any]], source_document: str) -> List[InventoryItem]:
        """Create InventoryItem objects from extracted data.
        
        Args:
            extracted_data: List of extracted entity dictionaries
            source_document: Source document identifier
            
        Returns:
            List of InventoryItem objects
        """
        items = []
        
        for entity in extracted_data:
            try:
                item = InventoryItem(
                    item_name=entity.get('name', entity.get('description', 'Unknown Item')),
                    part_number=entity.get('part_number'),
                    sku=entity.get('sku', entity.get('part_number')),
                    quantity=entity.get('quantity'),
                    unit_price=entity.get('unit_price'),
                    total_price=entity.get('total_price'),
                    vendor_name=entity.get('manufacturer', entity.get('vendor_name')),
                    vendor_id=entity.get('vendor_id'),
                    vendor_contact=entity.get('vendor_contact'),
                    description=entity.get('description', ''),
                    specifications=entity.get('specifications', {}),
                    category=entity.get('category'),
                    source_document=source_document,
                    extraction_confidence=entity.get('confidence', 0.5),
                    status=ItemStatus.PENDING,
                    raw_text=entity.get('raw_text', ''),
                    extracted_fields=entity
                )
                items.append(item)
                
            except Exception as e:
                self.logger.warning(f"Failed to create InventoryItem from entity: {str(e)}")
                continue
        
        return items
    
    def _calculate_confidence(self, items: List[InventoryItem]) -> float:
        """Calculate overall confidence score for extracted items.
        
        Args:
            items: List of inventory items
            
        Returns:
            Average confidence score
        """
        if not items:
            return 0.0
        
        total_confidence = sum(item.extraction_confidence or 0.0 for item in items)
        return total_confidence / len(items)
    
    def _get_extraction_method(self, file_path: Path) -> str:
        """Get the extraction method used for the file.
        
        Args:
            file_path: Path to the file
            
        Returns:
            Extraction method name
        """
        source_type = self._determine_source_type(file_path)
        
        if source_type == DataSource.PDF:
            return "pdf_extractor"
        elif source_type == DataSource.IMAGE:
            return "image_ocr"
        elif source_type in [DataSource.EXCEL, DataSource.CSV]:
            return "spreadsheet_parser"
        else:
            return "text_reader"
    
    def get_stats(self) -> Dict[str, Any]:
        """Get processing statistics.
        
        Returns:
            Dictionary with statistics
        """
        return self.stats.copy()

    def prompt_llm(self, prompt: str) -> str:
        """Directly prompt the underlying LLM and return the raw response text."""
        return self.entity_extractor.prompt_llm(prompt) 