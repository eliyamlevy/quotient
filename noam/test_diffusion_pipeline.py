"""
Unit tests for EmailDiffusionPipeline

Tests each filter and method with proper mocking and edge cases.
"""

import unittest
import json
import base64
from unittest.mock import Mock, patch, MagicMock
from unittest.mock import call
import tempfile
import os
from io import BytesIO

from email_diffusion_pipeline import (
    EmailDiffusionPipeline,
    ImageTextResult,
    QuoteLevelInfo,
    ItemMetadata,
    ProcessedQuote
)
from email_parser import EmailData


class TestImageTextResult(unittest.TestCase):
    """Test ImageTextResult dataclass"""
    
    def test_image_text_result_creation(self):
        """Test creating ImageTextResult with all fields"""
        result = ImageTextResult(
            content_id="img_001",
            text="Sample text from image",
            table_structure="┌─┐\n│A│\n└─┘"
        )
        
        self.assertEqual(result.content_id, "img_001")
        self.assertEqual(result.text, "Sample text from image")
        self.assertEqual(result.table_structure, "┌─┐\n│A│\n└─┘")
    
    def test_image_text_result_defaults(self):
        """Test ImageTextResult with default values"""
        result = ImageTextResult(content_id="img_001", text="Sample text")
        
        self.assertEqual(result.content_id, "img_001")
        self.assertEqual(result.text, "Sample text")
        self.assertEqual(result.table_structure, "")


class TestQuoteLevelInfo(unittest.TestCase):
    """Test QuoteLevelInfo dataclass"""
    
    def test_quote_level_info_creation(self):
        """Test creating QuoteLevelInfo with all fields"""
        info = QuoteLevelInfo(
            shipping_location="Huntington Beach, CA",
            client_name="John Smith",
            clauses=["C103", "E223", "H202"]
        )
        
        self.assertEqual(info.shipping_location, "Huntington Beach, CA")
        self.assertEqual(info.client_name, "John Smith")
        self.assertEqual(info.clauses, ["C103", "E223", "H202"])
    
    def test_quote_level_info_defaults(self):
        """Test QuoteLevelInfo with default values"""
        info = QuoteLevelInfo()
        
        self.assertIsNone(info.shipping_location)
        self.assertIsNone(info.client_name)
        self.assertEqual(info.clauses, [])


class TestItemMetadata(unittest.TestCase):
    """Test ItemMetadata dataclass"""
    
    def test_item_metadata_creation(self):
        """Test creating ItemMetadata with all fields"""
        item = ItemMetadata(
            part_number="AP1-19-111-T",
            quantity=6,
            description="Panel - Filler, 1U, Color 111-T",
            unit="EA",
            price="$25.50",
            lead_time="2 weeks",
            rfp_number="AC252347-001",
            item_number="1"
        )
        
        self.assertEqual(item.part_number, "AP1-19-111-T")
        self.assertEqual(item.quantity, 6)
        self.assertEqual(item.description, "Panel - Filler, 1U, Color 111-T")
        self.assertEqual(item.unit, "EA")
        self.assertEqual(item.price, "$25.50")
        self.assertEqual(item.lead_time, "2 weeks")
        self.assertEqual(item.rfp_number, "AC252347-001")
        self.assertEqual(item.item_number, "1")
    
    def test_item_metadata_defaults(self):
        """Test ItemMetadata with default values"""
        item = ItemMetadata(
            part_number="TEST-001",
            quantity=1,
            description="Test item"
        )
        
        self.assertEqual(item.part_number, "TEST-001")
        self.assertEqual(item.quantity, 1)
        self.assertEqual(item.description, "Test item")
        self.assertEqual(item.unit, "EA")
        self.assertIsNone(item.price)
        self.assertIsNone(item.lead_time)
        self.assertIsNone(item.rfp_number)
        self.assertIsNone(item.item_number)


class TestProcessedQuote(unittest.TestCase):
    """Test ProcessedQuote dataclass"""
    
    def test_processed_quote_creation(self):
        """Test creating ProcessedQuote with all fields"""
        quote_info = QuoteLevelInfo(
            shipping_location="Test Location",
            client_name="Test Client",
            clauses=["C103"]
        )
        
        items = [
            ItemMetadata(
                part_number="TEST-001",
                quantity=1,
                description="Test item"
            )
        ]
        
        image_texts = [
            ImageTextResult(
                content_id="img_001",
                text="Test image text"
            )
        ]
        
        quote = ProcessedQuote(
            quote_info=quote_info,
            items=items,
            raw_text="Test email body",
            image_texts=image_texts
        )
        
        self.assertEqual(quote.quote_info, quote_info)
        self.assertEqual(quote.items, items)
        self.assertEqual(quote.raw_text, "Test email body")
        self.assertEqual(quote.image_texts, image_texts)


class TestEmailDiffusionPipeline(unittest.TestCase):
    """Test EmailDiffusionPipeline class"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.pipeline = EmailDiffusionPipeline(
            model_name="test-model",
            api_url="http://localhost:11434"
        )
        
        # Mock email data
        self.mock_email = Mock(spec=EmailData)
        self.mock_email.body = "Test email body with inventory items"
        self.mock_email.inline_images = [
            {
                'content_id': 'img_001',
                'data': base64.b64encode(b'fake_image_data').decode('utf-8'),
                'content_type': 'image/png'
            }
        ]
    
    def test_pipeline_initialization(self):
        """Test pipeline initialization with different API URLs"""
        # Test with trailing slash
        pipeline1 = EmailDiffusionPipeline(api_url="http://localhost:11434/")
        self.assertEqual(pipeline1.api_url, "http://localhost:11434")
        
        # Test with /v1 suffix
        pipeline2 = EmailDiffusionPipeline(api_url="http://localhost:11434/v1")
        self.assertEqual(pipeline2.api_url, "http://localhost:11434")
        
        # Test with None
        pipeline3 = EmailDiffusionPipeline(api_url=None)
        self.assertEqual(pipeline3.api_url, "http://localhost:11434")
    
    @patch('email_diffusion_pipeline.parse_email')
    @patch.object(EmailDiffusionPipeline, '_convert_images_to_text')
    @patch.object(EmailDiffusionPipeline, '_extract_quote_level_info')
    @patch.object(EmailDiffusionPipeline, '_extract_item_metadata')
    @patch.object(EmailDiffusionPipeline, '_compile_result_matrix')
    def test_process_email_pipeline_flow(self, mock_compile, mock_extract_items, 
                                       mock_extract_quote, mock_convert_images, mock_parse):
        """Test the complete pipeline flow"""
        # Setup mocks
        mock_parse.return_value = self.mock_email
        mock_convert_images.return_value = [Mock(spec=ImageTextResult)]
        mock_extract_quote.return_value = Mock(spec=QuoteLevelInfo)
        mock_extract_items.return_value = [Mock(spec=ItemMetadata)]
        mock_compile.return_value = Mock(spec=ProcessedQuote)
        
        # Call the method
        result = self.pipeline.process_email("test_email.eml")
        
        # Verify the flow
        mock_parse.assert_called_once_with("test_email.eml")
        mock_convert_images.assert_called_once_with(self.mock_email.inline_images)
        mock_extract_quote.assert_called_once()
        mock_extract_items.assert_called_once()
        mock_compile.assert_called_once()
        
        self.assertEqual(result, mock_compile.return_value)
    
    @patch('requests.post')
    def test_convert_images_to_text_success(self, mock_post):
        """Test successful image-to-text conversion"""
        # Mock successful API response
        mock_response = Mock()
        mock_response.json.return_value = {'response': 'Extracted text from image'}
        mock_response.raise_for_status.return_value = None
        mock_post.return_value = mock_response
        
        images = [
            {
                'content_id': 'img_001',
                'data': base64.b64encode(b'fake_image_data').decode('utf-8')
            }
        ]
        
        results = self.pipeline._convert_images_to_text(images)
        
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0].content_id, 'img_001')
        self.assertEqual(results[0].text, 'Extracted text from image')
        self.assertIsInstance(results[0], ImageTextResult)
    
    @patch('requests.post')
    def test_convert_images_to_text_failure(self, mock_post):
        """Test image-to-text conversion failure handling"""
        # Mock API failure
        mock_post.side_effect = Exception("API Error")
        
        images = [
            {
                'content_id': 'img_001',
                'data': base64.b64encode(b'fake_image_data').decode('utf-8')
            }
        ]
        
        results = self.pipeline._convert_images_to_text(images)
        
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0].content_id, 'img_001')
        self.assertIn('IMAGE_PROCESSING_FAILED', results[0].text)
    
    def test_extract_table_structure(self):
        """Test table structure extraction"""
        # Test with table-like text
        table_text = "Item | Part Number | Quantity\n1    | TEST-001    | 5"
        structure = self.pipeline._extract_table_structure(table_text)
        
        self.assertIn("┌", structure)
        self.assertIn("│", structure)
        self.assertIn("└", structure)
        
        # Test with non-table text
        regular_text = "This is just regular text without tables"
        structure = self.pipeline._extract_table_structure(regular_text)
        
        self.assertEqual(structure, "")
    
    def test_combine_text_and_images(self):
        """Test combining email text with image text"""
        email_body = "Original email content"
        image_texts = [
            ImageTextResult(
                content_id="img_001",
                text="Image text content",
                table_structure="┌─┐\n│A│\n└─┘"
            )
        ]
        
        combined = self.pipeline._combine_text_and_images(email_body, image_texts)
        
        self.assertIn("Original email content", combined)
        self.assertIn("Image text content", combined)
        self.assertIn("┌─┐", combined)
        self.assertIn("[IMAGE: img_001]", combined)
    
    @patch('requests.post')
    def test_extract_quote_level_info_success(self, mock_post):
        """Test successful quote-level information extraction"""
        # Mock successful API response
        mock_response = Mock()
        mock_response.json.return_value = {
            'message': {
                'content': '{"shipping_location": "Test Location", "client_name": "Test Client", "clauses": ["C103"]}'
            }
        }
        mock_response.raise_for_status.return_value = None
        mock_post.return_value = mock_response
        
        text = "Test email text for extraction"
        result = self.pipeline._extract_quote_level_info(text)
        
        self.assertIsInstance(result, QuoteLevelInfo)
        self.assertEqual(result.shipping_location, "Test Location")
        self.assertEqual(result.client_name, "Test Client")
        self.assertEqual(result.clauses, ["C103"])
    
    @patch('requests.post')
    def test_extract_quote_level_info_json_code_block(self, mock_post):
        """Test quote extraction with JSON in code block"""
        mock_response = Mock()
        mock_response.json.return_value = {
            'message': {
                'content': '```json\n{"shipping_location": "Test", "client_name": "Client", "clauses": []}\n```'
            }
        }
        mock_response.raise_for_status.return_value = None
        mock_post.return_value = mock_response
        
        text = "Test email text"
        result = self.pipeline._extract_quote_level_info(text)
        
        self.assertEqual(result.shipping_location, "Test")
        self.assertEqual(result.client_name, "Client")
        self.assertEqual(result.clauses, [])
    
    @patch('requests.post')
    def test_extract_quote_level_info_failure(self, mock_post):
        """Test quote extraction failure handling"""
        mock_post.side_effect = Exception("API Error")
        
        text = "Test email text"
        
        with self.assertRaises(RuntimeError):
            self.pipeline._extract_quote_level_info(text)
    
    def test_clean_json_string(self):
        """Test JSON string cleaning functionality"""
        # Test trailing comma removal
        dirty_json = '{"key": "value",}'
        cleaned = self.pipeline._clean_json_string(dirty_json)
        self.assertEqual(cleaned, '{"key": "value"}')
        
        # Test trailing text removal
        dirty_json = '{"key": "value"} extra text'
        cleaned = self.pipeline._clean_json_string(dirty_json)
        self.assertEqual(cleaned, '{"key": "value"}')
        
        # Test quote fixing
        dirty_json = '{key: "value"}'
        cleaned = self.pipeline._clean_json_string(dirty_json)
        self.assertEqual(cleaned, '{ "key": "value"}')
    
    @patch('requests.post')
    def test_extract_item_metadata_success(self, mock_post):
        """Test successful item metadata extraction"""
        # Mock successful API response
        mock_response = Mock()
        mock_response.json.return_value = {
            'message': {
                'content': '[{"part_number": "TEST-001", "quantity": 5, "description": "Test item", "unit": "EA"}]'
            }
        }
        mock_response.raise_for_status.return_value = None
        mock_post.return_value = mock_response
        
        text = "Test email text with items"
        quote_info = QuoteLevelInfo(
            shipping_location="Test Location",
            client_name="Test Client",
            clauses=["C103"]
        )
        
        results = self.pipeline._extract_item_metadata(text, quote_info)
        
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0].part_number, "TEST-001")
        self.assertEqual(results[0].quantity, 5)
        self.assertEqual(results[0].description, "Test item")
        self.assertEqual(results[0].unit, "EA")
    
    @patch('requests.post')
    def test_extract_item_metadata_json_array_code_block(self, mock_post):
        """Test item extraction with JSON array in code block"""
        mock_response = Mock()
        mock_response.json.return_value = {
            'message': {
                'content': '```json\n[{"part_number": "TEST-001", "quantity": 1, "description": "Test"}]\n```'
            }
        }
        mock_response.raise_for_status.return_value = None
        mock_post.return_value = mock_response
        
        text = "Test email text"
        quote_info = QuoteLevelInfo()
        
        results = self.pipeline._extract_item_metadata(text, quote_info)
        
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0].part_number, "TEST-001")
    
    @patch('requests.post')
    def test_extract_item_metadata_failure(self, mock_post):
        """Test item extraction failure handling"""
        mock_post.side_effect = Exception("API Error")
        
        text = "Test email text"
        quote_info = QuoteLevelInfo()
        
        with self.assertRaises(RuntimeError):
            self.pipeline._extract_item_metadata(text, quote_info)
    
    def test_compile_result_matrix(self):
        """Test final result matrix compilation"""
        quote_info = QuoteLevelInfo(
            shipping_location="Test Location",
            client_name="Test Client",
            clauses=["C103"]
        )
        
        items = [
            ItemMetadata(
                part_number="TEST-001",
                quantity=1,
                description="Test item"
            )
        ]
        
        raw_text = "Test email body"
        image_texts = [
            ImageTextResult(
                content_id="img_001",
                text="Test image text"
            )
        ]
        
        result = self.pipeline._compile_result_matrix(
            quote_info, items, raw_text, image_texts
        )
        
        self.assertIsInstance(result, ProcessedQuote)
        self.assertEqual(result.quote_info, quote_info)
        self.assertEqual(result.items, items)
        self.assertEqual(result.raw_text, raw_text)
        self.assertEqual(result.image_texts, image_texts)


class TestEmailDiffusionPipelineIntegration(unittest.TestCase):
    """Integration tests for the pipeline"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.pipeline = EmailDiffusionPipeline(
            model_name="test-model",
            api_url="http://localhost:11434"
        )
    
    @patch('email_diffusion_pipeline.parse_email')
    @patch('requests.post')
    def test_full_pipeline_integration(self, mock_post, mock_parse):
        """Test full pipeline integration with mocked dependencies"""
        # Mock email parsing
        mock_email = Mock(spec=EmailData)
        mock_email.body = "Test email with inventory"
        mock_email.inline_images = []
        mock_parse.return_value = mock_email
        
        # Mock API responses for quote extraction
        mock_quote_response = Mock()
        mock_quote_response.json.return_value = {
            'message': {
                'content': '{"shipping_location": "Test", "client_name": "Client", "clauses": []}'
            }
        }
        mock_quote_response.raise_for_status.return_value = None
        
        # Mock API responses for item extraction
        mock_item_response = Mock()
        mock_item_response.json.return_value = {
            'message': {
                'content': '[{"part_number": "TEST-001", "quantity": 1, "description": "Test"}]'
            }
        }
        mock_item_response.raise_for_status.return_value = None
        
        # Configure mock to return different responses for different calls
        mock_post.side_effect = [mock_quote_response, mock_item_response]
        
        # Run the pipeline
        result = self.pipeline.process_email("test_email.eml")
        
        # Verify the result
        self.assertIsInstance(result, ProcessedQuote)
        self.assertEqual(result.quote_info.shipping_location, "Test")
        self.assertEqual(len(result.items), 1)
        self.assertEqual(result.items[0].part_number, "TEST-001")
    
    def test_pipeline_with_empty_email(self):
        """Test pipeline behavior with empty email"""
        # Create empty email data
        empty_email = Mock(spec=EmailData)
        empty_email.body = ""
        empty_email.inline_images = []
        
        with patch('email_diffusion_pipeline.parse_email', return_value=empty_email):
            with patch.object(self.pipeline, '_extract_quote_level_info') as mock_quote:
                with patch.object(self.pipeline, '_extract_item_metadata') as mock_items:
                    mock_quote.return_value = QuoteLevelInfo()
                    mock_items.return_value = []
                    
                    result = self.pipeline.process_email("empty_email.eml")
                    
                    self.assertEqual(len(result.items), 0)
                    self.assertEqual(result.raw_text, "")


class TestEmailDiffusionPipelineEdgeCases(unittest.TestCase):
    """Test edge cases and error conditions"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.pipeline = EmailDiffusionPipeline()
    
    def test_pipeline_with_malformed_json(self):
        """Test pipeline behavior with malformed JSON responses"""
        with patch('requests.post') as mock_post:
            # Mock malformed JSON response
            mock_response = Mock()
            mock_response.json.return_value = {
                'message': {
                    'content': '{"incomplete": "json"'
                }
            }
            mock_response.raise_for_status.return_value = None
            mock_post.return_value = mock_response
            
            text = "Test email text"
            
            with self.assertRaises(ValueError):
                self.pipeline._extract_quote_level_info(text)
    
    def test_pipeline_with_empty_api_response(self):
        """Test pipeline behavior with empty API responses"""
        with patch('requests.post') as mock_post:
            mock_response = Mock()
            mock_response.json.return_value = {
                'message': {
                    'content': ''
                }
            }
            mock_response.raise_for_status.return_value = None
            mock_post.return_value = mock_response
            
            text = "Test email text"
            
            with self.assertRaises(ValueError):
                self.pipeline._extract_quote_level_info(text)
    
    def test_pipeline_with_large_text_input(self):
        """Test pipeline behavior with very large text inputs"""
        # Create very long text
        long_text = "Test " * 10000  # 50,000 characters
        
        with patch('requests.post') as mock_post:
            mock_response = Mock()
            mock_response.json.return_value = {
                'message': {
                    'content': '{"shipping_location": "Test", "client_name": "Client", "clauses": []}'
                }
            }
            mock_response.raise_for_status.return_value = None
            mock_post.return_value = mock_response
            
            # Should handle large text without issues
            result = self.pipeline._extract_quote_level_info(long_text)
            self.assertIsInstance(result, QuoteLevelInfo)


if __name__ == '__main__':
    # Run the tests
    unittest.main(verbosity=2)

