from __future__ import annotations

import ctypes
import platform
from dataclasses import dataclass


FILE_MAP_WRITE = 0x0002
FILE_MAP_READ = 0x0004


@dataclass(slots=True)
class NamedMappingProbeResult:
    name: str
    exists: bool
    error: str | None = None


def probe_named_mapping(name: str, access: int = FILE_MAP_READ | FILE_MAP_WRITE) -> NamedMappingProbeResult:
    if not name:
        return NamedMappingProbeResult(name=name, exists=False, error="mapping name is empty")
    if platform.system() != "Windows":
        return NamedMappingProbeResult(name=name, exists=False, error="named mapping probe is Windows-only")

    kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)
    kernel32.OpenFileMappingW.argtypes = [ctypes.c_uint32, ctypes.c_int, ctypes.c_wchar_p]
    kernel32.OpenFileMappingW.restype = ctypes.c_void_p
    kernel32.CloseHandle.argtypes = [ctypes.c_void_p]
    kernel32.CloseHandle.restype = ctypes.c_int

    handle = kernel32.OpenFileMappingW(access, False, name)
    if not handle:
        error_code = ctypes.get_last_error()
        return NamedMappingProbeResult(
            name=name,
            exists=False,
            error=f"OpenFileMappingW failed with WinError {error_code}",
        )

    kernel32.CloseHandle(handle)
    return NamedMappingProbeResult(name=name, exists=True)
