# GGUF Model Setup Guide

This guide explains how to use local GGUF model files with Quotient for offline AI processing.

## What are GGUF Models?

GGUF (GPT-Generated Unified Format) is a file format for storing large language models that can be run locally using the `llama-cpp-python` library. These models are:

- **Offline-capable**: No internet connection required after download
- **Memory-efficient**: Optimized for local hardware
- **Fast**: Direct CPU/GPU inference
- **Privacy-focused**: All processing happens locally

## Installation

1. Install the required dependencies:
```bash
pip install llama-cpp-python
```

2. For GPU acceleration (optional):
```bash
# CUDA support
pip install llama-cpp-python --force-reinstall --index-url https://jllllll.github.io/llama-cpp-python-cuBLAS-wheels/AVX2/cu118

# OpenBLAS support (faster CPU inference)
pip install llama-cpp-python --force-reinstall --index-url https://jllllll.github.io/llama-cpp-python-cuBLAS-wheels/AVX2/openblas
```

## Downloading GGUF Models

### Option 1: Using the Download Script

Use the provided download script to get GGUF models from HuggingFace:

```bash
# Download a model (e.g., Llama-2-7B-Chat)
python scripts/download_gguf_model.py TheBloke/Llama-2-7B-Chat-GGUF

# Download with specific filename
python scripts/download_gguf_model.py TheBloke/Llama-2-7B-Chat-GGUF --filename llama-2-7b-chat.Q4_K_M.gguf

# Download to custom directory
python scripts/download_gguf_model.py TheBloke/Llama-2-7B-Chat-GGUF --output-dir ./my_models
```

### Option 2: Manual Download

1. Visit [HuggingFace GGUF Models](https://huggingface.co/TheBloke?search_models=gguf)
2. Choose a model (e.g., `TheBloke/Llama-2-7B-Chat-GGUF`)
3. Download the `.gguf` file you want (Q4_K_M is a good balance of size/quality)
4. Place it in your `models/` directory

## Configuration

Update your `config.yaml` to use the GGUF model:

```yaml
# Comment out or remove the HuggingFace configuration
# huggingface_token: "your_token_here"
# llm_id: "meta-llama/Llama-2-7b-chat-hf"

# Add GGUF model path
gguf_model_path: "models/llama-2-7b-chat.Q4_K_M.gguf"
```

## Model Recommendations

### For CPU-only systems:
- **Llama-2-7B-Chat-Q4_K_M**: Good balance of speed and quality (~4GB)
- **Llama-2-7B-Chat-Q5_K_M**: Better quality, slightly slower (~5GB)

### For systems with 8GB+ RAM:
- **Llama-2-13B-Chat-Q4_K_M**: Better quality, more memory (~7GB)
- **CodeLlama-7B-Instruct-Q4_K_M**: Good for code-related tasks (~4GB)

### For systems with 16GB+ RAM:
- **Llama-2-13B-Chat-Q5_K_M**: High quality (~8GB)
- **Llama-2-70B-Chat-Q4_K_M**: Best quality, requires significant RAM (~35GB)

## Testing

Test your GGUF model setup:

```bash
python scripts/test_gguf.py
```

## Performance Tuning

### CPU Optimization

Edit the GGUF model initialization in `entity_extractor.py`:

```python
self.gguf_model = Llama(
    model_path=model_path,
    n_ctx=2048,        # Context window size
    n_threads=8,       # Number of CPU threads (adjust based on your CPU)
    n_gpu_layers=0,    # Set to 0 for CPU-only
    verbose=False
)
```

### GPU Acceleration

For CUDA support, set `n_gpu_layers` to a positive number:

```python
self.gguf_model = Llama(
    model_path=model_path,
    n_ctx=2048,
    n_threads=4,
    n_gpu_layers=35,   # Number of layers to offload to GPU
    verbose=False
)
```

## Troubleshooting

### Common Issues

1. **"llama-cpp-python not available"**
   - Install: `pip install llama-cpp-python`

2. **"Model file not found"**
   - Check the path in `config.yaml`
   - Ensure the file exists and has `.gguf` extension

3. **"Out of memory"**
   - Use a smaller model (Q4_K_M instead of Q5_K_M)
   - Reduce `n_ctx` (context window)
   - Close other applications

4. **Slow performance**
   - Increase `n_threads` for CPU
   - Enable GPU acceleration with `n_gpu_layers`
   - Use a smaller model

### Memory Requirements

- **Q4_K_M models**: ~4-8GB RAM
- **Q5_K_M models**: ~5-10GB RAM
- **Q8_0 models**: ~8-16GB RAM

## Comparison: GGUF vs HuggingFace

| Feature | GGUF | HuggingFace |
|---------|------|-------------|
| Offline | ✅ Yes | ❌ No |
| Memory | ✅ Efficient | ❌ Higher |
| Speed | ✅ Fast | ⚠️ Slower |
| Setup | ⚠️ Manual | ✅ Easy |
| Model Variety | ⚠️ Limited | ✅ Extensive |

## Next Steps

1. Download a GGUF model using the script
2. Update your `config.yaml`
3. Test with `python scripts/test_gguf.py`
4. Start the API server: `python api.py`

Your Quotient system will now run completely offline with local AI processing! 