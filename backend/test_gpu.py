"""Quick script to test GPU availability."""
import torch

print("=" * 60)
print("GPU Detection Test")
print("=" * 60)
print(f"PyTorch Version: {torch.__version__}")
print(f"CUDA Available: {torch.cuda.is_available()}")

if torch.cuda.is_available():
    print(f"CUDA Version: {torch.version.cuda}")
    print(f"cuDNN Version: {torch.backends.cudnn.version()}")
    print(f"GPU Count: {torch.cuda.device_count()}")
    print(f"GPU Name: {torch.cuda.get_device_name(0)}")
    print(f"GPU Memory: {torch.cuda.get_device_properties(0).total_memory / 1024**3:.2f} GB")
    print("\n✓ GPU acceleration is available!")
else:
    print("\n✗ GPU not detected. Possible reasons:")
    print("  1. PyTorch CPU-only version installed")
    print("  2. CUDA drivers not installed")
    print("  3. CUDA version mismatch")
    print("\nTo fix:")
    print("  1. Check NVIDIA drivers: nvidia-smi")
    print("  2. Uninstall PyTorch: pip uninstall torch torchvision torchaudio")
    print("  3. Install CUDA version: pip install torch --index-url https://download.pytorch.org/whl/cu121")
print("=" * 60)

