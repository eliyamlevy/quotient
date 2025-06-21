"""Main pipeline for Quotient AI-powered inventory management."""

import logging
from typing import List, Dict, Any, Optional
from pathlib import Path

from .config import QuotientConfig
from ..utils.data_models import InventoryItem, ProcessingResult, GapAnalysis
from ..babbage.ingestion import Babbage


class QuotientPipeline:
    """Main pipeline orchestrating the three-layer architecture."""
    
    def __init__(self, config: QuotientConfig):
        """Initialize the pipeline.
        
        Args:
            config: Configuration object
        """
        self.config = config
        self.logger = logging.getLogger(__name__)
        
        # Initialize services
        self.babbage = Babbage(config)
        
        # Layer 2 and 3 will be implemented later
        self.layer2 = None  # Gap analysis and web search
        self.layer3 = None  # Data completion
    
    def process_documents(self, document_paths: List[Path]) -> ProcessingResult:
        """Process documents through the complete pipeline.
        
        Args:
            document_paths: List of document file paths
            
        Returns:
            Processing result with extracted and completed data
        """
        self.logger.info(f"Processing {len(document_paths)} documents")
        
        try:
            # Layer 1: Data ingestion and extraction
            self.logger.info("Starting Layer 1 (Babbage) - Data ingestion")
            layer1_result = self.babbage.process_documents(document_paths)
            
            if not layer1_result.items:
                self.logger.warning("No items extracted from documents")
                return ProcessingResult(
                    source_path=str(document_paths[0]) if document_paths else None,
                    items=[],
                    extraction_confidence=0.0,
                    processing_time=0.0
                )
            
            self.logger.info(f"Layer 1 extracted {len(layer1_result.items)} items")
            
            # For now, return Layer 1 results
            # Layer 2 and 3 will be implemented in future iterations
            return layer1_result
            
        except Exception as e:
            self.logger.error(f"Pipeline processing failed: {str(e)}")
            raise
    
    def process_single_document(self, document_path: Path) -> ProcessingResult:
        """Process a single document through the pipeline.
        
        Args:
            document_path: Path to the document
            
        Returns:
            Processing result
        """
        return self.process_documents([document_path])
    
    def get_processing_status(self) -> Dict[str, Any]:
        """Get the current status of the pipeline.
        
        Returns:
            Dictionary with pipeline status information
        """
        return {
            'layer1_babbage': 'available',
            'layer2_gap_analysis': 'not_implemented',
            'layer3_data_completion': 'not_implemented',
            'config': {
                'llm_backend': self.config.llm_backend,
                'llama_model': self.config.llama_model,
                'supported_formats': self.babbage.get_supported_formats()
            }
        }
    
    def validate_document(self, document_path: Path) -> Dict[str, Any]:
        """Validate if a document can be processed.
        
        Args:
            document_path: Path to the document
            
        Returns:
            Validation result
        """
        return self.babbage.validate_document(document_path) 