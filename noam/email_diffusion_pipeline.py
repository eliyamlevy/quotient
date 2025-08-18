"""
Email Diffusion Pipeline - Multi-Filter Processing Flow

This pipeline processes emails through multiple filters, each augmenting the data
with specific information, similar to how diffusion models work.
"""

import re
import base64
import json
import requests
from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional
from email_parser import parse_email


@dataclass
class ImageTextResult:
    """Result from image-to-text conversion"""
    content_id: str
    text: str
    table_structure: str = ""  # ASCII representation of table structure


@dataclass
class QuoteLevelInfo:
    """Quote-level information extracted from email"""
    shipping_location: Optional[str] = None
    client_name: Optional[str] = None
    clauses: List[str] = field(default_factory=list)


@dataclass
class ItemMetadata:
    """Individual item metadata"""
    part_number: str
    quantity: int
    description: str
    unit: str = "EA"
    price: Optional[str] = None
    lead_time: Optional[str] = None
    rfp_number: Optional[str] = None
    item_number: Optional[str] = None


@dataclass
class ProcessedQuote:
    """Final processed quote result"""
    quote_info: QuoteLevelInfo
    items: List[ItemMetadata]
    raw_text: str
    image_texts: List[ImageTextResult]


class EmailDiffusionPipeline:
    """
    Diffusion-style email processing pipeline with multiple filters
    """
    
    def __init__(self, model_name: str = "llama4:scout", api_url: str = "http://localhost:11434"):
        self.model_name = model_name
        # Normalize API base: remove trailing slashes and optional OpenAI-style "/v1"
        normalized = (api_url or "http://localhost:11434").rstrip('/')
        if normalized.endswith('/v1'):
            normalized = normalized[:-3]
        self.api_url = normalized
    
    def process_email(self, email_path: str) -> ProcessedQuote:
        """
        Process email through all filters in sequence
        """
        print("🚀 Starting Email Diffusion Pipeline")
        
        # Parse email
        email = parse_email(email_path)
        print(f"📧 Email parsed: {len(email.body)} chars, {len(email.inline_images)} images")
        
        # Filter 1: Convert images to text
        print("\n🔍 Filter 1: Image-to-Text Conversion")
        image_texts = self._convert_images_to_text(email.inline_images)
        
        # Clean email body by removing links before combining
        print(f"    🔍 Cleaning email body - removing links...")
        cleaned_body = email.body
        # Remove URLs, HTTP links, and common link patterns
        cleaned_body = re.sub(r'https?://[^\s]+', '', cleaned_body)  # Remove HTTP/HTTPS links
        cleaned_body = re.sub(r'www\.[^\s]+', '', cleaned_body)      # Remove www links
        cleaned_body = re.sub(r'[^\s]+\.com[^\s]*', '', cleaned_body)  # Remove .com links
        cleaned_body = re.sub(r'[^\s]+\.org[^\s]*', '', cleaned_body)  # Remove .org links
        cleaned_body = re.sub(r'[^\s]+\.net[^\s]*', '', cleaned_body)  # Remove .net links
        cleaned_body = re.sub(r'[^\s]+\.gov[^\s]*', '', cleaned_body)  # Remove .gov links
        cleaned_body = re.sub(r'[^\s]+\.edu[^\s]*', '', cleaned_body)  # Remove .edu links
        # Clean up extra whitespace from link removal
        cleaned_body = re.sub(r'\s+', ' ', cleaned_body)
        cleaned_body = cleaned_body.strip()
        print(f"    ✅ Email body cleaned, length: {len(cleaned_body)} chars")
        
        # Combine email body with image text
        combined_text = self._combine_text_and_images(cleaned_body, image_texts)
        
        # Filter 2: Extract quote-level information
        print("\n🔍 Filter 2: Quote-Level Information Extraction")
        quote_info = self._extract_quote_level_info(combined_text)
        
        # Filter 3: Extract item metadata
        print("\n🔍 Filter 3: Item Metadata Extraction")
        items = self._extract_item_metadata(combined_text, quote_info)
        
        # Filter 4: Compile final result matrix
        print("\n🔍 Filter 4: Final Result Matrix Compilation")
        final_result = self._compile_result_matrix(quote_info, items, combined_text, image_texts)
        
        print("\n✅ Pipeline Complete!")
        return final_result
    
    def _convert_images_to_text(self, inline_images: List[Dict[str, str]]) -> List[ImageTextResult]:
        """
        Filter 1: Convert all images to text using multimodal LLM, preserving table structure
        """
        results = []
        
        for img in inline_images:
            print(f"  Processing image: {img['content_id']}")
            
            try:
                # Use multimodal LLM to extract text from image
                image_text = self._extract_text_from_image(img)
                
                # Extract table structure if present
                table_structure = self._extract_table_structure(image_text)
                
                results.append(ImageTextResult(
                    content_id=img['content_id'],
                    text=image_text,
                    table_structure=table_structure
                ))
                
            except Exception as e:
                print(f"  ⚠️  Image processing failed: {e}")
                # Fallback to placeholder
                results.append(ImageTextResult(
                    content_id=img['content_id'],
                    text=f"[IMAGE_PROCESSING_FAILED: {img['content_id']}]",
                    table_structure=""
                ))
        
        return results
    
    def _extract_text_from_image(self, image_data: Dict[str, str]) -> str:
        """
        Use multimodal LLM to extract text from image
        """
        prompt = """
You are an expert at reading images and extracting text content, especially from tables and technical documents.

Please read this image and extract ALL the text content you can see except links and metadata. Pay special attention to:

1. Tables - preserve the structure and relationships between columns and rows
2. Part numbers, quantities, and descriptions
3. Any text that appears to be inventory items or order details
4. Headers, titles, and section labels
5. Numbers, measurements, and specifications

If you see tabular data, try to maintain the column structure in your response.
If you see a list of items, preserve the order and relationships.

IMPORTANT: Return ONLY the extracted text content. Do not add explanations, interpretations, or conversational text.
Do not say "I'm happy to help" or "If you provide" or similar phrases.
If you do not get an image, do not return anything.
"""
        
        # Convert base64 image to bytes for the model
        try:
            image_bytes = base64.b64decode(image_data['data'])
            
            # Use multimodal generate endpoint for vision models
            response = requests.post(
                f"{self.api_url}/api/generate",
                json={
                    "model": self.model_name,
                    "prompt": prompt,
                    "images": [base64.b64encode(image_bytes).decode('utf-8')],
                    "stream": False
                }
            )
            response.raise_for_status()
            
            result = response.json()
            return result['response'].strip()
            
        except Exception as e:
            print(f"    ⚠️  LLM image processing failed: {e}")
            return f"[IMAGE_READ_ERROR: {str(e)}]"
    
    def _extract_table_structure(self, text: str) -> str:
        """
        Extract and format table structure from text
        """
        # Look for patterns that suggest table structure
        lines = text.split('\n')
        table_lines = []
        
        for line in lines:
            # Check if line has multiple columns (separated by spaces, tabs, or |)
            if re.search(r'\s{2,}|\t|\|', line.strip()):
                table_lines.append(line.strip())
        
        if table_lines:
            # Create ASCII representation
            structure = "┌" + "─" * 50 + "┐\n"
            for line in table_lines[:5]:  # Limit to first 5 lines
                structure += f"│ {line[:48]:<48} │\n"
            structure += "└" + "─" * 50 + "┘"
            return structure
        
        return ""
    
    def _combine_text_and_images(self, email_body: str, image_texts: List[ImageTextResult]) -> str:
        """
        Combine email body with extracted image text
        """
        combined = email_body
        
        for img_text in image_texts:
            # Insert image text at appropriate location
            combined += f"\n\n[IMAGE: {img_text.content_id}]\n{img_text.text}\n"
            if img_text.table_structure:
                combined += f"\n[TABLE_STRUCTURE]\n{img_text.table_structure}\n"
        
        return combined
    
    def _extract_quote_level_info(self, text: str) -> QuoteLevelInfo:
        """
        Filter 2: Extract quote-level information using LLM
        """
        prompt = f"""
You are an email analysis expert. Extract the following information from this email:

1. SHIPPING LOCATION: Where are the items being shipped to? (Could be full address, state acronyms, or city names)
2. CLIENT NAME: Who is requesting the quote? (Usually the person in the signature)
3. CLAUSES: Any alphanumeric codes that represent terms/conditions (format: Letter + 3 digits, e.g., C103, E223, H202)

Email text:
{text[:2000]}...

IMPORTANT: Return ONLY a valid JSON object. Do not include any other text, explanations, or formatting.
The response must be parseable JSON with this exact structure:

{{
    "shipping_location": "extracted location or null",
    "client_name": "extracted name or null", 
    "clauses": ["list", "of", "clause", "codes"]
}}

Focus on finding:
- Shipping location in phrases like "shipping to [location]", "deliver to [location]", etc.
- Client name in signature sections after "Thank you," or at email bottom
- Clauses that match the pattern: Letter + 3 digits (e.g., C103, E223, H202, Q010, Q011S, Q091W, Q132, Q836S, Q186, Q227, Q300, Q320, Q184)

Remember: Return ONLY the JSON object, nothing else.
"""
        
        try:
            response = requests.post(
                f"{self.api_url}/api/chat",
                json={
                    "model": self.model_name,
                    "messages": [{"role": "user", "content": prompt}],
                    "stream": False
                }
            )
            response.raise_for_status()
            
            # Parse JSON response
            try:
                result = response.json()
                content = result['message']['content']
            except json.JSONDecodeError as json_err:
                print(f"    ❌ API response not valid JSON: {json_err}")
                print(f"    🔍 Raw response: {response.text[:300]}...")
                raise ValueError(f"Invalid API response format: {json_err}")
            
            # Clean the response - extract JSON from multi-line responses
            print(f"    🔍 Raw LLM response: {content[:300]}...")
            
            # Try multiple strategies to extract JSON from the response
            json_str = None
            
            # Strategy 1: Look for JSON between backticks
            code_block_match = re.search(r'```(?:json)?\s*\n?(.*?)\n?```', content, re.DOTALL)
            if code_block_match:
                json_str = code_block_match.group(1).strip()
                print(f"    🔍 Found JSON in code block: {json_str[:100]}...")
            
            # Strategy 2: Look for JSON object with balanced braces
            if not json_str:
                # Find the first { and then balance braces to find the complete object
                start_brace = content.find('{')
                if start_brace != -1:
                    brace_count = 0
                    end_pos = start_brace
                    for i, char in enumerate(content[start_brace:], start_brace):
                        if char == '{':
                            brace_count += 1
                        elif char == '}':
                            brace_count -= 1
                            if brace_count == 0:
                                end_pos = i + 1
                                break
                    
                    if brace_count == 0:  # Balanced braces
                        json_str = content[start_brace:end_pos]
                        print(f"    🔍 Found JSON with balanced braces: {json_str[:100]}...")
            
            # Strategy 3: Simple regex fallback for basic JSON
            if not json_str:
                simple_match = re.search(r'\{[^{}]*"[^"]*"[^{}]*\}', content, re.DOTALL)
                if simple_match:
                    json_str = simple_match.group(0)
                    print(f"    🔍 Found JSON with simple regex: {json_str[:100]}...")
            
            if json_str:
                try:
                    parsed_result = json.loads(json_str)
                    
                    return QuoteLevelInfo(
                        shipping_location=parsed_result.get('shipping_location'),
                        client_name=parsed_result.get('client_name'),
                        clauses=parsed_result.get('clauses', [])
                    )
                except json.JSONDecodeError as json_err:
                    print(f"    ❌ JSON parsing failed: {json_err}")
                    print(f"    🔍 Attempted to parse: {json_str}")
                    # Try to clean up common issues
                    cleaned_json = self._clean_json_string(json_str)
                    if cleaned_json:
                        try:
                            parsed_result = json.loads(cleaned_json)
                            return QuoteLevelInfo(
                                shipping_location=parsed_result.get('shipping_location'),
                                client_name=parsed_result.get('client_name'),
                                clauses=parsed_result.get('clauses', [])
                            )
                        except json.JSONDecodeError:
                            pass
                    raise ValueError(f"Invalid JSON format: {json_err}")
            else:
                print(f"  ❌ No JSON found in LLM response: {content[:200]}...")
                raise ValueError("No JSON found in response")
            
        except Exception as e:
            print(f"  ❌ LLM extraction failed: {e}")
            raise RuntimeError(f"Quote-level information extraction failed: {e}")
    
    def _clean_json_string(self, json_str: str) -> str:
        """
        Clean up common JSON formatting issues
        """
        cleaned = json_str.strip()
        
        # Remove trailing commas before closing braces/brackets
        cleaned = re.sub(r',(\s*[}\]])', r'\1', cleaned)
        
        # Remove any trailing text after the JSON
        cleaned = re.sub(r'}[^}]*$', '}', cleaned)
        
        # Fix common quote issues
        cleaned = re.sub(r'([{,])\s*([a-zA-Z_][a-zA-Z0-9_]*)\s*:', r'\1 "\2":', cleaned)
        
        return cleaned
    
    def _extract_item_metadata(self, text: str, quote_info: QuoteLevelInfo) -> List[ItemMetadata]:
        """
        Filter 3: Extract item metadata using LLM
        """
        # Extract item metadata using LLM
        prompt = f"""
You are an inventory extraction expert. Extract ALL inventory items from this email.

QUOTE CONTEXT:
- Shipping Location: {quote_info.shipping_location or 'Not specified'}
- Client Name: {quote_info.client_name or 'Not specified'}
- Clauses: {', '.join(quote_info.clauses) if quote_info.clauses else 'None'}

Email text:
{text[:25000]}...

CRITICAL: Extract EVERY SINGLE inventory item from this email. Do not miss any items.

IMPORTANT EXTRACTION RULES:
- Extract ONLY actual inventory items from any structured data
- IGNORE all conversational text, explanations, or narrative content
- IGNORE all links, URLs, or web addresses
- IGNORE all email signatures, greetings, or personal messages
- IGNORE all marketing text, disclaimers, or legal language
- Focus ONLY on items that have: part_number, quantity, and description
- Each extracted item must represent a real product/part that can be ordered

Look carefully through ALL content including:
1. Any structured data - extract items from organized lists
2. Bullet points or lists - capture all items
3. Any tabular information - look for organized item data
4. Image content (marked with [IMAGE:...]) - extract all visible items

Each item should have:
- part_number: The part number from the data
- quantity: The quantity specified (default to 1 if not specified)
- description: The description of the item
- unit: Unit of measure if specified (default to "EA")
- price: Price if mentioned
- lead_time: Lead time if mentioned
- rfp_number: RFP number if mentioned

IMPORTANT: 
- Return ONLY a valid JSON array
- Include ONLY actual inventory items
- Process ALL content completely
- Do not skip any items
- The response must be parseable JSON
- Use the EXACT part numbers from the data
- Do NOT include any example data from this prompt - only extract from the actual email content
- Do NOT include conversational text, links, or non-inventory content

Expected structure:
[
    {{
        "part_number": "actual part number from email",
        "quantity": "actual quantity from email",
        "description": "actual description from email",
        "unit": "actual unit from email",
        "price": "price if mentioned",
        "lead_time": "lead time if mentioned",
        "rfp_number": "rfp number if mentioned"
    }}
]

If no items found, return empty array: []

Remember: Extract EVERY SINGLE inventory item - completeness is critical!
"""

        try:
            response = requests.post(
                f"{self.api_url}/api/chat",
                json={
                    "model": self.model_name,
                    "messages": [{"role": "user", "content": prompt}],
                    "stream": False
                }
            )
            response.raise_for_status()
            
            # Parse JSON response
            try:
                result = response.json()
                content = result['message']['content']
            except json.JSONDecodeError as json_err:
                print(f"    ❌ API response not valid JSON: {json_err}")
                print(f"    🔍 Raw response: {response.text[:300]}...")
                raise ValueError(f"Invalid API response format: {json_err}")
            
            # Clean the response - extract JSON array from multi-line responses
            json_str = None
            
            # Strategy 1: Look for JSON array between backticks
            code_block_match = re.search(r'```(?:json)?\s*\n?(.*?)\n?```', content, re.DOTALL)
            if code_block_match:
                json_str = code_block_match.group(1).strip()
                print(f"    🔍 Found JSON array in code block: {json_str[:100]}...")
            
            # Strategy 2: Look for JSON array with balanced brackets
            if not json_str:
                start_bracket = content.find('[')
                if start_bracket != -1:
                    bracket_count = 0
                    end_pos = start_bracket
                    for i, char in enumerate(content[start_bracket:], start_bracket):
                        if char == '[':
                            bracket_count += 1
                        elif char == ']':
                            bracket_count -= 1
                            if bracket_count == 0:
                                end_pos = i + 1
                                break
                    
                    if bracket_count == 0:  # Balanced brackets
                        json_str = content[start_bracket:end_pos]
                        print(f"    🔍 Found JSON array with balanced brackets: {json_str[:100]}...")
            
            # Strategy 3: Simple regex fallback for basic JSON array
            if not json_str:
                simple_match = re.search(r'\[.*\]', content, re.DOTALL)
                if simple_match:
                    json_str = simple_match.group(0)
                    print(f"    🔍 Found JSON array with simple regex: {json_str[:100]}...")
            
            if json_str:
                try:
                    items_data = json.loads(json_str)
                    print(f"    ✅ Successfully parsed JSON array with {len(items_data)} items")
                    
                    # Convert to ItemMetadata objects
                    items = []
                    for i, item_data in enumerate(items_data):
                        # Handle missing or None values with proper defaults
                        quantity = item_data.get('quantity')
                        if quantity is None or quantity == '':
                            quantity = 1  # Default to 1 if no quantity specified
                        else:
                            try:
                                quantity = int(quantity)
                            except (ValueError, TypeError):
                                quantity = 1  # Default to 1 if conversion fails
                        
                        items.append(ItemMetadata(
                            part_number=item_data.get('part_number', ''),
                            quantity=quantity,
                            description=item_data.get('description', ''),
                            unit=item_data.get('unit', 'EA'),
                            price=item_data.get('price'),
                            lead_time=item_data.get('lead_time'),
                            rfp_number=item_data.get('rfp_number'),
                            item_number=str(i + 1)
                        ))
                    
                    return items
                    
                except json.JSONDecodeError as json_err:
                    print(f"    ❌ JSON parsing failed: {json_err}")
                    print(f"    🔍 Attempted to parse: {json_str}")
                    # Try to clean up common issues
                    cleaned_json = self._clean_json_string(json_str)
                    if cleaned_json:
                        try:
                            items_data = json.loads(cleaned_json)
                            print(f"    ✅ Successfully cleaned and parsed JSON")
                            
                            # Convert to ItemMetadata objects
                            items = []
                            for i, item_data in enumerate(items_data):
                                # Handle missing or None values with proper defaults
                                quantity = item_data.get('quantity')
                                if quantity is None or quantity == '':
                                    quantity = 1  # Default to 1 if no quantity specified
                                else:
                                    try:
                                        quantity = int(quantity)
                                    except (ValueError, TypeError):
                                        quantity = 1  # Default to 1 if conversion fails
                                
                                items.append(ItemMetadata(
                                    part_number=item_data.get('part_number', ''),
                                    quantity=quantity,
                                    description=item_data.get('description', ''),
                                    unit=item_data.get('unit', 'EA'),
                                    price=item_data.get('price'),
                                    lead_time=item_data.get('lead_time'),
                                    rfp_number=item_data.get('rfp_number'),
                                    item_number=str(i + 1)
                                ))
                            
                            return items
                        except json.JSONDecodeError:
                            raise ValueError(f"Invalid JSON format after cleanup: {json_err}")
                    else:
                        raise ValueError(f"Invalid JSON format: {json_err}")
            else:
                print(f"  ❌ No JSON array found in LLM response: {content[:200]}...")
                raise ValueError("No JSON array found in response")
            
        except Exception as e:
            print(f"  ❌ LLM item extraction failed: {e}")
            raise RuntimeError(f"Item metadata extraction failed: {e}")
    
    def _compile_result_matrix(self, quote_info: QuoteLevelInfo, items: List[ItemMetadata], 
                             raw_text: str, image_texts: List[ImageTextResult]) -> ProcessedQuote:
        """
        Filter 4: Compile final result matrix
        """
        print(f"  📊 Compiling results: {len(items)} items")
        print(f"  📍 Shipping: {quote_info.shipping_location}")
        print(f"  👤 Client: {quote_info.client_name}")
        print(f"  📋 Clauses: {len(quote_info.clauses)} found")
        
        return ProcessedQuote(
            items=items,
            quote_info=quote_info,
            raw_text=raw_text,
            image_texts=image_texts
        )


def main():
    """Test the diffusion pipeline"""
    pipeline = EmailDiffusionPipeline()
    
    # Test with a sample email
    email_path = "../data/email_batch/LONG QUOTE EXAMPLE.eml"
    
    try:
        result = pipeline.process_email(email_path)
        
        print("\n" + "="*80)
        print("📋 FINAL RESULTS")
        print("="*80)
        
        print(f"\n📦 Quote Information:")
        print(f"   Shipping Location: {result.quote_info.shipping_location}")
        print(f"   Client Name: {result.quote_info.client_name}")
        print(f"   Clauses: {', '.join(result.quote_info.clauses)}")
        
        print(f"\n🛍️  Inventory Items ({len(result.items)}):")
        for i, item in enumerate(result.items, 1):
            print(f"   {i:2d}. {item.part_number:15s} | Qty: {item.quantity:3d} | {item.description}")
        
        print(f"\n📷 Images Processed: {len(result.image_texts)}")
        for img in result.image_texts:
            print(f"   - {img.content_id}: {len(img.text)} chars")
        
        # Export results
        export_data = {
            "quote_info": {
                "shipping_location": result.quote_info.shipping_location,
                "client_name": result.quote_info.client_name,
                "clauses": result.quote_info.clauses
            },
            "items": [
                {
                    "item_number": item.item_number,
                    "part_number": item.part_number,
                    "quantity": item.quantity,
                    "unit": item.unit,
                    "description": item.description,
                    "price": item.price,
                    "lead_time": item.lead_time,
                    "rfp_number": item.rfp_number
                }
                for item in result.items
            ],
            "images_processed": len(result.image_texts)
        }
        
        with open("diffusion_results.json", "w") as f:
            json.dump(export_data, f, indent=2)
        
        print(f"\n💾 Results exported to: diffusion_results.json")
        
    except Exception as e:
        print(f"❌ Pipeline failed: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
