from __future__ import annotations

import re
import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable


ATS_APP_ID = "270880"
KNOWN_STEAM_ROOTS = [
    Path(r"C:\Program Files (x86)\Steam"),
    Path(r"D:\Steam"),
    Path(r"E:\Steam"),
]


@dataclass(slots=True)
class TelemetryProbeStatus:
    ats_running: bool
    plugin_dll_present: bool
    plugin_dll_path: str | None = None
    mapping_name: str | None = None
    mapping_present: bool = False
    mapping_error: str | None = None
    game_log_plugin_loaded: bool = False
    game_log_initialized: bool = False
    decode_supported: bool | None = None
    decode_error: str | None = None
    tick_advanced: bool | None = None


@dataclass(slots=True)
class ControlProbeStatus:
    ats_running: bool
    plugin_dll_present: bool
    python_module_present: bool
    field_mapping_ok: bool
    mapping_name: str | None = None
    mapping_present: bool = False
    mapping_error: str | None = None


def classify_telemetry_probe_status(status: TelemetryProbeStatus) -> tuple[str, list[str]]:
    details: list[str] = []
    if status.mapping_present and status.decode_supported is True and status.tick_advanced is not False:
        details.append(f"{status.mapping_name} is visible and decodes successfully.")
        if status.tick_advanced:
            details.append("Live update token changed across sampled frames.")
        return "telemetry ready", details

    if status.mapping_present and status.decode_supported is True and status.tick_advanced is False:
        details.append(f"{status.mapping_name} is visible and decodes successfully.")
        details.append("Live update token did not change across sampled frames.")
        return "mapping visible but stale/non-updating", details

    if status.mapping_present and status.decode_supported is False:
        details.append(f"{status.mapping_name} is visible.")
        if status.decode_error:
            details.append(status.decode_error)
        return "mapping visible but unsupported layout", details

    if status.mapping_present:
        details.append(f"{status.mapping_name} is visible.")
        return "telemetry ready", details

    if _is_permission_like_error(status.mapping_error):
        details.append(status.mapping_error or "unknown mapping error")
        return "probable permission/environment issue", details

    if not status.ats_running:
        details.append("ATS process is not running.")
        return "ATS not running", details

    if not status.plugin_dll_present:
        details.append(f"Telemetry plugin DLL is missing: {status.plugin_dll_path}")
        return "plugin missing", details

    if status.game_log_plugin_loaded and not status.game_log_initialized:
        details.append("Plugin DLL was loaded by ATS, but shared memory is not initialized yet.")
        details.append("Likely ATS is still in a menu/popup gate or has not reached the in-world state.")
        return "named shared memory missing", details

    if status.game_log_plugin_loaded:
        details.append(f"{status.mapping_name} is still missing after plugin load.")
        return "named shared memory missing", details

    details.append("ATS is running but there is no evidence that the telemetry plugin finished loading.")
    return "plugin missing", details


def classify_control_probe_status(status: ControlProbeStatus) -> tuple[str, list[str]]:
    details: list[str] = []
    if status.mapping_present and status.python_module_present and status.field_mapping_ok:
        details.append(f"{status.mapping_name} is visible.")
        return "control path ready", details

    if _is_permission_like_error(status.mapping_error):
        details.append(status.mapping_error or "unknown mapping error")
        return "probable permission/environment issue", details

    if not status.python_module_present:
        details.append("Python module `scscontroller` is not importable.")
        return "Python control module missing", details

    if not status.field_mapping_ok:
        details.append("Configured field mapping does not match the Python control client.")
        return "field mapping mismatch", details

    if not status.ats_running:
        details.append("ATS process is not running.")
        return "ATS not running", details

    if not status.plugin_dll_present:
        details.append("Control plugin DLL is missing from ATS plugins directory.")
        return "plugin missing", details

    details.append(f"{status.mapping_name} is not visible yet.")
    return "named shared memory missing", details


def find_ats_game_dir() -> Path | None:
    for steam_root in KNOWN_STEAM_ROOTS:
        manifest = steam_root / "steamapps" / f"appmanifest_{ATS_APP_ID}.acf"
        if not manifest.exists():
            continue
        installdir = _read_installdir_from_manifest(manifest)
        if not installdir:
            continue
        candidate = steam_root / "steamapps" / "common" / installdir
        if candidate.exists():
            return candidate
    return None


def find_game_log_path() -> Path:
    return Path.home() / "Documents" / "American Truck Simulator" / "game.log.txt"


def read_recent_game_log_lines(limit: int = 200) -> list[str]:
    log_path = find_game_log_path()
    if not log_path.exists():
        return []
    return log_path.read_text(encoding="utf-8", errors="ignore").splitlines()[-limit:]


def process_is_running(process_names: Iterable[str]) -> bool:
    names = {name.lower() for name in process_names}
    try:
        output = subprocess.check_output(["tasklist"], text=True, encoding="utf-8", errors="ignore")
    except Exception:
        return False
    for line in output.splitlines():
        lowered = line.lower()
        if any(name in lowered for name in names):
            return True
    return False


def _read_installdir_from_manifest(path: Path) -> str | None:
    text = path.read_text(encoding="utf-8", errors="ignore")
    match = re.search(r'"installdir"\s+"([^"]+)"', text)
    return match.group(1) if match else None


def _is_permission_like_error(error: str | None) -> bool:
    if not error:
        return False
    return "WinError 5" in error or "access is denied" in error.lower()
