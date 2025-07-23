import email
from email import policy
import base64
from dataclasses import dataclass
from typing import List, Dict, Any, Union

@dataclass
class Email:
    header: Dict[str, Any]
    body: str
    attachments: List[Dict[str, str]]
    inline_images: List[Dict[str, str]]

def parse_email(file_path: str) -> Email:
    with open(file_path, 'r', encoding='utf-8') as f:
        msg = email.message_from_file(f, policy=policy.default)
    
    # Extract headers
    header = dict(msg.items())
    
    # Extract body
    body = ""
    if msg.is_multipart():
        for part in msg.walk():
            if part.get_content_type() == "text/plain":
                payload = part.get_payload(decode=True)
                if payload and isinstance(payload, bytes):
                    body = payload.decode('utf-8', errors='ignore')
                break
    else:
        payload = msg.get_payload(decode=True)
        if payload and isinstance(payload, bytes):
            body = payload.decode('utf-8', errors='ignore')
    
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
    
    return Email(header=header, body=body, attachments=attachments, inline_images=inline_images)
