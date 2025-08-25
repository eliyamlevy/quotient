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
        
        # Count total tables found
        total_tables = len(email.inline_images)
        print(f"    📊 Total tables found: {total_tables}")
        
        # Clean email body by removing only actual links while preserving formatting
        print(f"    🔍 Cleaning email body - removing links while preserving formatting...")
        cleaned_body = email.body
        
        # Remove only actual URLs and links, preserving newlines and table formatting
        # Remove HTTP/HTTPS URLs (but preserve text that might look like URLs in tables)
        cleaned_body = re.sub(r'https?://[^\s\n]+', '', cleaned_body)
        
        # Remove www links (but be more careful not to remove part numbers)
        cleaned_body = re.sub(r'\bwww\.[^\s\n]+\.[^\s\n]+', '', cleaned_body)
        
        # Remove email addresses (but preserve text that might contain @ symbols)
        cleaned_body = re.sub(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b', '', cleaned_body)
        
        # Clean up multiple consecutive spaces but preserve newlines
        cleaned_body = re.sub(r'[ ]{2,}', ' ', cleaned_body)
        
        # Preserve the original structure
        cleaned_body = cleaned_body.strip()
        print(f"    ✅ Email body cleaned, length: {len(cleaned_body)} chars")
        print(f"    📊 Preserved newlines and table formatting")
        print(f"    🔧 Enhanced table detection and formatting preservation")
        
        # Combine email body with image text
        combined_text = self._combine_text_and_images(cleaned_body, image_texts)
        
        # The email parser has already extracted individual table rows
        # Let's combine them into a coherent table structure for the LLM
        print("\n🔍 Combining extracted table rows into coherent structure...")
        combined_table = self._combine_table_rows(combined_text)
        print(f"    ✅ Combined table structure: {len(combined_table)} chars")
        
        # Filter 2: Extract quote-level information
        print("\n🔍 Filter 2: Quote-Level Information Extraction")
        quote_info = self._extract_quote_level_info(combined_text)
        
        # Filter 3: Extract item metadata (simplified)
        print("\n🔍 Filter 3: Item Metadata Extraction (Simplified)")
        items = self._extract_item_metadata(combined_table, quote_info)
        
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
        Only process actual structured tables, not random text with spaces
        """
        lines = text.split('\n')
        table_lines = []
        
        # Look for actual table patterns, not just any text with spaces
        for line in lines:
            line = line.strip()
            if not line:
                continue
                
            # Check if this looks like a real table row
            # Must have multiple columns with consistent structure
            if '|' in line and len(line.split('|')) >= 4:
                # Pipe-separated table row
                table_lines.append(line)
            elif re.search(r'\s{3,}', line) and len(line) > 30:
                # Space-separated table row - must be long enough and have enough columns
                parts = re.split(r'\s{3,}', line)
                if len(parts) >= 4:  # At least 4 columns for a real table
                    # Check if first column looks like a row number
                    if re.match(r'^\d+$', parts[0].strip()):
                        table_lines.append(line)
        
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
        Combine email body with extracted image text, preserving formatting
        """
        combined = email_body
        
        for img_text in image_texts:
            # Insert image text with clear separators while preserving formatting
            combined += f"\n\n{'='*50}\n[IMAGE: {img_text.content_id}]\n{'='*50}\n"
            combined += img_text.text
            if img_text.table_structure:
                combined += f"\n\n[TABLE_STRUCTURE]\n{img_text.table_structure}"
            combined += f"\n{'='*50}\n"
        
        # Enhance table detection in the combined text
        combined = self._enhance_table_formatting(combined)
        
        return combined
    
    def _enhance_table_formatting(self, text: str) -> str:
        """
        Enhance table formatting to make it more readable for LLM parsing
        Only process actual table data, not random text
        """
        lines = text.split('\n')
        enhanced_lines = []
        
        for line in lines:
            # Look for lines that might be table headers or data rows
            if '|' in line and len(line.split('|')) >= 4:
                # This looks like a table row with pipe separators
                enhanced_lines.append(line)
            elif re.search(r'\s{3,}', line) and len(line.strip()) > 30:
                # This looks like a table row with space separators
                # Only enhance if it looks like actual table data with proper structure
                parts = re.split(r'\s{3,}', line.strip())
                if len(parts) >= 4:  # At least 4 columns for a real table
                    # Check if first column looks like a row number and second like a part number
                    if (re.match(r'^\d+$', parts[0].strip()) and 
                        re.match(r'^[A-Z0-9\-:]+$', parts[1].strip())):
                        # Looks like table data with row number and part number
                        enhanced_line = ' | '.join(parts)
                        enhanced_lines.append(enhanced_line)
                    else:
                        enhanced_lines.append(line)
                else:
                    enhanced_lines.append(line)
            else:
                enhanced_lines.append(line)
        
        return '\n'.join(enhanced_lines)
    
    def _combine_table_rows(self, text: str) -> str:
        """
        Combine individual table rows extracted by the email parser into one coherent table
        The email parser treats each row as a separate table, so we need to combine them
        """
        lines = text.split('\n')
        table_rows = []
        header_found = False
        
        for line in lines:
            line = line.strip()
            if not line:
                continue
            
            # Look for the table header
            if ('Item | Part Number | Quantity | U/M | Description | Price | Lead Time | RFP #' in line or
                'Item | Part Number | Quantity | U/M | Description' in line):
                if not header_found:
                    table_rows.append(line)
                    table_rows.append('-' * 80)  # Add separator line
                    header_found = True
                break
            
            # Look for individual table rows that were extracted by the email parser
            # These typically look like: "1 | AP1-19-111-T | 6 | EA | Panel - Filler, 1U, Color 111-T | AC252347-001"
            if '|' in line and re.match(r'^\d+\s*\|', line):
                # This looks like a table data row
                table_rows.append(line)
            elif re.match(r'^\d+\s+[A-Z0-9\-:]+', line):
                # This looks like a space-separated table row
                # Convert to pipe-separated format for consistency
                parts = re.split(r'\s{3,}', line)
                if len(parts) >= 4:
                    formatted_line = ' | '.join(parts)
                    table_rows.append(formatted_line)
            # Also look for the individual table rows that the email parser extracted
            # These are marked with [TABLE X] and contain the actual data
            elif line.startswith('[TABLE') and ']' in line:
                # This is a table marker, skip it
                continue
            elif re.match(r'^\d+\s+\|', line):
                # This looks like a table data row starting with a number and pipe
                table_rows.append(line)
            elif re.match(r'^\d+\s+[A-Z0-9\-:]+', line) and len(line) > 15:
                # This looks like a space-separated table row with enough content
                # Convert to pipe-separated format for consistency
                parts = re.split(r'\s{3,}', line)
                if len(parts) >= 3:  # At least 3 columns
                    formatted_line = ' | '.join(parts)
                    table_rows.append(formatted_line)
            # Also look for lines that start with numbers and contain part numbers
            elif re.match(r'^\d+\s+[A-Z0-9\-:]+', line) and len(line) > 10:
                # This looks like a space-separated table data row
                # Convert to pipe-separated format for consistency
                parts = re.split(r'\s{2,}', line)  # Use 2+ spaces as separator
                if len(parts) >= 3:  # At least 3 columns
                    formatted_line = ' | '.join(parts)
                    table_rows.append(formatted_line)
            # Also look for any line that contains a part number pattern
            elif re.search(r'\b[A-Z0-9\-:]+\s+\d+\s+[A-Z]+\b', line):
                # This looks like it contains part number, quantity, and unit
                # Try to extract the structured data
                if re.match(r'^\d+', line):
                    # Line starts with a number, likely a table row
                    table_rows.append(line)
        
        if table_rows:
            print(f"    📊 Found {len(table_rows)} table rows to combine")
            return '\n'.join(table_rows)
        else:
            print(f"    ⚠️  No table rows found, using original text")
            return text
    
    def _extract_item_table(self, text: str) -> str:
        """
        Extract only the actual item table from the email text
        Filters out non-table content and focuses on structured item data
        """
        lines = text.split('\n')
        table_lines = []
        in_table = False
        table_started = False
        consecutive_data_rows = 0
        
        for line in lines:
            line = line.strip()
            if not line:
                continue
            
            # Look for table header patterns - be more flexible
            if (('Item' in line and 'Part Number' in line and 'Quantity' in line) or
                ('Item | Part Number | Quantity' in line) or
                (line.startswith('Item') and '|' in line and len(line.split('|')) >= 4) or
                # Also look for the actual table header from the email
                ('Item | Part Number | Quantity | U/M | Description | Price | Lead Time | RFP #' in line)):
                in_table = True
                table_started = True
                consecutive_data_rows = 0
                table_lines.append(line)
                continue
            
            # If we're in a table, look for data rows
            if in_table:
                # Check if this looks like a table data row
                if '|' in line and len(line.split('|')) >= 4:
                    # Pipe-separated table row - must have at least 4 columns
                    table_lines.append(line)
                    consecutive_data_rows += 1
                elif re.search(r'\s{3,}', line) and len(line) > 30:
                    # Space-separated table row - must be long enough
                    parts = re.split(r'\s{3,}', line)
                    if len(parts) >= 4:  # At least 4 columns for a real table
                        # Check if first column looks like a row number and second like a part number
                        if (re.match(r'^\d+$', parts[0].strip()) and 
                            re.match(r'^[A-Z0-9\-:]+$', parts[1].strip())):
                            # Looks like table data with row number and part number
                            table_lines.append(line)
                            consecutive_data_rows += 1
                        else:
                            # Not a data row, might be end of table
                            if consecutive_data_rows < 3:  # Need at least 3 consecutive data rows
                                table_lines = []  # Reset if we don't have enough data
                                in_table = False
                            else:
                                in_table = False
                    else:
                        # Not enough columns
                        if consecutive_data_rows < 3:
                            table_lines = []
                            in_table = False
                        else:
                            in_table = False
                elif line.startswith('---') or line.startswith('==='):
                    # Table separator line
                    table_lines.append(line)
                elif consecutive_data_rows >= 3 and (not re.search(r'\s{2,}', line) and len(line) < 30):
                    # Short line without multiple spaces - likely end of table
                    # But only if we have enough data rows
                    in_table = False
                elif consecutive_data_rows >= 3:
                    # Keep lines that look like they belong to the table
                    table_lines.append(line)
                else:
                    # Not enough consecutive data rows, reset
                    table_lines = []
                    in_table = False
        
        if table_lines and consecutive_data_rows >= 3:
            print(f"    📊 Found table with {consecutive_data_rows} data rows")
            return '\n'.join(table_lines)
        else:
            print(f"    ⚠️  No valid table found, using original text")
            return text
    
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
        Filter 3: Extract item metadata using LLM - Simplified version
        Returns a clean JSON list of items with basic metadata
        """
        prompt = f"""
Extract ALL inventory items from this email text. This is critical - you must extract EVERY SINGLE item.

Email text:
{text[:25000]}...

IMPORTANT: This text contains table data with preserved formatting. Look for:
- Structured tables with columns (Item, Part Number, Quantity, U/M, Description, etc.)
- Data separated by | (pipes), spaces, or tabs
- Rows of inventory items
- Image content marked with [IMAGE:...] sections
- Enhanced table formatting with pipe separators (|) for better readability

CRITICAL REQUIREMENTS:
1. Extract EVERY SINGLE inventory item - do not miss any
2. Look for ALL rows in the table that contain part numbers
3. Process the entire table completely
4. Do not stop after a few items - continue until you've processed everything

Each item should have:
- part_number: The part number from the table
- quantity: The quantity (default to 1 if not specified)
- description: The item description
- unit: Unit of measure (default to "EA")
- price: Price if mentioned
- lead_time: Lead time if mentioned
- rfp_number: RFP number if mentioned

Return ONLY a valid JSON array like this:
[
    {{
        "part_number": "actual part number",
        "quantity": "actual quantity",
        "description": "actual description",
        "unit": "actual unit",
        "price": "price if mentioned",
        "lead_time": "lead time if mentioned",
        "rfp_number": "rfp number if mentioned"
    }}
]

If no items found, return: []

REMEMBER: Extract EVERY SINGLE item - completeness is critical!
"""

        try:
            response = requests.post(
                f"{self.api_url}/api/chat",
                json={
                    "model": self.model_name,
                    "messages": [{"role": "user", "content": prompt}],
                    "stream": False,
                    # Encourage longer, more complete outputs
                    "options": {
                        "num_predict": 4096,
                        "num_ctx": 8192,
                        "temperature": 0.2,
                        "top_p": 0.9
                    }
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
            
            # Debug: show raw model output to diagnose truncation or partial arrays
            try:
                preview = content[:600].replace('\n', '\n')
                print(f"    🔍 Raw items LLM response ({len(content)} chars): {preview}...")
            except Exception:
                pass

            # Extract JSON array from response
            json_str = None
            
            # Look for JSON array between backticks
            code_block_match = re.search(r'```(?:json)?\s*\n?(.*?)\n?```', content, re.DOTALL)
            if code_block_match:
                json_str = code_block_match.group(1).strip()
            
            # Look for JSON array with balanced brackets
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
    email_path = "data/email_batch/LONG QUOTE EXAMPLE.eml"
    
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
