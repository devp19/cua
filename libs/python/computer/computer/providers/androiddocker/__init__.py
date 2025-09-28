"""
verify docker and adb dependencies are instaleld
set has_android bool flag to true if both are installed (further used in factory to check if provider is available)
"""

try:
    import subprocess
    subprocess.run(["docker", "--version"], capture_output=True, check=True)
    subprocess.run(["adb", "version"], capture_output=True, check=True)
    HAS_ANDROID = True
except (subprocess.SubprocessError, FileNotFoundError):
    HAS_ANDROID = False

from .provider import AndroidDockerProvider

__all__ = ["AndroidDockerProvider", "HAS_ANDROID"]

