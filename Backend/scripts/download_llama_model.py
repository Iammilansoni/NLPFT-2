"""
Download Llama 3.2 3B Instruct GGUF model
Downloads the quantized Q4_K_M version for efficient CPU inference
"""

import os
import sys
import urllib.request
from pathlib import Path
from tqdm import tqdm


class DownloadProgressBar(tqdm):
    """Progress bar for downloads"""
    def update_to(self, b=1, bsize=1, tsize=None):
        if tsize is not None:
            self.total = tsize
        self.update(b * bsize - self.n)


def download_file(url: str, output_path: str):
    """Download file with progress bar"""
    print(f"Downloading from: {url}")
    print(f"Saving to: {output_path}")
    
    with DownloadProgressBar(unit='B', unit_scale=True, miniters=1, desc=output_path) as t:
        urllib.request.urlretrieve(url, filename=output_path, reporthook=t.update_to)
    
    print(f"✅ Download complete: {output_path}")


def main():
    """Download Llama 3.2 3B Instruct model"""
    
    # Model details
    MODEL_NAME = "llama-3.2-3b-instruct-q4_k_m.gguf"
    MODEL_URL = "https://huggingface.co/bartowski/Llama-3.2-3B-Instruct-GGUF/resolve/main/Llama-3.2-3B-Instruct-Q4_K_M.gguf"
    
    # Default model directory
    models_dir = Path.home() / "models"
    models_dir.mkdir(exist_ok=True)
    
    model_path = models_dir / MODEL_NAME
    
    # Check if already downloaded
    if model_path.exists():
        print(f"✅ Model already exists: {model_path}")
        print(f"   Size: {model_path.stat().st_size / (1024**3):.2f} GB")
        
        response = input("Do you want to re-download? (y/N): ")
        if response.lower() != 'y':
            print("Skipping download.")
            print(f"\nTo use this model, set in your .env file:")
            print(f'LLAMA_MODEL_PATH="{model_path}"')
            return
    
    print("\n" + "="*60)
    print("Downloading Llama 3.2 3B Instruct (Q4_K_M quantized)")
    print("="*60)
    print(f"Model: {MODEL_NAME}")
    print(f"Size: ~2.0 GB")
    print(f"Quantization: Q4_K_M (good balance of quality and speed)")
    print(f"Destination: {model_path}")
    print("="*60 + "\n")
    
    try:
        download_file(MODEL_URL, str(model_path))
        
        print("\n" + "="*60)
        print("✅ Model downloaded successfully!")
        print("="*60)
        print(f"Model path: {model_path}")
        print(f"Size: {model_path.stat().st_size / (1024**3):.2f} GB")
        print("\nNext steps:")
        print("1. Install llama.cpp:")
        print("   - Download from: https://github.com/ggerganov/llama.cpp/releases")
        print("   - Or build from source")
        print("2. Add to your .env file:")
        print(f'   LLAMA_MODEL_PATH="{model_path}"')
        print('   LLAMA_CPP_PATH="path/to/llama-cli"  # or just "llama-cli" if in PATH')
        print("\n3. Test the model:")
        print("   python scripts/test_llama_model.py")
        print("="*60)
        
    except Exception as e:
        print(f"\n❌ Download failed: {e}")
        print("\nAlternative download methods:")
        print("1. Manual download:")
        print(f"   URL: {MODEL_URL}")
        print(f"   Save to: {model_path}")
        print("\n2. Using huggingface-cli:")
        print("   pip install huggingface-hub")
        print("   huggingface-cli download bartowski/Llama-3.2-3B-Instruct-GGUF Llama-3.2-3B-Instruct-Q4_K_M.gguf")
        sys.exit(1)


if __name__ == "__main__":
    main()
