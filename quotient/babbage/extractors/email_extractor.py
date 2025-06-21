"""Email content extraction and parsing."""

import logging
from typing import Dict, Any, Optional, List
from email import message_from_string
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import re

from ...core.config import QuotientConfig
from ...utils.validators import extract_text_from_email


class EmailExtractor:
    """Extract and parse email content."""
    
    def __init__(self, config: QuotientConfig):
        """Initialize the email extractor.
        
        Args:
            config: Configuration object
        """
        self.config = config
        self.logger = logging.getLogger(__name__)
    
    def extract_text(self, email_content: str) -> str:
        """Extract text content from email.
        
        Args:
            email_content: Raw email content
            
        Returns:
            Extracted text content
        """
        self.logger.info("Extracting text from email content")
        
        try:
            return extract_text_from_email(email_content)
            
        except Exception as e:
            self.logger.error(f"Error extracting email text: {str(e)}")
            raise
    
    def parse_email(self, email_content: str) -> Dict[str, Any]:
        """Parse email and extract metadata and content.
        
        Args:
            email_content: Raw email content
            
        Returns:
            Dictionary with parsed email information
        """
        try:
            email = message_from_string(email_content)
            
            # Extract basic metadata
            metadata = {
                'from': email.get('from', ''),
                'to': email.get('to', ''),
                'subject': email.get('subject', ''),
                'date': email.get('date', ''),
                'message_id': email.get('message-id', ''),
                'content_type': email.get_content_type(),
                'headers': dict(email.items())
            }
            
            # Extract text content
            text_content = self.extract_text(email_content)
            
            # Extract attachments info
            attachments = self._extract_attachments_info(email)
            
            return {
                'metadata': metadata,
                'text_content': text_content,
                'attachments': attachments,
                'raw_content': email_content
            }
            
        except Exception as e:
            self.logger.error(f"Error parsing email: {str(e)}")
            raise
    
    def _extract_attachments_info(self, email) -> List[Dict[str, Any]]:
        """Extract information about email attachments.
        
        Args:
            email: Parsed email object
            
        Returns:
            List of attachment information dictionaries
        """
        attachments = []
        
        try:
            if email.is_multipart():
                for part in email.walk():
                    if part.get_filename():
                        attachment_info = {
                            'filename': part.get_filename(),
                            'content_type': part.get_content_type(),
                            'size': len(part.get_payload(decode=True)) if part.get_payload(decode=True) else 0,
                            'content_disposition': part.get('content-disposition', '')
                        }
                        attachments.append(attachment_info)
                        
        except Exception as e:
            self.logger.warning(f"Error extracting attachment info: {str(e)}")
        
        return attachments
    
    def extract_contact_info(self, email_content: str) -> Dict[str, str]:
        """Extract contact information from email.
        
        Args:
            email_content: Raw email content
            
        Returns:
            Dictionary with contact information
        """
        try:
            email = message_from_string(email_content)
            
            contact_info = {}
            
            # Extract from email headers
            contact_info['from_email'] = self._extract_email_address(email.get('from', ''))
            contact_info['to_email'] = self._extract_email_address(email.get('to', ''))
            contact_info['reply_to'] = self._extract_email_address(email.get('reply-to', ''))
            
            # Extract from email body
            text_content = self.extract_text(email_content)
            contact_info.update(self._extract_contact_from_text(text_content))
            
            return contact_info
            
        except Exception as e:
            self.logger.error(f"Error extracting contact info: {str(e)}")
            return {}
    
    def _extract_email_address(self, email_string: str) -> str:
        """Extract email address from email string.
        
        Args:
            email_string: Email string (e.g., "John Doe <john@example.com>")
            
        Returns:
            Extracted email address
        """
        if not email_string:
            return ""
        
        # Pattern to match email addresses
        email_pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
        match = re.search(email_pattern, email_string)
        
        return match.group(0) if match else ""
    
    def _extract_contact_from_text(self, text: str) -> Dict[str, str]:
        """Extract contact information from text content.
        
        Args:
            text: Text content
            
        Returns:
            Dictionary with contact information
        """
        contact_info = {}
        
        # Phone patterns
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
        
        # Website patterns
        website_pattern = r'\bhttps?://[^\s]+\b'
        websites = re.findall(website_pattern, text)
        if websites:
            contact_info['website'] = websites[0]
        
        # Company name patterns (simple heuristic)
        company_patterns = [
            r'\b[A-Z][a-z]+(?:\s+[A-Z][a-z]+)*\s+(?:Inc|Corp|LLC|Ltd|Company|Co)\b',
            r'\b[A-Z][a-z]+(?:\s+[A-Z][a-z]+)*\s+(?:Technologies|Systems|Solutions|Group)\b'
        ]
        
        for pattern in company_patterns:
            companies = re.findall(pattern, text)
            if companies:
                contact_info['company'] = companies[0]
                break
        
        return contact_info
    
    def is_quote_email(self, email_content: str) -> bool:
        """Check if email contains quote information.
        
        Args:
            email_content: Raw email content
            
        Returns:
            True if email likely contains quote information
        """
        try:
            text_content = self.extract_text(email_content).lower()
            
            # Keywords that suggest quote content
            quote_keywords = [
                'quote', 'quotation', 'pricing', 'price', 'cost', 'estimate',
                'invoice', 'order', 'purchase', 'item', 'product', 'part',
                'quantity', 'unit price', 'total', 'amount', 'vendor',
                'supplier', 'manufacturer', 'specifications', 'specs'
            ]
            
            # Check for quote-related keywords
            keyword_count = sum(1 for keyword in quote_keywords if keyword in text_content)
            
            # Check for price patterns
            price_patterns = [
                r'\$\d+\.?\d*',  # $123.45
                r'\d+\.?\d*\s*(?:USD|dollars?|cents?)',  # 123.45 USD
                r'total.*\$\d+\.?\d*',  # total $123.45
            ]
            
            price_count = sum(1 for pattern in price_patterns if re.search(pattern, text_content))
            
            # Consider it a quote email if we find enough indicators
            return keyword_count >= 3 or price_count >= 2
            
        except Exception as e:
            self.logger.error(f"Error checking if email is quote: {str(e)}")
            return False
    
    def extract_quote_sections(self, email_content: str) -> List[Dict[str, Any]]:
        """Extract potential quote sections from email.
        
        Args:
            email_content: Raw email content
            
        Returns:
            List of quote sections
        """
        try:
            text_content = self.extract_text(email_content)
            lines = text_content.split('\n')
            
            quote_sections = []
            current_section = []
            in_quote_section = False
            
            for line in lines:
                line = line.strip()
                
                # Check if line contains quote indicators
                if self._is_quote_line(line):
                    if not in_quote_section:
                        in_quote_section = True
                        current_section = []
                    current_section.append(line)
                else:
                    if in_quote_section and current_section:
                        quote_sections.append({
                            'content': '\n'.join(current_section),
                            'line_count': len(current_section)
                        })
                        current_section = []
                        in_quote_section = False
            
            # Add final section if exists
            if in_quote_section and current_section:
                quote_sections.append({
                    'content': '\n'.join(current_section),
                    'line_count': len(current_section)
                })
            
            return quote_sections
            
        except Exception as e:
            self.logger.error(f"Error extracting quote sections: {str(e)}")
            return []
    
    def _is_quote_line(self, line: str) -> bool:
        """Check if a line contains quote information.
        
        Args:
            line: Text line
            
        Returns:
            True if line contains quote information
        """
        line_lower = line.lower()
        
        # Check for price patterns
        price_patterns = [
            r'\$\d+\.?\d*',
            r'\d+\.?\d*\s*(?:USD|dollars?|cents?)',
        ]
        
        has_price = any(re.search(pattern, line_lower) for pattern in price_patterns)
        
        # Check for quantity patterns
        quantity_patterns = [
            r'\b\d+\s*(?:pcs?|pieces?|units?|items?)\b',
            r'qty\s*:\s*\d+',
            r'quantity\s*:\s*\d+',
        ]
        
        has_quantity = any(re.search(pattern, line_lower) for pattern in quantity_patterns)
        
        # Check for product/part patterns
        product_patterns = [
            r'\b(?:part|item|product|sku|model|description)\s*:',
            r'\b[A-Z]{2,}\d+[A-Z0-9]*\b',  # Part numbers like ABC123
        ]
        
        has_product = any(re.search(pattern, line_lower) for pattern in product_patterns)
        
        return has_price or has_quantity or has_product 