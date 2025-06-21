# Preprocessing Integration in Text Processing

## Overview

This document describes the integration of the preprocessing pipeline into the text processing endpoint (`/process-text`) of the Quotient API. The preprocessing pipeline runs before entity extraction to improve the quality of text processing.

## Changes Made

### 1. Babbage Service Updates (`quotient/babbage/ingestion.py`)

#### Added Preprocessing Support
- **Import**: Added `PreprocPipeline` import
- **Initialization**: Added `self.preproc = None` in `__init__`
- **Setup Method**: Added `_setup_preproc()` method to initialize preprocessing pipeline
- **Processing Flow**: Modified `process_document()` to include preprocessing step

#### Processing Flow Changes
```python
# Before entity extraction, add preprocessing:
self._setup_preproc()

if self.preproc is not None:
    try:
        preproc_results = self.preproc.run_pipeline(raw_text)
        preprocessed_text = preproc_results['layer3']  # Use final layer output
    except Exception as e:
        preprocessed_text = raw_text  # Fallback to original text
else:
    preprocessed_text = raw_text

# Use preprocessed text for entity extraction
extracted_data = self.entity_extractor.extract_entities(preprocessed_text)
```

#### Enhanced Results
- **Layer1 Result**: Added preprocessing information to `layer1_result`
- **Metadata**: Includes preprocessing status, results, and text length information

### 2. API Updates (`api.py`)

#### Enhanced Request Model
```python
class TextProcessingRequest(BaseModel):
    text: str
    max_items: Optional[int] = 50
    use_preprocessing: Optional[bool] = True  # Enable/disable preprocessing
    return_preproc_results: Optional[bool] = False  # Include preprocessing results
```

#### Updated Process Text Endpoint
- **New Parameters**: Added `use_preprocessing` and `return_preproc_results` support
- **Enhanced Response**: Includes preprocessing status and optional results
- **Logging**: Added preprocessing status logging

#### Response Format
```json
{
    "success": true,
    "text_length": 1234,
    "items_extracted": 3,
    "processing_time_seconds": 2.5,
    "max_items_requested": 10,
    "use_preprocessing": true,
    "items": [...],
    "preprocessing_results": {  // Optional, when return_preproc_results=true
        "service": "babbage",
        "extraction_method": "text_reader",
        "text_length": 1234,
        "items_extracted": 3,
        "preprocessing": {
            "enabled": true,
            "results": {
                "layer1": "...",
                "layer2": "...",
                "layer3": "..."
            },
            "preprocessed_text_length": 1200
        }
    }
}
```

## Preprocessing Pipeline

### Layer 1: Text Normalization
- Converts all letters to lowercase
- Preserves non-alphabetic characters

### Layer 2: Label Clarification
- Uses LLM to replace quantity-related terms with "quantity"
- Replaces ID-related terms with "item_id"
- Standardizes terminology for better extraction

### Layer 3: Item Recognition
- Uses LLM to separate text into distinct items
- Preserves all relevant information per item
- Improves structure for entity extraction

## Usage Examples

### Basic Usage with Preprocessing
```python
import requests

response = requests.post(
    "http://localhost:8000/process-text",
    json={
        "text": "Your inventory text here...",
        "max_items": 10,
        "use_preprocessing": True,
        "return_preproc_results": False
    }
)
```

### Advanced Usage with Results
```python
response = requests.post(
    "http://localhost:8000/process-text",
    json={
        "text": "Your inventory text here...",
        "max_items": 10,
        "use_preprocessing": True,
        "return_preproc_results": True  # Get preprocessing details
    }
)

result = response.json()
if 'preprocessing_results' in result:
    preproc_info = result['preprocessing_results']['preprocessing']
    print(f"Preprocessing enabled: {preproc_info['enabled']}")
    print(f"Layer results: {list(preproc_info['results'].keys())}")
```

### Disable Preprocessing
```python
response = requests.post(
    "http://localhost:8000/process-text",
    json={
        "text": "Your inventory text here...",
        "max_items": 10,
        "use_preprocessing": False  # Skip preprocessing
    }
)
```

## Testing

### Test Scripts Created
1. **`scripts/test_preproc_integration.py`**: Comprehensive testing of preprocessing integration
2. **`examples/preprocessing_example.py`**: Usage examples and demonstrations
3. **Updated `scripts/test_api.py`**: Enhanced to test preprocessing functionality

### Running Tests
```bash
# Test preprocessing integration
python scripts/test_preproc_integration.py

# Run examples
python examples/preprocessing_example.py

# Test API functionality
python scripts/test_api.py
```

## Benefits

### Improved Text Processing
- **Better Structure**: Preprocessing normalizes and structures text
- **Enhanced Extraction**: More accurate entity extraction from messy text
- **Standardized Format**: Consistent terminology across different input formats

### Flexibility
- **Optional**: Can be enabled/disabled per request
- **Configurable**: Control over preprocessing behavior
- **Transparent**: Optional access to preprocessing results for debugging

### Robustness
- **Fallback**: Graceful degradation if preprocessing fails
- **Error Handling**: Comprehensive error handling and logging
- **Performance**: Efficient processing with minimal overhead

## Configuration

### Default Settings
- **Preprocessing**: Enabled by default (`use_preprocessing: true`)
- **Results**: Disabled by default (`return_preproc_results: false`)
- **Max Items**: 50 items by default

### Customization
- Modify default values in `TextProcessingRequest` model
- Adjust preprocessing pipeline parameters in `PreprocPipeline`
- Configure LLM settings in `config.yaml`

## Future Enhancements

### Potential Improvements
1. **Layer-Specific Control**: Enable/disable individual preprocessing layers
2. **Custom Preprocessing**: User-defined preprocessing rules
3. **Performance Optimization**: Caching and optimization for repeated patterns
4. **Advanced Analytics**: Detailed preprocessing performance metrics

### Integration Opportunities
1. **File Processing**: Extend preprocessing to file uploads
2. **Batch Processing**: Preprocessing for multiple documents
3. **Real-time Processing**: Streaming preprocessing for large documents

## Troubleshooting

### Common Issues
1. **Preprocessing Fails**: Check LLM availability and configuration
2. **No Results**: Verify text input and preprocessing parameters
3. **Performance Issues**: Monitor processing times and resource usage

### Debugging
1. **Enable Logging**: Check API logs for preprocessing details
2. **Request Results**: Use `return_preproc_results: true` to inspect preprocessing
3. **Test Endpoints**: Use `/preproc-text` endpoint for direct preprocessing testing

## Conclusion

The preprocessing integration enhances the text processing capabilities of the Quotient API by providing structured, normalized text to the entity extraction pipeline. This results in more accurate inventory item extraction, especially from complex or poorly formatted text inputs.

The implementation is backward-compatible, optional, and provides comprehensive debugging capabilities while maintaining robust error handling and performance optimization. 