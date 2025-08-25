"""
Test configuration and mock data for EmailDiffusionPipeline tests

Contains sample data, mock responses, and test utilities.
"""

import base64
import json
from typing import Dict, List, Any

# Sample test data
SAMPLE_EMAIL_BODY = """
Dear Team,

Please provide a quote for the following items to be shipped to Huntington Beach, CA.

Items needed:
- AP1-19-111-T: 6 units - Panel Filler, 1U, Color 111-T
- AP3-19-111-T: 10 units - Panel Filler, 2U, Color 111-T

Clauses: C103, E223, H202

Best regards,
John Smith
Procurement Manager
"""

SAMPLE_IMAGE_DATA = {
    'content_id': 'img_001',
    'data': base64.b64encode(b'fake_image_data_for_testing').decode('utf-8'),
    'content_type': 'image/png'
}

SAMPLE_TABLE_TEXT = """
Item | Part Number | Quantity | U/M | Description
1    | AP1-19-111-T | 6      | EA  | Panel - Filler, 1U, Color 111-T
2    | AP3-19-111-T | 10     | EA  | Panel - Filler, 2U, Color 111-T
"""

# Mock API responses
MOCK_QUOTE_EXTRACTION_RESPONSE = {
    'message': {
        'content': json.dumps({
            'shipping_location': 'Huntington Beach, CA',
            'client_name': 'John Smith',
            'clauses': ['C103', 'E223', 'H202']
        })
    }
}

MOCK_ITEM_EXTRACTION_RESPONSE = {
    'message': {
        'content': json.dumps([
            {
                'part_number': 'AP1-19-111-T',
                'quantity': 6,
                'description': 'Panel - Filler, 1U, Color 111-T',
                'unit': 'EA',
                'price': None,
                'lead_time': None,
                'rfp_number': None
            },
            {
                'part_number': 'AP3-19-111-T',
                'quantity': 10,
                'description': 'Panel - Filler, 2U, Color 111-T',
                'unit': 'EA',
                'price': None,
                'lead_time': None,
                'rfp_number': None
            }
        ])
    }
}

MOCK_IMAGE_TEXT_RESPONSE = {
    'response': 'Extracted text from image: Item | Part Number | Quantity | U/M | Description'
}

# Test email structures
TEST_EMAIL_STRUCTURES = {
    'simple': {
        'body': 'Simple email with basic text',
        'inline_images': []
    },
    'with_images': {
        'body': 'Email with embedded images',
        'inline_images': [SAMPLE_IMAGE_DATA]
    },
    'with_tables': {
        'body': SAMPLE_EMAIL_BODY,
        'inline_images': [SAMPLE_IMAGE_DATA]
    },
    'empty': {
        'body': '',
        'inline_images': []
    },
    'large': {
        'body': 'Test ' * 10000,  # 50,000 characters
        'inline_images': []
    }
}

# Expected test results
EXPECTED_QUOTE_INFO = {
    'shipping_location': 'Huntington Beach, CA',
    'client_name': 'John Smith',
    'clauses': ['C103', 'E223', 'H202']
}

EXPECTED_ITEMS = [
    {
        'part_number': 'AP1-19-111-T',
        'quantity': 6,
        'description': 'Panel - Filler, 1U, Color 111-T',
        'unit': 'EA',
        'price': None,
        'lead_time': None,
        'rfp_number': None
    },
    {
        'part_number': 'AP3-19-111-T',
        'quantity': 10,
        'description': 'Panel - Filler, 2U, Color 111-T',
        'unit': 'EA',
        'price': None,
        'lead_time': None,
        'rfp_number': None
    }
]

# Error scenarios
ERROR_SCENARIOS = {
    'api_failure': Exception("API connection failed"),
    'malformed_json': '{"incomplete": "json"',
    'empty_response': '',
    'invalid_json': '{"key": "value",}',  # Trailing comma
    'extra_text': '{"key": "value"} extra content',
    'unquoted_key': '{key: "value"}'
}

# Test utilities
def create_mock_email_data(body: str, inline_images: List[Dict[str, str]]):
    """Create a mock EmailData object for testing"""
    from unittest.mock import Mock
    from email_parser import EmailData
    
    mock_email = Mock(spec=EmailData)
    mock_email.body = body
    mock_email.inline_images = inline_images
    return mock_email

def create_mock_api_response(content: str, status_code: int = 200):
    """Create a mock API response for testing"""
    from unittest.mock import Mock
    
    mock_response = Mock()
    mock_response.json.return_value = {'message': {'content': content}}
    mock_response.status_code = status_code
    mock_response.raise_for_status.return_value = None
    return mock_response

def create_mock_failed_api_response(error: Exception):
    """Create a mock API response that raises an error"""
    from unittest.mock import Mock
    
    mock_response = Mock()
    mock_response.side_effect = error
    return mock_response

# Test data validation
def validate_quote_info(quote_info, expected: Dict[str, Any]):
    """Validate that quote info matches expected values"""
    assert quote_info.shipping_location == expected['shipping_location']
    assert quote_info.client_name == expected['client_name']
    assert quote_info.clauses == expected['clauses']

def validate_items(items, expected: List[Dict[str, Any]]):
    """Validate that items match expected values"""
    assert len(items) == len(expected)
    
    for i, (item, expected_item) in enumerate(zip(items, expected)):
        assert item.part_number == expected_item['part_number'], f"Item {i} part number mismatch"
        assert item.quantity == expected_item['quantity'], f"Item {i} quantity mismatch"
        assert item.description == expected_item['description'], f"Item {i} description mismatch"
        assert item.unit == expected_item['unit'], f"Item {i} unit mismatch"

def validate_image_text_result(result, expected_content_id: str):
    """Validate that image text result has correct structure"""
    assert hasattr(result, 'content_id')
    assert hasattr(result, 'text')
    assert hasattr(result, 'table_structure')
    assert result.content_id == expected_content_id
    assert isinstance(result.text, str)
    assert isinstance(result.table_structure, str)

