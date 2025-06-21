# Quotient Deployment Guide - Ubuntu with NVIDIA GPU

This guide will help you deploy Quotient on your Ubuntu workstation with NVIDIA GPU for optimal performance.

## Prerequisites

### System Requirements
- Ubuntu 20.04 LTS or later
- NVIDIA GPU with CUDA support (RTX 3070 or better recommended)
- 16GB+ system RAM
- 50GB+ free disk space
- Python 3.13.2

### NVIDIA Driver Installation

1. **Check GPU and driver status:**
   ```bash
   nvidia-smi
   ```

2. **Install NVIDIA drivers if not present:**
   ```bash
   sudo apt update
   sudo apt install nvidia-driver-535  # or latest version
   sudo reboot
   ```

3. **Verify CUDA installation:**
   ```bash
   nvcc --version
   ```

## Environment Setup

### 1. Install Conda
```bash
# Download and install Miniconda
wget https://repo.anaconda.com/miniconda/Miniconda3-latest-Linux-x86_64.sh
bash Miniconda3-latest-Linux-x86_64.sh

# Restart shell or source conda
source ~/.bashrc
```

### 2. Create Python Environment
```bash
# Create environment with Python 3.13.2
conda create -n quotient python=3.13.2
conda activate quotient

# Verify Python version
python --version
```

### 3. Install PyTorch with CUDA Support
```bash
# Install PyTorch with CUDA 12.1 support
conda install pytorch torchvision torchaudio pytorch-cuda=12.1 -c pytorch -c nvidia

# Verify CUDA availability
python -c "import torch; print(f'CUDA available: {torch.cuda.is_available()}'); print(f'CUDA device: {torch.cuda.get_device_name(0) if torch.cuda.is_available() else \"None\"}')"
```

### 4. Install Additional Dependencies
```bash
# Install core dependencies
pip install -r requirements.txt

# Install additional CUDA-optimized packages
pip install accelerate bitsandbytes
```

## Configuration

### 1. Environment Variables
Create a `.env` file in the project root:

```bash
# LLM Configuration
LLM_BACKEND=openchat
LLM_ID=openchat/openchat-3.5-0106-Q4_K_M

# Hardware Optimization
USE_CUDA=true
USE_MPS=false
MAX_MEMORY_GB=16

# Processing Configuration
MAX_FILE_SIZE_MB=100
OUTPUT_DIR=output

# Optional: OpenAI fallback
# OPENAI_API_KEY=your_openai_key_here
```

### 2. Model Download
Download the OpenChat3.5 model (no token required):

```bash
# Download model (this will take time and space)
python -c "
from transformers import AutoTokenizer, AutoModelForCausalLM
model_id = 'openchat/openchat-3.5-0106-Q4_K_M'
tokenizer = AutoTokenizer.from_pretrained(model_id)
model = AutoModelForCausalLM.from_pretrained(model_id)
"
```

## Testing the Setup

### 1. Hardware Detection Test
```bash
python test_hardware.py
```

Expected output:
```
=== Hardware Information ===
Device Type: cuda
Available Memory: 16.0GB
GPU: NVIDIA GeForce RTX 4080
CUDA Version: 12.1
Compute Capability: (8, 9)
Optimization Config: {'torch_dtype': torch.float16, 'device_map': 'auto', ...}
============================
```

### 2. Basic Functionality Test
```bash
python test_basic.py
```

### 3. Full System Test
```bash
python example.py
```

## Performance Optimization

### 1. GPU Memory Management
For different GPU memory sizes:

**24GB+ (RTX 4090, A100):**
- Use full precision (float16)
- No quantization needed
- Enable flash attention

**16GB (RTX 4080):**
- Use float16 precision
- 8-bit quantization optional
- Memory mapping enabled

**8GB (RTX 3070):**
- Use float16 precision
- 8-bit quantization recommended
- Memory mapping required

### 2. Model Size Optimization
Adjust model size based on available memory:

```python
# In your configuration
if gpu_memory >= 24:
    model_id = "openchat/openchat-3.5-0106"  # Full precision model
elif gpu_memory >= 8:
    model_id = "openchat/openchat-3.5-0106-Q4_K_M"   # Quantized model
else:
    model_id = "microsoft/DialoGPT-medium"   # Smaller model
```

### 3. Batch Processing
For processing multiple documents:

```python
# Configure batch size based on GPU memory
if gpu_memory >= 24:
    batch_size = 8
elif gpu_memory >= 16:
    batch_size = 4
else:
    batch_size = 2
```

## Monitoring and Troubleshooting

### 1. GPU Monitoring
```bash
# Monitor GPU usage
watch -n 1 nvidia-smi

# Monitor memory usage
nvidia-smi --query-gpu=memory.used,memory.total --format=csv
```

### 2. Common Issues

**CUDA Out of Memory:**
- Reduce batch size
- Enable 8-bit quantization
- Use smaller model
- Clear GPU cache: `torch.cuda.empty_cache()`

**Model Loading Slow:**
- Use SSD storage
- Enable memory mapping
- Consider model caching

**Low Performance:**
- Check CUDA version compatibility
- Verify GPU driver version
- Monitor thermal throttling

### 3. Performance Benchmarks
```bash
# Run performance test
python -c "
import time
from quotient.utils.hardware_utils import HardwareDetector
from quotient.babbage.processors.entity_extractor import EntityExtractor
from quotient.core.config import QuotientConfig

config = QuotientConfig()
config.llm_backend = 'openchat'

extractor = EntityExtractor(config)

test_text = 'Qty: 100 pcs - Resistor 10kΩ 1/4W - $0.05 each'
start_time = time.time()
entities = extractor.extract_entities(test_text)
end_time = time.time()

print(f'Processing time: {end_time - start_time:.2f} seconds')
print(f'Entities extracted: {len(entities)}')
"
```

## Production Deployment

### 1. Systemd Service
Create `/etc/systemd/system/quotient.service`:

```ini
[Unit]
Description=Quotient AI Inventory System
After=network.target

[Service]
Type=simple
User=quotient
WorkingDirectory=/opt/quotient
Environment=PATH=/opt/conda/envs/quotient/bin
ExecStart=/opt/conda/envs/quotient/bin/python -m quotient.core.pipeline
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

### 2. Docker Deployment
Create `Dockerfile`:

```dockerfile
FROM nvidia/cuda:12.1-devel-ubuntu20.04

# Install system dependencies
RUN apt-get update && apt-get install -y \
    python3.13 \
    python3-pip \
    git \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY requirements.txt .
RUN pip3 install -r requirements.txt

# Copy application
COPY . /app
WORKDIR /app

# Run application
CMD ["python3", "-m", "quotient.core.pipeline"]
```

### 3. Resource Limits
Set appropriate resource limits:

```bash
# GPU memory limit
export CUDA_VISIBLE_DEVICES=0
export CUDA_MEM_FRACTION=0.8

# System memory limit
ulimit -v 16000000  # 16GB virtual memory
```

## Security Considerations

### 1. Model Security
- Store models in secure location
- Use model signing for integrity
- Regular model updates

### 2. Data Security
- Encrypt sensitive data
- Use secure file permissions
- Implement access controls

### 3. Network Security
- Use HTTPS for API endpoints
- Implement authentication
- Regular security updates

## Maintenance

### 1. Regular Updates
```bash
# Update conda environment
conda update --all

# Update PyTorch
conda install pytorch torchvision torchaudio pytorch-cuda=12.1 -c pytorch -c nvidia

# Update other packages
pip install --upgrade -r requirements.txt
```

### 2. Model Updates
```bash
# Update Llama model
python -c "
from transformers import AutoTokenizer, AutoModelForCausalLM
model_id = 'meta-llama/Meta-Llama-3-8B-Instruct'
tokenizer = AutoTokenizer.from_pretrained(model_id, revision='main')
model = AutoModelForCausalLM.from_pretrained(model_id, revision='main')
"
```

### 3. Performance Monitoring
- Monitor GPU utilization
- Track processing times
- Monitor memory usage
- Regular performance benchmarks

## Support

For issues and support:
1. Check the troubleshooting section above
2. Review GPU driver and CUDA compatibility
3. Monitor system resources
4. Check PyTorch and transformers documentation

## Performance Expectations

With proper configuration on an RTX 4080 (16GB):
- Model loading: 30-60 seconds
- Entity extraction: 2-5 seconds per document
- Batch processing: 10-20 documents per minute
- Memory usage: 8-12GB GPU memory

These numbers will vary based on document complexity and model size. 