# Email Diffusion Pipeline - Testing Guide

This directory contains comprehensive unit tests for the EmailDiffusionPipeline system.

## 🧪 Test Structure

### Test Files
- **`test_diffusion_pipeline.py`** - Main test suite with all test cases
- **`test_config.py`** - Test configuration, mock data, and utilities
- **`simple_test.py`** - Simple test runner using standard unittest (no pytest required)
- **`run_tests.py`** - Advanced test runner with pytest features
- **`test_requirements.txt`** - Python dependencies for advanced testing

### Test Categories

#### 1. **Dataclass Tests** (`TestImageTextResult`, `TestQuoteLevelInfo`, `TestItemMetadata`, `TestProcessedQuote`)
- Tests data structure creation and validation
- Verifies default values and field assignments
- Ensures proper data types and constraints

#### 2. **Pipeline Tests** (`TestEmailDiffusionPipeline`)
- Tests pipeline initialization and configuration
- Verifies API URL normalization
- Tests complete pipeline flow with mocked dependencies

#### 3. **Filter Tests**
- **Image-to-Text Conversion**: Tests image processing and text extraction
- **Quote-Level Extraction**: Tests metadata extraction from emails
- **Item Metadata Extraction**: Tests inventory item parsing
- **Result Compilation**: Tests final output assembly

#### 4. **Integration Tests** (`TestEmailDiffusionPipelineIntegration`)
- Tests full pipeline integration with mocked external services
- Verifies data flow between different filters
- Tests end-to-end processing scenarios

#### 5. **Edge Case Tests** (`TestEmailDiffusionPipelineEdgeCases`)
- Tests error handling and failure scenarios
- Verifies behavior with malformed data
- Tests large input handling and API failures

## 🚀 Running Tests

### Option 1: Simple Tests (No Dependencies)
```bash
# Run all tests using standard unittest
make test

# Run quick tests (dataclasses only)
make test-quick

# Or run directly
cd noam
python simple_test.py
python simple_test.py --quick
```

### Option 2: Advanced Tests (Requires pytest)
```bash
# Install test dependencies
pip install -r noam/test_requirements.txt

# Run with pytest
make test-pytest

# Run with coverage
make test-coverage

# Or run directly
cd noam
python run_tests.py
python run_tests.py --coverage
```

### Option 3: Specific Test Categories
```bash
cd noam

# Run specific categories
python run_tests.py --category dataclasses
python run_tests.py --category pipeline
python run_tests.py --category integration
python run_tests.py --category edge_cases
python run_tests.py --category filters
python run_tests.py --category utils

# Run with custom patterns
python run_tests.py --pattern "test_convert_images"
python run_tests.py --verbose
```

## 📊 Test Coverage

The test suite covers:

- **100% of dataclass definitions** - All fields, defaults, and validation
- **100% of pipeline methods** - All public and private methods
- **Error handling** - API failures, malformed data, edge cases
- **Data transformations** - Text processing, JSON parsing, image handling
- **Integration flows** - End-to-end pipeline execution

## 🔧 Test Configuration

### Mock Data
The `test_config.py` file provides:
- Sample email content and structures
- Mock API responses
- Test utilities and validation functions
- Error scenario definitions

### Mocking Strategy
- **External APIs**: All HTTP requests are mocked
- **File I/O**: File operations are mocked or use temporary files
- **Dependencies**: External modules are mocked where appropriate

## 🐛 Debugging Tests

### Verbose Output
```bash
# Run with detailed output
python simple_test.py  # Standard unittest verbose
python run_tests.py --verbose  # pytest verbose
```

### Specific Test Debugging
```bash
# Run single test method
python -m pytest test_diffusion_pipeline.py::TestEmailDiffusionPipeline::test_pipeline_initialization -v

# Run tests matching pattern
python run_tests.py --pattern "test_convert_images_to_text"
```

### Test Isolation
Each test class uses `setUp()` to create fresh test fixtures, ensuring tests don't interfere with each other.

## 📝 Adding New Tests

### 1. **Test Class Structure**
```python
class TestNewFeature(unittest.TestCase):
    def setUp(self):
        """Set up test fixtures"""
        pass
    
    def test_feature_behavior(self):
        """Test specific feature behavior"""
        # Arrange
        # Act
        # Assert
        pass
```

### 2. **Test Naming Convention**
- Test methods: `test_descriptive_name`
- Test classes: `TestFeatureName`
- Use descriptive names that explain what is being tested

### 3. **Mocking Guidelines**
- Mock external dependencies (APIs, databases, files)
- Use `@patch` decorator for method-level mocking
- Create realistic mock data in `test_config.py`

### 4. **Assertion Best Practices**
- Test one concept per test method
- Use specific assertions (`assertEqual`, `assertIn`, etc.)
- Provide clear error messages for failures

## 🚨 Common Issues

### Import Errors
```bash
# Ensure you're in the noam/ directory
cd noam
python simple_test.py
```

### Missing Dependencies
```bash
# Install test requirements
pip install -r test_requirements.txt
```

### Test Failures
- Check that all required modules are available
- Verify mock data matches expected formats
- Ensure test environment matches production setup

## 📈 Performance Testing

### Large Input Testing
The test suite includes tests for:
- Large text inputs (50,000+ characters)
- Multiple image processing
- Complex table structures

### Memory Usage
Tests verify that the pipeline handles large inputs without memory issues.

## 🔍 Continuous Integration

### GitHub Actions
The test suite is designed to run in CI/CD environments:
- No external dependencies required for basic tests
- Mocked external services
- Deterministic test results

### Pre-commit Hooks
Consider adding tests to pre-commit hooks:
```bash
# .pre-commit-config.yaml
- repo: local
  hooks:
    - id: run-tests
      name: Run Tests
      entry: python noam/simple_test.py
      language: system
      pass_filenames: false
```

## 📚 Additional Resources

- **unittest Documentation**: https://docs.python.org/3/library/unittest.html
- **pytest Documentation**: https://docs.pytest.org/
- **Mock Documentation**: https://docs.python.org/3/library/unittest.mock.html

## 🤝 Contributing

When adding new features:
1. Write tests first (TDD approach)
2. Ensure all tests pass
3. Maintain test coverage above 90%
4. Update this documentation

## 📞 Support

For test-related issues:
1. Check the test output for specific error messages
2. Verify your environment matches the requirements
3. Run tests with verbose output for more details
4. Check that all dependencies are properly installed

