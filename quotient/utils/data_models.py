"""Data models for the Quotient system."""

from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional, Union
from datetime import datetime
from enum import Enum
import pandas as pd


class ItemStatus(Enum):
    """Status of an inventory item."""
    PENDING = "pending"
    COMPLETE = "complete"
    INCOMPLETE = "incomplete"
    ERROR = "error"


class DataSource(Enum):
    """Source of the data."""
    PDF = "pdf"
    EMAIL = "email"
    EXCEL = "excel"
    CSV = "csv"
    IMAGE = "image"
    TEXT = "text"


@dataclass
class InventoryItem:
    """Represents a single inventory item."""
    
    # Basic identification
    item_name: str
    part_number: Optional[str] = None
    sku: Optional[str] = None
    
    # Quantities and pricing
    quantity: Optional[int] = None
    unit_price: Optional[float] = None
    total_price: Optional[float] = None
    
    # Vendor information
    vendor_name: Optional[str] = None
    vendor_id: Optional[str] = None
    vendor_contact: Optional[str] = None
    
    # Specifications
    description: Optional[str] = None
    specifications: Dict[str, Any] = field(default_factory=dict)
    category: Optional[str] = None
    
    # Metadata
    source_document: Optional[str] = None
    extraction_confidence: Optional[float] = None
    status: ItemStatus = ItemStatus.PENDING
    
    # Timestamps
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)
    
    # Processing metadata
    raw_text: Optional[str] = None
    extracted_fields: Dict[str, Any] = field(default_factory=dict)
    
    def __post_init__(self):
        """Calculate derived fields after initialization."""
        if self.quantity and self.unit_price and not self.total_price:
            self.total_price = self.quantity * self.unit_price
        
        if self.total_price and self.quantity and not self.unit_price:
            self.unit_price = self.total_price / self.quantity
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "item_name": self.item_name,
            "part_number": self.part_number,
            "sku": self.sku,
            "quantity": self.quantity,
            "unit_price": self.unit_price,
            "total_price": self.total_price,
            "vendor_name": self.vendor_name,
            "vendor_id": self.vendor_id,
            "vendor_contact": self.vendor_contact,
            "description": self.description,
            "specifications": self.specifications,
            "category": self.category,
            "source_document": self.source_document,
            "extraction_confidence": self.extraction_confidence,
            "status": self.status.value,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
            "raw_text": self.raw_text,
            "extracted_fields": self.extracted_fields
        }
    
    def to_dataframe_row(self) -> Dict[str, Any]:
        """Convert to DataFrame row format."""
        return {
            "Item Name": self.item_name,
            "Part Number": self.part_number,
            "SKU": self.sku,
            "Quantity": self.quantity,
            "Unit Price": self.unit_price,
            "Total Price": self.total_price,
            "Vendor Name": self.vendor_name,
            "Vendor ID": self.vendor_id,
            "Vendor Contact": self.vendor_contact,
            "Description": self.description,
            "Category": self.category,
            "Status": self.status.value,
            "Source Document": self.source_document,
            "Extraction Confidence": self.extraction_confidence
        }
    
    def is_complete(self) -> bool:
        """Check if the item has all required fields."""
        required_fields = ["item_name"]
        optional_but_important = ["quantity", "unit_price", "vendor_name"]
        
        # Check required fields
        for field in required_fields:
            if not getattr(self, field):
                return False
        
        # Check if we have at least some important fields
        important_fields_present = sum(
            1 for field in optional_but_important 
            if getattr(self, field) is not None
        )
        
        return important_fields_present >= 2  # At least 2 important fields


@dataclass
class GapAnalysis:
    """Represents gaps in inventory item data."""
    
    item: InventoryItem
    missing_fields: List[str] = field(default_factory=list)
    confidence_scores: Dict[str, float] = field(default_factory=dict)
    suggested_searches: List[str] = field(default_factory=list)
    priority: int = 1  # 1 = high, 2 = medium, 3 = low
    
    def __post_init__(self):
        """Analyze gaps after initialization."""
        self._analyze_gaps()
        self._generate_search_terms()
        self._calculate_priority()
    
    def _analyze_gaps(self):
        """Identify missing fields."""
        important_fields = [
            "part_number", "sku", "quantity", "unit_price", 
            "vendor_name", "description", "category"
        ]
        
        self.missing_fields = [
            field for field in important_fields
            if not getattr(self.item, field)
        ]
    
    def _generate_search_terms(self):
        """Generate search terms for missing information."""
        base_terms = []
        
        if self.item.item_name:
            base_terms.append(self.item.item_name)
        
        if self.item.part_number:
            base_terms.append(self.item.part_number)
        
        if self.item.vendor_name:
            base_terms.append(self.item.vendor_name)
        
        # Generate search combinations
        for field in self.missing_fields:
            if base_terms:
                search_term = f"{' '.join(base_terms)} {field}"
                self.suggested_searches.append(search_term)
    
    def _calculate_priority(self):
        """Calculate priority based on missing fields."""
        critical_fields = ["quantity", "unit_price"]
        important_fields = ["vendor_name", "part_number"]
        
        critical_missing = sum(1 for field in critical_fields if field in self.missing_fields)
        important_missing = sum(1 for field in important_fields if field in self.missing_fields)
        
        if critical_missing > 0:
            self.priority = 1
        elif important_missing > 0:
            self.priority = 2
        else:
            self.priority = 3


@dataclass
class ProcessingResult:
    """Result of processing a document through the pipeline."""
    
    # Input information
    source_path: Optional[str] = None
    source_type: Optional[DataSource] = None
    processing_timestamp: datetime = field(default_factory=datetime.now)
    
    # Extracted data
    items: List[InventoryItem] = field(default_factory=list)
    raw_text: Optional[str] = None
    
    # Processing metadata
    extraction_confidence: float = 0.0
    processing_time: float = 0.0
    errors: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    
    # Layer-specific results
    layer1_result: Optional[Dict[str, Any]] = None
    layer2_result: Optional[Dict[str, Any]] = None
    layer3_result: Optional[Dict[str, Any]] = None
    
    def add_item(self, item: InventoryItem):
        """Add an inventory item to the result."""
        self.items.append(item)
    
    def add_error(self, error: str):
        """Add an error message."""
        self.errors.append(error)
    
    def add_warning(self, warning: str):
        """Add a warning message."""
        self.warnings.append(warning)
    
    def to_dataframe(self) -> pd.DataFrame:
        """Convert to pandas DataFrame."""
        if not self.items:
            return pd.DataFrame()
        
        rows = [item.to_dataframe_row() for item in self.items]
        return pd.DataFrame(rows)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "source_path": self.source_path,
            "source_type": self.source_type.value if self.source_type else None,
            "processing_timestamp": self.processing_timestamp.isoformat(),
            "items": [item.to_dict() for item in self.items],
            "raw_text": self.raw_text,
            "extraction_confidence": self.extraction_confidence,
            "processing_time": self.processing_time,
            "errors": self.errors,
            "warnings": self.warnings,
            "layer1_result": self.layer1_result,
            "layer2_result": self.layer2_result,
            "layer3_result": self.layer3_result
        }
    
    def get_summary(self) -> Dict[str, Any]:
        """Get a summary of the processing result."""
        total_items = len(self.items)
        complete_items = sum(1 for item in self.items if item.is_complete())
        incomplete_items = total_items - complete_items
        
        return {
            "total_items": total_items,
            "complete_items": complete_items,
            "incomplete_items": incomplete_items,
            "completion_rate": complete_items / total_items if total_items > 0 else 0,
            "extraction_confidence": self.extraction_confidence,
            "processing_time": self.processing_time,
            "error_count": len(self.errors),
            "warning_count": len(self.warnings)
        } 