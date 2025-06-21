"""Formatting utilities for Quotient."""

import re
from typing import Optional, Union, Dict, Any
from decimal import Decimal, InvalidOperation


def format_currency(amount: Union[str, float, int], currency: str = "USD") -> str:
    """Format currency amount.
    
    Args:
        amount: Amount to format
        currency: Currency code (default: USD)
        
    Returns:
        Formatted currency string
    """
    try:
        # Convert to float if string
        if isinstance(amount, str):
            # Remove currency symbols and clean up
            cleaned = re.sub(r'[^\d.,-]', '', amount)
            amount = float(cleaned.replace(',', ''))
        
        # Format based on currency
        if currency == "USD":
            return f"${amount:,.2f}"
        elif currency == "EUR":
            return f"€{amount:,.2f}"
        elif currency == "GBP":
            return f"£{amount:,.2f}"
        else:
            return f"{amount:,.2f} {currency}"
            
    except (ValueError, TypeError):
        return str(amount)


def parse_currency(currency_str: str) -> Optional[float]:
    """Parse currency string to float.
    
    Args:
        currency_str: Currency string to parse
        
    Returns:
        Parsed amount as float, or None if parsing fails
    """
    try:
        # Remove currency symbols and clean up
        cleaned = re.sub(r'[^\d.,-]', '', currency_str)
        
        # Handle different decimal separators
        if ',' in cleaned and '.' in cleaned:
            # European format: 1.234,56
            if cleaned.find(',') > cleaned.find('.'):
                cleaned = cleaned.replace('.', '').replace(',', '.')
            else:
                # US format: 1,234.56
                cleaned = cleaned.replace(',', '')
        elif ',' in cleaned:
            # Check if comma is decimal separator
            parts = cleaned.split(',')
            if len(parts) == 2 and len(parts[1]) <= 2:
                # Likely decimal separator
                cleaned = cleaned.replace(',', '.')
            else:
                # Likely thousands separator
                cleaned = cleaned.replace(',', '')
        
        return float(cleaned)
        
    except (ValueError, TypeError):
        return None


def format_quantity(quantity: Union[str, int, float], unit: str = "") -> str:
    """Format quantity with unit.
    
    Args:
        quantity: Quantity to format
        unit: Unit of measurement
        
    Returns:
        Formatted quantity string
    """
    try:
        if isinstance(quantity, str):
            # Try to extract number from string
            number_match = re.search(r'(\d+(?:\.\d+)?)', quantity)
            if number_match:
                quantity = float(number_match.group(1))
            else:
                return quantity
        
        # Format number
        if isinstance(quantity, float) and quantity.is_integer():
            formatted = f"{int(quantity):,}"
        else:
            formatted = f"{quantity:,.2f}".rstrip('0').rstrip('.')
        
        # Add unit if provided
        if unit:
            return f"{formatted} {unit}"
        else:
            return formatted
            
    except (ValueError, TypeError):
        return str(quantity)


def parse_quantity(quantity_str: str) -> Optional[float]:
    """Parse quantity string to float.
    
    Args:
        quantity_str: Quantity string to parse
        
    Returns:
        Parsed quantity as float, or None if parsing fails
    """
    try:
        # Extract number from string
        number_match = re.search(r'(\d+(?:\.\d+)?)', quantity_str)
        if number_match:
            return float(number_match.group(1))
        return None
        
    except (ValueError, TypeError):
        return None


def format_part_number(part_number: str) -> str:
    """Format part number for consistency.
    
    Args:
        part_number: Part number to format
        
    Returns:
        Formatted part number
    """
    if not part_number:
        return ""
    
    # Remove extra spaces and convert to uppercase
    formatted = re.sub(r'\s+', ' ', part_number.strip()).upper()
    
    # Remove common prefixes/suffixes that might be inconsistent
    prefixes_to_remove = ['PART#', 'PART #', 'P/N', 'PN', 'SKU#', 'SKU #']
    for prefix in prefixes_to_remove:
        if formatted.startswith(prefix):
            formatted = formatted[len(prefix):].strip()
    
    return formatted


def format_vendor_name(vendor_name: str) -> str:
    """Format vendor name for consistency.
    
    Args:
        vendor_name: Vendor name to format
        
    Returns:
        Formatted vendor name
    """
    if not vendor_name:
        return ""
    
    # Title case and clean up
    formatted = re.sub(r'\s+', ' ', vendor_name.strip()).title()
    
    # Handle common abbreviations
    abbreviations = {
        'Inc': 'Inc.',
        'Corp': 'Corp.',
        'Ltd': 'Ltd.',
        'Co': 'Co.',
        'LLC': 'LLC',
        'LLP': 'LLP'
    }
    
    for abbr, replacement in abbreviations.items():
        formatted = re.sub(rf'\b{abbr}\b', replacement, formatted, flags=re.IGNORECASE)
    
    return formatted


def format_description(description: str, max_length: int = 200) -> str:
    """Format description text.
    
    Args:
        description: Description to format
        max_length: Maximum length of description
        
    Returns:
        Formatted description
    """
    if not description:
        return ""
    
    # Clean up whitespace
    formatted = re.sub(r'\s+', ' ', description.strip())
    
    # Truncate if too long
    if len(formatted) > max_length:
        formatted = formatted[:max_length-3] + "..."
    
    return formatted


def extract_contact_info(text: str) -> Dict[str, str]:
    """Extract contact information from text.
    
    Args:
        text: Text to extract contact info from
        
    Returns:
        Dictionary with contact information
    """
    contact_info = {}
    
    # Email pattern
    email_pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
    emails = re.findall(email_pattern, text)
    if emails:
        contact_info['email'] = emails[0]
    
    # Phone pattern (various formats)
    phone_patterns = [
        r'\b\d{3}[-.]?\d{3}[-.]?\d{4}\b',  # 123-456-7890
        r'\b\(\d{3}\)\s*\d{3}[-.]?\d{4}\b',  # (123) 456-7890
        r'\b\d{10}\b',  # 1234567890
    ]
    
    for pattern in phone_patterns:
        phones = re.findall(pattern, text)
        if phones:
            contact_info['phone'] = phones[0]
            break
    
    # Website pattern
    website_pattern = r'\bhttps?://[^\s]+\b'
    websites = re.findall(website_pattern, text)
    if websites:
        contact_info['website'] = websites[0]
    
    return contact_info


def clean_text_for_processing(text: str) -> str:
    """Clean text for AI processing.
    
    Args:
        text: Text to clean
        
    Returns:
        Cleaned text
    """
    if not text:
        return ""
    
    # Remove extra whitespace
    cleaned = re.sub(r'\s+', ' ', text.strip())
    
    # Remove special characters that might interfere with processing
    cleaned = re.sub(r'[^\w\s.,;:!?@#$%&*()\[\]{}<>/\\|`~+=_\-]', '', cleaned)
    
    # Normalize line breaks
    cleaned = cleaned.replace('\n', ' ').replace('\r', ' ')
    
    return cleaned


def format_specifications(specs: Dict[str, Any]) -> str:
    """Format specifications dictionary to string.
    
    Args:
        specs: Specifications dictionary
        
    Returns:
        Formatted specifications string
    """
    if not specs:
        return ""
    
    formatted_parts = []
    for key, value in specs.items():
        if value is not None and value != "":
            formatted_parts.append(f"{key}: {value}")
    
    return "; ".join(formatted_parts) 