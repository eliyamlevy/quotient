# Quotient - AI-Powered Inventory Management System

Quotient is a sophisticated AI-powered inventory management system with a three-layer architecture designed to automatically extract, analyze, and complete inventory data from various sources.

## 🚀 Features

### **Layer 1: Babbage Service (Data Ingestion & Processing)**
- **Multi-format Document Processing**: PDFs, emails, spreadsheets, images
- **AI-Powered Entity Extraction**: Using local Llama models or OpenAI
- **Hardware-Aware Optimization**: Automatic CUDA/MPS/CPU detection and optimization
- **Data Normalization**: Standardized inventory item formatting

### **Web API Service**
- **RESTful API**: FastAPI-based web service for remote access
- **File Upload Processing**: Direct file upload and processing
- **Text Processing**: Process text content for inventory extraction
- **Real-time Processing**: Background task processing with status updates
- **Interactive Documentation**: Auto-generated API docs at `/docs`

### **Hardware Optimization**
- **CUDA Support**: Optimized for NVIDIA GPUs with automatic memory management
- **Apple Silicon Support**: MPS acceleration for Mac users
- **CPU Fallback**: Graceful degradation for systems without GPU
- **Memory Management**: Automatic quantization based on available resources

### **Supported File Types**
- **Documents**: PDF, DOCX, TXT
- **Spreadsheets**: XLSX, CSV
- **Images**: JPG, PNG (with OCR)
- **Emails**: EML files

## 🏗️ Architecture

```
Quotient/
├── babbage/                 # Layer 1: Data Ingestion
│   ├── extractors/         # File format extractors
│   ├── processors/         # AI entity extraction
│   └── normalizers/        # Data standardization
├── core/                   # Core system components
│   ├── config.py          # Hardware-aware configuration
│   └── pipeline.py        # Main processing pipeline
├── utils/                  # Utilities and data models
│   ├── hardware_utils.py  # Hardware detection & optimization
│   └── data_models.py     # Data structures
└── tests/                  # Test suite
```

## 🛠️ Installation

### Prerequisites
- Python 3.13.2
- Conda (recommended for environment management)
- NVIDIA GPU with CUDA support (for optimal performance)

### Quick Start

1. **Clone the repository**
   ```bash
   git clone <your-repo-url>
   cd quotient
   ```

2. **Create conda environment**
   ```bash
   conda create -n quotient python=3.13.2
   conda activate quotient
   ```

3. **Install PyTorch with hardware support**
   ```bash
   # For CUDA (Ubuntu/Linux)
   conda install pytorch torchvision torchaudio pytorch-cuda=12.1 -c pytorch -c nvidia
   
   # For MPS (Apple Silicon)
   conda install pytorch=2.5.1 -c pytorch
   ```

4. **Install dependencies**
   ```bash
   conda install transformers=4.51.3 huggingface_accelerate=1.4.0
   pip install -r requirements.txt
   ```

5. **Test the installation**
   ```bash
   python test_hardware.py
   ```

## 🔧 Configuration

Create a `.env` file in the project root:

```bash
# LLM Configuration
LLM_BACKEND=openchat
LLM_ID=openchat/openchat-3.5-0106-Q4_K_M

# Hardware Optimization
USE_CUDA=true
USE_MPS=true
MAX_MEMORY_GB=16

# Processing Configuration
MAX_FILE_SIZE_MB=100
OUTPUT_DIR=output
```

## 🧪 Testing

### Hardware Detection Test
```bash
python test_hardware.py
```

### Basic Functionality Test
```bash
python test_basic.py
```

### Full System Test
```bash
python example.py
```

## 🚀 Usage

### Basic Usage
```python
from quotient.core.pipeline import QuotientPipeline
from quotient.core.config import QuotientConfig

# Initialize with hardware-aware configuration
config = QuotientConfig()
config.llm_backend = "llama"

# Create pipeline
pipeline = QuotientPipeline(config)

# Process documents
results = pipeline.process_documents(["invoice.pdf", "inventory.xlsx"])
```

### Web API Usage

#### Start the API Server
```bash
# Using the startup script (recommended)
./start_api.sh

# Or directly with Python
python api.py
```

The API will be available at:
- **API Server**: http://localhost:8000
- **Interactive Docs**: http://localhost:8000/docs
- **Health Check**: http://localhost:8000/health

#### API Endpoints

**Health Check**
```bash
curl http://localhost:8000/health
```

**Process Text**
```bash
curl -X POST "http://localhost:8000/process-text" \
     -H "Content-Type: application/json" \
     -d '{"text": "Item: Laptop, Quantity: 5, Price: $999", "max_items": 10}'
```

**Process File**
```bash
curl -X POST "http://localhost:8000/process-file" \
     -F "file=@inventory.xlsx" \
     -F "max_items=50"
```

**Get Supported Formats**
```bash
curl http://localhost:8000/supported-formats
```

#### Python Client Example
```python
from api_client_example import QuotientAPIClient

# Create client
client = QuotientAPIClient("http://localhost:8000")

# Process text
result = client.process_text("Item: Chair, Quantity: 10, Price: $299")
print(f"Extracted {result['items_extracted']} items")

# Process file
result = client.process_file("data/sample_inventory.xlsx")
print(f"Processed {result['filename']}")
```

#### Testing the API
```bash
# Run comprehensive API tests
python test_api.py

# Test specific endpoints
python api_client_example.py
```

### Hardware Information
```python
from quotient.utils.hardware_utils import print_hardware_info

# Display hardware capabilities
print_hardware_info()
```

## 🎯 Performance

### Hardware-Specific Optimizations

**NVIDIA GPU (CUDA)**:
- Float16 precision for faster inference
- Automatic memory mapping
- Quantization support (8-bit/4-bit)
- Flash attention for large models

**Apple Silicon (MPS)**:
- Float32 precision (MPS limitation)
- Memory-efficient processing
- Optimized for Mac hardware

**CPU Fallback**:
- Quantized models for memory efficiency
- Rule-based extraction as backup
- Compatible with all systems

### Expected Performance
- **CUDA (RTX 4080)**: 0.5-2 seconds per document
- **MPS (M2 Pro)**: 2-5 seconds per document  
- **CPU**: 10-30 seconds per document

## 🔒 Security

- Local model inference (no data sent to external APIs)
- Configurable API key management
- Secure file handling
- Environment-based configuration

## 📄 Documentation

- [Architecture Plan](docs/ARCHITECTURE_PLAN.md)
- [Deployment Guide](docs/DEPLOYMENT_GUIDE.md)
- [CUDA Deployment Guide](docs/DEPLOYMENT_CUDA.md)
- [Hugging Face Setup](docs/HUGGINGFACE_SETUP.md)
- [Project TODOs](docs/TODOS.md)

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests
5. Submit a pull request

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🆘 Support

For issues and support:
1. Check the [troubleshooting guide](docs/troubleshooting.md)
2. Review hardware compatibility
3. Check PyTorch and transformers documentation
4. Open an issue on GitHub

## 🎉 Acknowledgments

- Built with PyTorch and HuggingFace Transformers
- Hardware optimization inspired by modern AI deployment practices
- Designed for production-ready inventory management 