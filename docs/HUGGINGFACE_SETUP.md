# Hugging Face Token Setup Guide

## Why You Need a Token

Some models on Hugging Face (especially Llama models) are "gated" and require authentication to download. This is to ensure responsible AI usage.

## Getting Your Token

### 1. Create/Login to Hugging Face Account
- Go to [https://huggingface.co/](https://huggingface.co/)
- Sign up or log in to your account

### 2. Generate Access Token
1. Go to [https://huggingface.co/settings/tokens](https://huggingface.co/settings/tokens)
2. Click "New token"
3. Give it a name (e.g., "Quotient AI")
4. Select "Read" role (minimum required)
5. Click "Generate token"
6. **Copy the token** (you won't see it again!)

### 3. Request Model Access
For Llama models, you also need to request access:

1. Go to the model page (e.g., [Llama-2-7b-chat-hf](https://huggingface.co/meta-llama/Llama-2-7b-chat-hf))
2. Click "Request access"
3. Fill out the form (usually just your use case)
4. Wait for approval (usually quick, 1-24 hours)

## Alternative Models (No Token Required)

If you don't want to wait for Llama access, you can use these open models:

```bash
# In your .env file, change to:
LLM_ID=openchat/openchat-3.5-0106-Q4_K_M
```

Other good alternatives:
- `openchat/openchat-3.5-0106-Q4_K_M` (7B parameters, quantized, excellent quality)
- `microsoft/DialoGPT-medium` (345M parameters, fast)
- `gpt2` (124M parameters, very fast)
- `distilgpt2` (82M parameters, fastest)

## Setting Up Your Environment

### 1. Create .env file
```bash
cp env.example .env
```

### 2. Add your token
```bash
# Edit .env file
nano .env
```

Add your token:
```env
HUGGINGFACE_TOKEN=hf_your_token_here
LLM_ID=openchat/openchat-3.5-0106-Q4_K_M
USE_CUDA=true
MAX_MEMORY_GB=16
```

### 3. Test the setup
```bash
python test_slimmed.py
```

## Troubleshooting

### "Model not found" error
- Check if you have access to the model
- Verify your token is correct
- Try a different model (see alternatives above)

### "Token invalid" error
- Generate a new token
- Make sure you copied the full token
- Check if your account is verified

### "Access denied" error
- Request access to the specific model
- Wait for approval
- Use an alternative model in the meantime

## Model Comparison

| Model | Size | Quality | Speed | Token Required | Memory |
|-------|------|---------|-------|----------------|--------|
| openchat/openchat-3.5-0106-Q4_K_M | 7B | Excellent | Fast | No | 4-6GB |
| microsoft/DialoGPT-medium | 345M | Good | Fast | No | 2GB |
| gpt2 | 124M | Basic | Very Fast | No | 1GB |
| distilgpt2 | 82M | Basic | Fastest | No | 0.5GB |
| meta-llama/Llama-2-7b-chat-hf | 7B | Better | Medium | Yes | 8GB |
| meta-llama/Llama-3-8b-instruct | 8B | Best | Medium | Yes | 10GB |

## Security Notes

- Keep your token secure
- Don't commit it to version control
- Use environment variables
- Rotate tokens periodically 