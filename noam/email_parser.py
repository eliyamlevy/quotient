import email
from email import policy
import base64
import re
from dataclasses import dataclass
from typing import List, Dict, Any, Union

def convert_html_tables_to_text(html_content: str) -> str:
    """Convert HTML tables to structured text format for better AI processing"""
    if not html_content:
        return html_content
    
    print(f"Processing HTML content for tables, length: {len(html_content)}")
    
    # More robust table detection - look for various table patterns
    # Microsoft Word/Outlook often uses complex table structures
    table_patterns = [
        r'<table[^>]*>(.*?)</table>',
        r'<table[^>]*>.*?</table>',
        r'<tr[^>]*>.*?</tr>',  # Sometimes tables are just rows without table tags
    ]
    
    tables_found = []
    for pattern in table_patterns:
        tables = re.findall(pattern, html_content, re.DOTALL | re.IGNORECASE)
        if tables:
            tables_found.extend(tables)
            print(f"Found {len(tables)} potential table structures with pattern: {pattern}")
    
    if not tables_found:
        print("No tables found, returning original content")
        return html_content
    
    # Process each table
    result = html_content
    for i, table_html in enumerate(tables_found):
        print(f"Processing table {i+1}, length: {len(table_html)}")
        
        # Extract rows - be more flexible with row detection
        row_patterns = [
            r'<tr[^>]*>(.*?)</tr>',
            r'<td[^>]*>.*?</td>',  # Sometimes rows are just td elements
        ]
        
        rows = []
        for pattern in row_patterns:
            found_rows = re.findall(pattern, table_html, re.DOTALL | re.IGNORECASE)
            if found_rows:
                rows.extend(found_rows)
                print(f"Found {len(found_rows)} rows with pattern: {pattern}")
        
        if not rows:
            print(f"No rows found in table {i+1}")
            continue
        
        # Convert table to structured text
        table_text = f"\n[TABLE {i+1}]\n"
        
        for row_idx, row_html in enumerate(rows):
            # Extract cells - be more flexible
            cell_patterns = [
                r'<(?:th|td)[^>]*>(.*?)</(?:th|td)>',
                r'<td[^>]*>(.*?)</td>',
                r'<th[^>]*>(.*?)</th>',
            ]
            
            cells = []
            for pattern in cell_patterns:
                found_cells = re.findall(pattern, row_html, re.DOTALL | re.IGNORECASE)
                if found_cells:
                    cells.extend(found_cells)
                    break  # Use first pattern that finds cells
            
            if cells:
                print(f"Row {row_idx + 1}: Found {len(cells)} cells")
                # Clean up cell content (remove HTML tags)
                clean_cells = []
                for cell in cells:
                    # Remove HTML tags
                    clean_cell = re.sub(r'<[^>]+>', '', cell)
                    # Clean up whitespace and special characters
                    clean_cell = re.sub(r'\s+', ' ', clean_cell)
                    clean_cell = re.sub(r'&nbsp;', ' ', clean_cell)
                    clean_cell = clean_cell.strip()
                    if clean_cell:  # Only add non-empty cells
                        clean_cells.append(clean_cell)
                
                if clean_cells:
                    # Join cells with | separator
                    table_text += " | ".join(clean_cells) + "\n"
                    
                    # Add separator line after header row
                    if row_idx == 0:
                        separator_length = len(" | ".join(clean_cells))
                        table_text += "-" * separator_length + "\n"
        
        table_text += "[/TABLE]\n"
        print(f"Generated table text: {table_text[:200]}...")
        
        # Replace the original table with structured text
        # Be more careful about replacement to avoid partial matches
        result = result.replace(table_html, table_text, 1)
    
    # Clean up any remaining HTML tags and normalize whitespace
    result = re.sub(r'<[^>]+>', '', result)
    result = re.sub(r'&nbsp;', ' ', result)
    result = re.sub(r'\s+', ' ', result)
    result = result.strip()
    
    # Remove Microsoft Word/Outlook CSS styling
    result = re.sub(r'v\\:\* \{behavior:url\(#default#VML\);\}.*?\.shape \{behavior:url\(#default#VML\);\}', '', result, flags=re.DOTALL)
    result = re.sub(r'[a-zA-Z]+\\:\* \{behavior:url\(#default#[A-Z]+\);\}', '', result)
    
    # Clean up any remaining artifacts
    result = re.sub(r'\s+', ' ', result)
    result = result.strip()
    
    print(f"Final processed content length: {len(result)}")
    print(f"Final content preview: {result[:500]}...")
    
    return result

@dataclass
class Email:
    header: Dict[str, Any]
    body: str  # Processed text for AI
    html_body: str  # Original HTML for display
    attachments: List[Dict[str, str]]
    inline_images: List[Dict[str, str]]

def parse_email(file_path: str) -> Email:
    with open(file_path, 'r', encoding='utf-8') as f:
        msg = email.message_from_file(f, policy=policy.default)
    
    # Extract headers
    header = dict(msg.items())
    
    # Extract body - prioritize HTML for better table formatting
    body = ""
    html_body = ""
    plain_body = ""
    
    if msg.is_multipart():
        for part in msg.walk():
            content_type = part.get_content_type()
            print(f"Found content type: {content_type}")
            if content_type == "text/html":
                payload = part.get_payload(decode=True)
                if payload and isinstance(payload, bytes):
                    html_body = payload.decode('utf-8', errors='ignore')
                    print(f"Found HTML content, length: {len(html_body)}")
            elif content_type == "text/plain":
                payload = part.get_payload(decode=True)
                if payload and isinstance(payload, bytes):
                    plain_body = payload.decode('utf-8', errors='ignore')
                    print(f"Found plain text content, length: {len(plain_body)}")
    else:
        content_type = msg.get_content_type()
        payload = msg.get_payload(decode=True)
        if payload and isinstance(payload, bytes):
            if content_type == "text/html":
                html_body = payload.decode('utf-8', errors='ignore')
            else:
                plain_body = payload.decode('utf-8', errors='ignore')
    
    # Store original HTML for display
    original_html = html_body if html_body else plain_body
    
    # Use HTML if available, otherwise fall back to plain text
    if html_body:
        print("Using HTML content and converting tables to structured text")
        # Convert HTML tables to structured text for better AI processing
        body = convert_html_tables_to_text(html_body)
    else:
        print("Using plain text content")
        body = plain_body
    
    print(f"Final body length: {len(body)}")
    print(f"Body preview: {body[:200]}...")
    
    # Extract attachments
    attachments = []
    inline_images = []
    for part in msg.walk():
        content_disposition = part.get_content_disposition()
        content_type = part.get_content_type()
        
        # Debug output
        if content_type.startswith('image/'):
            print(f"Found image part: Content-Type={content_type}, Content-Disposition={content_disposition}")
            print(f"  Content-ID: {part.get('Content-ID', 'None')}")
            print(f"  Filename: {part.get_filename()}")
        
        if content_disposition == 'attachment':
            filename = part.get_filename()
            content_id = part.get('Content-ID', '')
            
            # If it has a Content-ID, it's meant to be displayed inline
            if content_id and content_type.startswith('image/'):
                content_id = content_id.strip('<>')
                attachment_data = part.get_payload(decode=True)
                if attachment_data and isinstance(attachment_data, bytes):
                    inline_images.append({
                        'content_id': content_id,
                        'content_type': content_type,
                        'data': base64.b64encode(attachment_data).decode()
                    })
            elif filename:
                # Regular attachment
                attachment_data = part.get_payload(decode=True)
                if attachment_data and isinstance(attachment_data, bytes):
                    attachments.append({
                        'filename': filename,
                        'data': base64.b64encode(attachment_data).decode()
                    })
        elif content_disposition == 'inline' and content_type.startswith('image/'):
            # Handle inline images
            content_id = part.get('Content-ID', '')
            if content_id:
                # Remove angle brackets from Content-ID
                content_id = content_id.strip('<>')
                image_data = part.get_payload(decode=True)
                if image_data and isinstance(image_data, bytes):
                    inline_images.append({
                        'content_id': content_id,
                        'content_type': content_type,
                        'data': base64.b64encode(image_data).decode()
                    })
        elif content_type.startswith('image/') and not content_disposition:
            # Handle images without explicit content disposition (sometimes treated as inline)
            content_id = part.get('Content-ID', '')
            if content_id:
                content_id = content_id.strip('<>')
                image_data = part.get_payload(decode=True)
                if image_data and isinstance(image_data, bytes):
                    inline_images.append({
                        'content_id': content_id,
                        'content_type': content_type,
                        'data': base64.b64encode(image_data).decode()
                    })
    
    return Email(header=header, body=body, html_body=original_html, attachments=attachments, inline_images=inline_images)
