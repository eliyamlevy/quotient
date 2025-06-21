# Quotient - AI-Powered Inventory Management System

Quotient is a sophisticated AI-powered inventory management system with a three-layer architecture designed to automatically extract, analyze, and complete inventory data from various sources.

## 🚀 Features

### **Layer 1: Babbage Service (Data Ingestion & Processing)**
- **Multi-format Document Processing**: PDFs, spreadsheets, images
- **AI-Powered Entity Extraction**: Using local Llama models
- **Hardware-Aware Optimization**: Automatic hardware detection and optimization
- **Data Normalization**: Standardized inventory item formatting

### **Supported File Types**
- **Documents**: PDF, TXT
- **Spreadsheets**: XLSX, CSV
- **Images**: JPG, PNG (with OCR)

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

## 🌿 Deployment Branches

This repository contains different deployment configurations optimized for different environments:

### **`slim` Branch - Laptop Development**
- Lightweight version for Mac/Laptop development
- MPS acceleration for Apple Silicon
- CPU fallback support
- Minimal dependencies

**Quick Start (Laptop)**:
```bash
git checkout slim
conda create -n quotient python=3.11
conda activate quotient
pip install -r requirements.txt
```

### **`cuda-deployment` Branch - CUDA Server**
- Full CUDA optimization for NVIDIA GPUs
- 4-bit quantization support
- Optimized for Ubuntu servers
- Complete deployment guide

**Quick Start (CUDA Server)**:
```bash
git checkout cuda-deployment
conda env create -f environment.yml
conda activate quotient
```

### **`main` Branch - Base System**
- Core functionality without hardware-specific optimizations
- Good starting point for custom deployments
- Manual configuration required

## 🛠️ Installation

### Prerequisites
- Python 3.11+
- Conda (recommended for environment management)

### Quick Start

1. **Choose your deployment branch** (see above)
2. **Clone the repository**
   ```bash
   git clone <your-repo-url>
   cd quotient
   ```

3. **Follow branch-specific instructions**

## 🔧 Configuration

Create a `.env` file in the project root:

```bash
# LLM Configuration
LLM_BACKEND=llama
LLAMA_MODEL=microsoft/DialoGPT-medium  # No token required

# Hardware Optimization
USE_MPS=true
MAX_MEMORY_GB=8

# Processing Configuration
MAX_FILE_SIZE_MB=50
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

## �� Documentation

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

## 🎉 Acknowledgments

- Built with PyTorch and HuggingFace Transformers
- Hardware optimization inspired by modern AI deployment practices
- Designed for production-ready inventory management 