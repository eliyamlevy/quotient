"""Validation utilities for Quotient."""

import os
from pathlib import Path
from typing import List, Tuple, Optional
import re
from email import message_from_string
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart


def validate_file_type(file_path: str, supported_formats: List[str]) -> Tuple[bool, str]:
    """Validate if a file type is supported.
    
    Args:
        file_path: Path to the file
        supported_formats: List of supported file extensions
        
    Returns:
        Tuple of (is_valid, error_message)
    """
    if not os.path.exists(file_path):
        return False, f"File does not exist: {file_path}"
    
    file_extension = Path(file_path).suffix.lower().lstrip('.')
    
    if file_extension not in supported_formats:
        return False, f"Unsupported file type: {file_extension}. Supported: {', '.join(supported_formats)}"
    
    return True, ""


def validate_email_content(email_content: str) -> Tuple[bool, str, Optional[dict]]:
    """Validate and parse email content.
    
    Args:
        email_content: Raw email content
        
    Returns:
        Tuple of (is_valid, error_message, parsed_email)
    """
    try:
        # Try to parse as email
        email = message_from_string(email_content)
        
        # Check if it has basic email structure
        if not email.get('from') and not email.get('to'):
            return False, "Invalid email format: missing from/to headers", None
        
        # Extract email metadata
        metadata = {
            'from': email.get('from', ''),
            'to': email.get('to', ''),
            'subject': email.get('subject', ''),
            'date': email.get('date', ''),
            'content_type': email.get_content_type(),
        }
        
        return True, "", metadata
        
    except Exception as e:
        return False, f"Failed to parse email: {str(e)}", None


def validate_pdf_content(file_path: str) -> Tuple[bool, str]:
    """Validate PDF file content.
    
    Args:
        file_path: Path to the PDF file
        
    Returns:
        Tuple of (is_valid, error_message)
    """
    try:
        import fitz  # PyMuPDF
        
        doc = fitz.open(file_path)
        if doc.page_count == 0:
            return False, "PDF file is empty"
        
        # Check if PDF is corrupted
        if not doc.is_pdf:
            return False, "File is not a valid PDF"
        
        doc.close()
        return True, ""
        
    except ImportError:
        return True, "PyMuPDF not available, skipping PDF validation"
    except Exception as e:
        return False, f"PDF validation failed: {str(e)}"


def validate_image_content(file_path: str) -> Tuple[bool, str]:
    """Validate image file content.
    
    Args:
        file_path: Path to the image file
        
    Returns:
        Tuple of (is_valid, error_message)
    """
    try:
        from PIL import Image
        
        with Image.open(file_path) as img:
            # Check if image can be opened
            img.verify()
        
        return True, ""
        
    except ImportError:
        return True, "Pillow not available, skipping image validation"
    except Exception as e:
        return False, f"Image validation failed: {str(e)}"


def validate_spreadsheet_content(file_path: str) -> Tuple[bool, str]:
    """Validate spreadsheet file content.
    
    Args:
        file_path: Path to the spreadsheet file
        
    Returns:
        Tuple of (is_valid, error_message)
    """
    try:
        import pandas as pd
        
        # Try to read the file
        if file_path.endswith('.csv'):
            pd.read_csv(file_path, nrows=1)  # Just read first row to test
        elif file_path.endswith(('.xls', '.xlsx')):
            pd.read_excel(file_path, nrows=1)  # Just read first row to test
        else:
            return False, f"Unsupported spreadsheet format: {file_path}"
        
        return True, ""
        
    except Exception as e:
        return False, f"Spreadsheet validation failed: {str(e)}"


def validate_file_size(file_path: str, max_size_mb: int = 50) -> Tuple[bool, str]:
    """Validate file size.
    
    Args:
        file_path: Path to the file
        max_size_mb: Maximum file size in MB
        
    Returns:
        Tuple of (is_valid, error_message)
    """
    if not os.path.exists(file_path):
        return False, f"File does not exist: {file_path}"
    
    file_size_mb = os.path.getsize(file_path) / (1024 * 1024)
    
    if file_size_mb > max_size_mb:
        return False, f"File size ({file_size_mb:.2f}MB) exceeds maximum ({max_size_mb}MB)"
    
    return True, ""


def extract_text_from_email(email_content: str) -> str:
    """Extract text content from email.
    
    Args:
        email_content: Raw email content
        
    Returns:
        Extracted text content
    """
    try:
        email = message_from_string(email_content)
        
        # Get text content
        text_content = ""
        
        if email.is_multipart():
            for part in email.walk():
                if part.get_content_type() == "text/plain":
                    text_content += part.get_payload(decode=True).decode('utf-8', errors='ignore')
        else:
            if email.get_content_type() == "text/plain":
                text_content = email.get_payload(decode=True).decode('utf-8', errors='ignore')
        
        return text_content.strip()
        
    except Exception as e:
        # Fallback: return original content
        return email_content


def sanitize_filename(filename: str) -> str:
    """Sanitize filename for safe storage.
    
    Args:
        filename: Original filename
        
    Returns:
        Sanitized filename
    """
    # Remove or replace unsafe characters
    unsafe_chars = r'[<>:"/\\|?*]'
    sanitized = re.sub(unsafe_chars, '_', filename)
    
    # Limit length
    if len(sanitized) > 255:
        name, ext = os.path.splitext(sanitized)
        sanitized = name[:255-len(ext)] + ext
    
    return sanitized 