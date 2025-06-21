#!/usr/bin/env python3
"""Download GGUF models from HuggingFace for local use."""

import os
import sys
import argparse
import requests
from pathlib import Path
from tqdm import tqdm
from typing import Optional

def download_file(url: str, filepath: str, chunk_size: int = 8192):
    """Download a file with progress bar."""
    response = requests.get(url, stream=True)
    response.raise_for_status()
    
    total_size = int(response.headers.get('content-length', 0))
    
    with open(filepath, 'wb') as f:
        with tqdm(total=total_size, unit='B', unit_scale=True, desc=os.path.basename(filepath)) as pbar:
            for chunk in response.iter_content(chunk_size=chunk_size):
                if chunk:
                    f.write(chunk)
                    pbar.update(len(chunk))

def find_gguf_files(model_id: str, token: Optional[str] = None) -> list:
    """Find GGUF files in a HuggingFace model repository."""
    headers = {}
    if token:
        headers['Authorization'] = f'Bearer {token}'
    
    # Get model info from HuggingFace API
    api_url = f"https://huggingface.co/api/models/{model_id}"
    response = requests.get(api_url, headers=headers)
    response.raise_for_status()
    
    model_info = response.json()
    files = model_info.get('siblings', [])
    
    # Filter for GGUF files
    gguf_files = [f for f in files if f['rfilename'].endswith('.gguf')]
    
    return gguf_files

def download_gguf_model(model_id: str, output_dir: str = "models", token: Optional[str] = None, filename: Optional[str] = None):
    """Download a GGUF model from HuggingFace."""
    
    print(f"Searching for GGUF files in {model_id}...")
    
    try:
        gguf_files = find_gguf_files(model_id, token)
        
        if not gguf_files:
            print(f"No GGUF files found in {model_id}")
            return
        
        print(f"Found {len(gguf_files)} GGUF file(s):")
        for i, file_info in enumerate(gguf_files):
            print(f"  {i+1}. {file_info['rfilename']} ({file_info['size']} bytes)")
        
        # Select file to download
        if filename:
            selected_file = next((f for f in gguf_files if f['rfilename'] == filename), None)
            if not selected_file:
                print(f"File {filename} not found in model")
                return
        else:
            # Select the first file (usually the main model)
            selected_file = gguf_files[0]
        
        # Create output directory
        os.makedirs(output_dir, exist_ok=True)
        
        # Download file
        download_url = f"https://huggingface.co/{model_id}/resolve/main/{selected_file['rfilename']}"
        output_path = os.path.join(output_dir, selected_file['rfilename'])
        
        print(f"\nDownloading {selected_file['rfilename']}...")
        download_file(download_url, output_path)
        
        print(f"\nModel downloaded successfully to: {output_path}")
        print(f"Add this path to your config.yaml:")
        print(f"gguf_model_path: \"{output_path}\"")
        
    except Exception as e:
        print(f"Error downloading model: {str(e)}")
        sys.exit(1)

def main():
    parser = argparse.ArgumentParser(description="Download GGUF models from HuggingFace")
    parser.add_argument("model_id", help="HuggingFace model ID (e.g., TheBloke/Llama-2-7B-Chat-GGUF)")
    parser.add_argument("--output-dir", default="models", help="Output directory for downloaded model")
    parser.add_argument("--token", help="HuggingFace token (for gated models)")
    parser.add_argument("--filename", help="Specific GGUF filename to download")
    
    args = parser.parse_args()
    
    download_gguf_model(args.model_id, args.output_dir, args.token, args.filename)

if __name__ == "__main__":
    main() 