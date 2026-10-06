"""Read-only Colab hardware report; run with colab exec -f this_file."""
import importlib.metadata
import json
import os
import platform
import shutil
import subprocess
from datetime import datetime, timezone


def command(args):
    result = subprocess.run(args, capture_output=True, text=True, timeout=20)
    return {"returncode": result.returncode, "output": result.stdout.strip(), "error": result.stderr.strip()}


report = {
    "time_utc": datetime.now(timezone.utc).isoformat(),
    "python": platform.python_version(),
    "platform": platform.platform(),
    "cwd": os.getcwd(),
    "disk_gib": {k: round(v / 2**30, 2) for k, v in shutil.disk_usage("/content")._asdict().items()},
    "gpu": command(["nvidia-smi", "--query-gpu=name,memory.total,memory.free,driver_version", "--format=csv"]),
    "nvidia_smi": command(["nvidia-smi"]),
    "memory": command(["free", "-h"]),
    "packages": {},
}
for package in ("torch", "vllm", "transformers", "huggingface-hub"):
    try:
        report["packages"][package] = importlib.metadata.version(package)
    except importlib.metadata.PackageNotFoundError:
        report["packages"][package] = None
try:
    import torch
    report["torch_gpu"] = {
        "cuda_available": torch.cuda.is_available(),
        "cuda_version": torch.version.cuda,
        "bf16_supported": torch.cuda.is_bf16_supported() if torch.cuda.is_available() else False,
        "device_count": torch.cuda.device_count(),
        "capability": torch.cuda.get_device_capability() if torch.cuda.is_available() else None,
    }
except ImportError:
    report["torch_gpu"] = None
print(json.dumps(report, indent=2))
