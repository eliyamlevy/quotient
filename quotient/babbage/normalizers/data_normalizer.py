"""Data normalization for inventory information."""

import logging
from typing import List, Dict, Any, Optional, Union
import re
from datetime import datetime

from ...core.config import QuotientConfig
from ...utils.data_models import InventoryItem


class DataNormalizer:
    """Normalize and standardize inventory data."""
    
    def __init__(self, config: QuotientConfig):
        """Initialize the data normalizer.
        
        Args:
            config: Configuration object
        """
        self.config = config
        self.logger = logging.getLogger(__name__)
    
    def normalize_inventory_items(self, items: Union[List[Dict[str, Any]], List[InventoryItem]]) -> List[InventoryItem]:
        """Normalize a list of inventory items.
        
        Args:
            items: List of raw inventory item dictionaries or InventoryItem objects
            
        Returns:
            List of normalized InventoryItem objects
        """
        self.logger.info(f"Normalizing {len(items)} inventory items")
        
        normalized_items = []
        
        for item in items:
            try:
                if isinstance(item, dict):
                    normalized_item = self._normalize_single_item(item)
                elif isinstance(item, InventoryItem):
                    normalized_item = self._normalize_inventory_item(item)
                else:
                    self.logger.warning(f"Unknown item type: {type(item)}")
                    continue
                    
                if normalized_item:
                    normalized_items.append(normalized_item)
                    
            except Exception as e:
                self.logger.warning(f"Failed to normalize item: {str(e)}")
                continue
        
        return normalized_items
    
    def normalize_items(self, items: List[InventoryItem]) -> List[InventoryItem]:
        """Legacy method for backward compatibility.
        
        Args:
            items: List of inventory items to normalize
            
        Returns:
            List of normalized inventory items
        """
        return self.normalize_inventory_items(items)
    
    def _normalize_inventory_item(self, item: InventoryItem) -> InventoryItem:
        """Normalize a single InventoryItem object.
        
        Args:
            item: InventoryItem to normalize
            
        Returns:
            Normalized InventoryItem
        """
        # Create a copy to avoid modifying original
        normalized = InventoryItem(
            item_name=self._normalize_name(item.item_name),
            part_number=self._normalize_part_number(item.part_number) if item.part_number else None,
            sku=self._normalize_part_number(item.sku) if item.sku else None,
            quantity=self._normalize_quantity(item.quantity),
            unit_price=self._normalize_price(item.unit_price),
            total_price=self._normalize_price(item.total_price),
            vendor_name=self._normalize_manufacturer(item.vendor_name) if item.vendor_name else None,
            vendor_id=item.vendor_id,
            vendor_contact=item.vendor_contact,
            description=self._normalize_description(item.description) if item.description else None,
            specifications=item.specifications.copy(),
            category=self._normalize_category(item.category) if item.category else None,
            source_document=item.source_document,
            extraction_confidence=item.extraction_confidence,
            status=item.status,
            raw_text=item.raw_text,
            extracted_fields=item.extracted_fields.copy()
        )
        
        return normalized
    
    def _normalize_single_item(self, item: Dict[str, Any]) -> Optional[InventoryItem]:
        """Normalize a single inventory item.
        
        Args:
            item: Raw item dictionary
            
        Returns:
            Normalized InventoryItem or None
        """
        try:
            # Extract and normalize basic fields
            name = self._normalize_name(item.get('name', item.get('item_name', '')))
            description = self._normalize_description(item.get('description', ''))
            quantity = self._normalize_quantity(item.get('quantity', 0))
            unit_price = self._normalize_price(item.get('unit_price', 0.0))
            category = self._normalize_category(item.get('category', ''))
            manufacturer = self._normalize_manufacturer(item.get('manufacturer', item.get('vendor_name', '')))
            part_number = self._normalize_part_number(item.get('part_number', item.get('sku', '')))
            unit = self._normalize_unit(item.get('unit', 'pcs'))
            
            # Create InventoryItem
            normalized_item = InventoryItem(
                item_name=name,
                description=description,
                quantity=quantity,
                unit_price=unit_price,
                category=category,
                vendor_name=manufacturer,
                part_number=part_number,
                sku=part_number,  # Use part_number as SKU if no separate SKU
                status=item.get('status', 'pending')
            )
            
            return normalized_item
            
        except Exception as e:
            self.logger.error(f"Error normalizing item: {str(e)}")
            return None
    
    def _normalize_name(self, name: str) -> str:
        """Normalize item name.
        
        Args:
            name: Raw name
            
        Returns:
            Normalized name
        """
        if not name:
            return "Unknown Item"
        
        # Remove extra whitespace
        name = re.sub(r'\s+', ' ', name.strip())
        
        # Capitalize first letter of each word
        name = name.title()
        
        # Remove common prefixes/suffixes that don't add value
        prefixes_to_remove = ['Item:', 'Product:', 'Part:', 'SKU:']
        for prefix in prefixes_to_remove:
            if name.startswith(prefix):
                name = name[len(prefix):].strip()
        
        return name if name else "Unknown Item"
    
    def _normalize_description(self, description: str) -> str:
        """Normalize item description.
        
        Args:
            description: Raw description
            
        Returns:
            Normalized description
        """
        if not description:
            return ""
        
        # Remove extra whitespace and normalize line breaks
        description = re.sub(r'\s+', ' ', description.strip())
        
        # Remove excessive punctuation
        description = re.sub(r'[!]{2,}', '!', description)
        description = re.sub(r'[?]{2,}', '?', description)
        
        return description
    
    def _normalize_quantity(self, quantity) -> int:
        """Normalize quantity value.
        
        Args:
            quantity: Raw quantity value
            
        Returns:
            Normalized quantity as integer
        """
        if quantity is None:
            return 0
        
        try:
            if isinstance(quantity, str):
                # Extract numeric value from string
                numeric_match = re.search(r'(\d+)', quantity)
                if numeric_match:
                    return int(numeric_match.group(1))
                return 0
            else:
                return int(quantity)
                
        except (ValueError, TypeError):
            return 0
    
    def _normalize_price(self, price) -> float:
        """Normalize price value.
        
        Args:
            price: Raw price value
            
        Returns:
            Normalized price as float
        """
        if price is None:
            return 0.0
        
        try:
            if isinstance(price, str):
                # Remove currency symbols and clean up
                cleaned = re.sub(r'[^\d.,]', '', price)
                
                # Handle different decimal formats
                if ',' in cleaned and '.' in cleaned:
                    if cleaned.find(',') > cleaned.find('.'):
                        cleaned = cleaned.replace('.', '').replace(',', '.')
                    else:
                        cleaned = cleaned.replace(',', '')
                elif ',' in cleaned:
                    cleaned = cleaned.replace(',', '')
                
                if cleaned:
                    return float(cleaned)
                return 0.0
            else:
                return float(price)
                
        except (ValueError, TypeError):
            return 0.0
    
    def _normalize_category(self, category: str) -> str:
        """Normalize category.
        
        Args:
            category: Raw category
            
        Returns:
            Normalized category
        """
        if not category:
            return "Unknown"
        
        # Standardize common categories
        category_mapping = {
            'electronics': 'Electronics',
            'electronic': 'Electronics',
            'electrical': 'Electronics',
            'mechanical': 'Mechanical',
            'mech': 'Mechanical',
            'chemical': 'Chemical',
            'chem': 'Chemical',
            'office': 'Office Supplies',
            'office supplies': 'Office Supplies',
            'tools': 'Tools',
            'tool': 'Tools',
            'hardware': 'Hardware',
            'software': 'Software',
            'raw materials': 'Raw Materials',
            'raw material': 'Raw Materials',
            'finished goods': 'Finished Goods',
            'finished good': 'Finished Goods',
            'packaging': 'Packaging',
            'misc': 'Miscellaneous',
            'miscellaneous': 'Miscellaneous',
            'other': 'Miscellaneous',
            'unknown': 'Unknown'
        }
        
        category_lower = category.lower().strip()
        
        # Check for exact matches
        if category_lower in category_mapping:
            return category_mapping[category_lower]
        
        # Check for partial matches
        for key, value in category_mapping.items():
            if key in category_lower or category_lower in key:
                return value
        
        # If no match found, capitalize and return
        return category.title()
    
    def _normalize_manufacturer(self, manufacturer: str) -> str:
        """Normalize manufacturer name.
        
        Args:
            manufacturer: Raw manufacturer name
            
        Returns:
            Normalized manufacturer name
        """
        if not manufacturer:
            return ""
        
        # Remove extra whitespace
        manufacturer = re.sub(r'\s+', ' ', manufacturer.strip())
        
        # Standardize common company suffixes
        suffix_mapping = {
            'inc': 'Inc.',
            'incorporated': 'Inc.',
            'corp': 'Corp.',
            'corporation': 'Corp.',
            'llc': 'LLC',
            'ltd': 'Ltd.',
            'limited': 'Ltd.',
            'co': 'Co.',
            'company': 'Co.'
        }
        
        # Split into words
        words = manufacturer.split()
        
        # Process each word
        normalized_words = []
        for word in words:
            word_lower = word.lower()
            if word_lower in suffix_mapping:
                normalized_words.append(suffix_mapping[word_lower])
            else:
                # Capitalize first letter
                normalized_words.append(word.title())
        
        return ' '.join(normalized_words)
    
    def _normalize_part_number(self, part_number: str) -> str:
        """Normalize part number.
        
        Args:
            part_number: Raw part number
            
        Returns:
            Normalized part number
        """
        if not part_number:
            return ""
        
        # Remove extra whitespace and convert to uppercase
        part_number = part_number.strip().upper()
        
        # Remove common prefixes
        prefixes_to_remove = ['PART#', 'PART:', 'SKU:', 'ITEM#', 'ITEM:']
        for prefix in prefixes_to_remove:
            if part_number.startswith(prefix):
                part_number = part_number[len(prefix):].strip()
        
        return part_number
    
    def _normalize_unit(self, unit: str) -> str:
        """Normalize unit of measurement.
        
        Args:
            unit: Raw unit
            
        Returns:
            Normalized unit
        """
        if not unit:
            return "pcs"
        
        # Standardize common units
        unit_mapping = {
            'pcs': 'pcs',
            'piece': 'pcs',
            'pieces': 'pcs',
            'unit': 'pcs',
            'units': 'pcs',
            'item': 'pcs',
            'items': 'pcs',
            'kg': 'kg',
            'kilogram': 'kg',
            'kilograms': 'kg',
            'lb': 'lbs',
            'pound': 'lbs',
            'pounds': 'lbs',
            'g': 'g',
            'gram': 'g',
            'grams': 'g',
            'm': 'm',
            'meter': 'm',
            'meters': 'm',
            'cm': 'cm',
            'centimeter': 'cm',
            'centimeters': 'cm',
            'mm': 'mm',
            'millimeter': 'mm',
            'millimeters': 'mm',
            'l': 'L',
            'liter': 'L',
            'liters': 'L',
            'ml': 'mL',
            'milliliter': 'mL',
            'milliliters': 'mL',
            'box': 'box',
            'boxes': 'box',
            'pack': 'pack',
            'packs': 'pack',
            'bottle': 'bottle',
            'bottles': 'bottle',
            'can': 'can',
            'cans': 'can',
            'roll': 'roll',
            'rolls': 'roll',
            'sheet': 'sheet',
            'sheets': 'sheet'
        }
        
        unit_lower = unit.lower().strip()
        
        if unit_lower in unit_mapping:
            return unit_mapping[unit_lower]
        
        # If no match found, return as is
        return unit
    
    def deduplicate_items(self, items: List[InventoryItem]) -> List[InventoryItem]:
        """Remove duplicate inventory items.
        
        Args:
            items: List of inventory items
            
        Returns:
            List with duplicates removed
        """
        self.logger.info(f"Deduplicating {len(items)} items")
        
        seen_items = set()
        unique_items = []
        
        for item in items:
            # Create a key for comparison
            item_key = self._create_item_key(item)
            
            if item_key not in seen_items:
                seen_items.add(item_key)
                unique_items.append(item)
            else:
                self.logger.debug(f"Removing duplicate item: {item.item_name}")
        
        self.logger.info(f"Removed {len(items) - len(unique_items)} duplicate items")
        return unique_items
    
    def _create_item_key(self, item: InventoryItem) -> str:
        """Create a unique key for item comparison.
        
        Args:
            item: Inventory item
            
        Returns:
            Unique key string
        """
        # Use part number if available, otherwise use name and manufacturer
        if item.part_number:
            return f"{item.part_number.lower()}"
        else:
            return f"{item.item_name.lower()}_{item.vendor_name.lower() if item.vendor_name else ''}"
    
    def merge_similar_items(self, items: List[InventoryItem]) -> List[InventoryItem]:
        """Merge items that are likely the same but have different representations.
        
        Args:
            items: List of inventory items
            
        Returns:
            List with similar items merged
        """
        self.logger.info(f"Merging similar items from {len(items)} items")
        
        # Group items by similarity
        groups = self._group_similar_items(items)
        
        # Merge each group
        merged_items = []
        for group in groups:
            if len(group) == 1:
                merged_items.append(group[0])
            else:
                merged_item = self._merge_item_group(group)
                merged_items.append(merged_item)
        
        self.logger.info(f"Merged into {len(merged_items)} items")
        return merged_items
    
    def _group_similar_items(self, items: List[InventoryItem]) -> List[List[InventoryItem]]:
        """Group items that are similar to each other.
        
        Args:
            items: List of inventory items
            
        Returns:
            List of item groups
        """
        groups = []
        processed = set()
        
        for i, item1 in enumerate(items):
            if i in processed:
                continue
            
            group = [item1]
            processed.add(i)
            
            for j, item2 in enumerate(items[i+1:], i+1):
                if j in processed:
                    continue
                
                if self._are_items_similar(item1, item2):
                    group.append(item2)
                    processed.add(j)
            
            groups.append(group)
        
        return groups
    
    def _are_items_similar(self, item1: InventoryItem, item2: InventoryItem) -> bool:
        """Check if two items are similar enough to merge.
        
        Args:
            item1: First inventory item
            item2: Second inventory item
            
        Returns:
            True if items are similar
        """
        # Check if they have the same part number
        if item1.part_number and item2.part_number:
            if item1.part_number.lower() == item2.part_number.lower():
                return True
        
        # Check if they have similar names
        name1 = item1.item_name.lower()
        name2 = item2.item_name.lower()
        
        # Simple similarity check (can be improved with more sophisticated algorithms)
        if name1 in name2 or name2 in name1:
            return True
        
        # Check if they have the same manufacturer and similar names
        if (item1.vendor_name and item2.vendor_name and 
            item1.vendor_name.lower() == item2.vendor_name.lower()):
            
            # Check for common words in names
            words1 = set(name1.split())
            words2 = set(name2.split())
            common_words = words1.intersection(words2)
            
            if len(common_words) >= 2:  # At least 2 common words
                return True
        
        return False
    
    def _merge_item_group(self, group: List[InventoryItem]) -> InventoryItem:
        """Merge a group of similar items into one.
        
        Args:
            group: List of similar inventory items
            
        Returns:
            Merged inventory item
        """
        if not group:
            raise ValueError("Cannot merge empty group")
        
        if len(group) == 1:
            return group[0]
        
        # Use the first item as base
        merged = group[0]
        
        # Sum quantities
        total_quantity = sum(item.quantity for item in group if item.quantity)
        
        # Calculate average unit price
        prices = [item.unit_price for item in group if item.unit_price and item.unit_price > 0]
        avg_price = sum(prices) / len(prices) if prices else 0.0
        
        # Combine descriptions
        descriptions = [item.description for item in group if item.description]
        combined_description = "; ".join(descriptions) if descriptions else ""
        
        # Create merged item
        merged_item = InventoryItem(
            item_name=merged.item_name,
            description=combined_description,
            quantity=total_quantity,
            unit_price=avg_price,
            category=merged.category,
            vendor_name=merged.vendor_name,
            part_number=merged.part_number,
            sku=merged.part_number,
            status=merged.status
        )
        
        return merged_item 