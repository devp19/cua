"""
verify docker and adb dependencies are instaleld
set has_android bool flag to true if both are installed (further used in factory to check if provider is available)
"""

try:
    import subprocess
    subprocess.run(["docker", "--version"], capture_output=True, check=True)
    HAS_DOCKER = True
except (subprocess.SubprocessError, FileNotFoundError):
    HAS_DOCKER = False

import shutil
HAS_ADB = shutil.which("adb") is not None

HAS_ANDROID = HAS_DOCKER and HAS_ADB

from .provider import AndroidDockerProvider

__all__ = ["AndroidDockerProvider", "HAS_ANDROID"]



