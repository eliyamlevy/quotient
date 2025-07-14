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
    for part in msg.walk():
        if part.get_content_disposition() == 'attachment':
            filename = part.get_filename()
            if filename:
                attachment_data = part.get_payload(decode=True)
                if attachment_data and isinstance(attachment_data, bytes):
                    attachments.append({
                        'filename': filename,
                        'data': base64.b64encode(attachment_data).decode()
                    })
    
    return Email(header=header, body=body, attachments=attachments)
