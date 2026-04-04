from __future__ import annotations

import os
import subprocess
from pathlib import Path


def detect_gpu_available() -> bool:
    visible_devices = os.getenv("CUDA_VISIBLE_DEVICES")
    if visible_devices and visible_devices.strip() not in {"", "-1", "none", "void"}:
        return True

    try:
        result = subprocess.run(
            [
                "nvidia-smi",
                "--query-gpu=name",
                "--format=csv,noheader",
            ],
            capture_output=True,
            check=False,
            text=True,
            timeout=2,
        )
    except (FileNotFoundError, subprocess.SubprocessError, OSError):
        result = None

    if result and result.returncode == 0 and result.stdout.strip():
        return True

    return any(Path(path).exists() for path in ("/dev/nvidiactl", "/dev/nvidia0"))
