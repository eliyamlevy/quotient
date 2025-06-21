# Quotient CUDA Server Deployment Guide

## Prerequisites

- Ubuntu 20.04+ with NVIDIA GPU
- CUDA 11.8+ installed
- Git installed
- Internet connection

## Setup Steps

### 1. Install and Initialize Conda

```bash
# Download Miniconda
wget https://repo.anaconda.com/miniconda/Miniconda3-latest-Linux-x86_64.sh

# Install Miniconda (follow prompts, accept defaults)
bash Miniconda3-latest-Linux-x86_64.sh

# Reload shell or source bashrc
source ~/.bashrc

# Initialize conda for current shell
conda init bash

# Reload shell again
source ~/.bashrc

# Verify conda installation
conda --version
```

### 2. Install System Dependencies

```bash
# Update package list
sudo apt update

# Install required system packages
sudo apt install -y git wget curl build-essential

# Install Tesseract OCR
sudo apt install -y tesseract-ocr tesseract-ocr-eng

# Install NVIDIA drivers (if not already installed)
# Check if drivers are installed: nvidia-smi
# If not: sudo apt install nvidia-driver-535
```

## System Requirements

- **OS**: Ubuntu 20.04+ (recommended)
- **Python**: 3.11 (for PyTorch compatibility)
- **GPU**: NVIDIA GPU with 8GB+ VRAM (16GB+ recommended)
- **RAM**: 16GB+ system RAM
- **Storage**: 50GB+ free space

## Installation

### 1. Install System Dependencies

```bash
# Update system
sudo apt update && sudo apt upgrade -y

# Install Python 3.11
sudo apt install python3.11 python3.11-venv python3.11-dev -y

# Install CUDA dependencies
sudo apt install nvidia-cuda-toolkit -y

# Install Tesseract for OCR
sudo apt install tesseract-ocr -y

# Install other dependencies
sudo apt install git wget curl -y
```

### 2. Install NVIDIA Drivers and CUDA

```bash
# Check GPU
nvidia-smi

# If not installed, follow NVIDIA's guide:
# https://docs.nvidia.com/cuda/cuda-installation-guide-linux/
```

### 3. Clone and Setup Repository

```bash
# Clone repository
git clone <your-repo-url>
cd quotient

# Option 1: Create environment from file (recommended)
conda env create -f environment.yml
conda activate quotient

# Option 2: Manual setup
# conda create -n quotient python=3.11 -y
# conda activate quotient
# conda install pytorch torchvision torchaudio pytorch-cuda=12.1 -c pytorch -c nvidia -y
# conda install -c conda-forge pandas openpyxl pillow pytesseract python-dotenv numpy -y
# pip install transformers accelerate bitsandbytes PyPDF2 pdfplumber
```

### 4. Environment Configuration

```bash
# Copy environment template
cp env.example .env

# Edit .env file with your settings
nano .env

# Required settings:
# HUGGINGFACE_TOKEN=your_token_here
# MODEL_NAME=meta-llama/Llama-2-7b-chat-hf
# MAX_MEMORY_GB=8
# USE_4BIT=true
```

### 5. Test Installation

```bash
# Test basic functionality
python test_basic.py

# Test hardware detection
python test_hardware.py

# Test with sample data
python example.py
```

## Performance Optimization

### 1. GPU Memory Management

For different GPU sizes:

**8GB GPU (RTX 3070, etc.):**
```python
# Use 4-bit quantization
load_in_4bit=True
max_memory_gb=6
```

**16GB GPU (RTX 4080, etc.):**
```python
# Use 8-bit quantization or none
load_in_8bit=True
max_memory_gb=12
```

**24GB+ GPU (RTX 4090, A100, etc.):**
```python
# No quantization needed
load_in_8bit=False
load_in_4bit=False
max_memory_gb=20
```

### 2. Model Selection

| Model | Size | Quality | Speed | Memory |
|-------|------|---------|-------|--------|
| microsoft/DialoGPT-medium | 345M | Good | Fast | 2GB |
| meta-llama/Llama-2-7b-chat-hf | 7B | Better | Medium | 8GB |
| meta-llama/Llama-3-8b-instruct | 8B | Best | Medium | 10GB |

### 3. Batch Processing

For processing multiple documents:

```python
from pathlib import Path
from quotient.core import QuotientPipeline, QuotientConfig

config = QuotientConfig()
pipeline = QuotientPipeline(config)

# Process multiple files
files = ["doc1.pdf", "doc2.xlsx", "doc3.jpg"]
results = []

for file in files:
    result = pipeline.process_single_document(Path(file))
    results.append(result)
    print(f"Processed {file}: {len(result.items)} items")
```

## Troubleshooting

### Common Issues

1. **CUDA out of memory**
   - Reduce `max_memory_gb` in config
   - Enable 4-bit quantization
   - Use smaller model

2. **Model download fails**
   - Check internet connection
   - Use HuggingFace token for gated models
   - Download model manually

3. **OCR not working**
   - Install Tesseract: `sudo apt install tesseract-ocr`
   - Check language packs: `sudo apt install tesseract-ocr-eng`

4. **PDF extraction fails**
   - Install pdfplumber: `pip install pdfplumber`
   - Check PDF file integrity

5. **Conda environment issues**
   - Update conda: `conda update conda`
   - Clean environment: `conda clean --all`
   - Recreate environment: `conda env remove -n quotient && conda env create -f environment.yml`

6. **PyTorch CUDA not found**
   - Check CUDA version: `nvidia-smi`
   - Install matching PyTorch version: `conda install pytorch-cuda=12.1 -c pytorch -c nvidia`
   - Verify installation: `python -c "import torch; print(torch.cuda.is_available())"`

### Performance Monitoring

```bash
# Monitor GPU usage
watch -n 1 nvidia-smi

# Monitor system resources
htop

# Check Python memory usage
python -c "import torch; print(torch.cuda.memory_allocated() / 1e9, 'GB')"
```

## Production Deployment

### 1. Systemd Service

Create `/etc/systemd/system/quotient.service`:
```ini
[Unit]
Description=Quotient AI Service
After=network.target

[Service]
Type=simple
User=quotient
WorkingDirectory=/opt/quotient
Environment=PATH=/opt/quotient/venv/bin
ExecStart=/opt/quotient/venv/bin/python server.py
Restart=always

[Install]
WantedBy=multi-user.target
```

### 2. Nginx Configuration

```nginx
server {
    listen 80;
    server_name your-domain.com;

    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
```

### 3. Security

- Use firewall: `sudo ufw enable`
- Set up SSL with Let's Encrypt
- Use non-root user for service
- Regular security updates

## Support

For issues:
1. Check logs: `journalctl -u quotient.service`
2. Test hardware: `python test_slimmed.py`
3. Verify CUDA: `python -c "import torch; print(torch.cuda.is_available())"` 