from ats_cinepilot.bridge.live_diagnostics import (
    ControlProbeStatus,
    TelemetryProbeStatus,
    classify_control_probe_status,
    classify_telemetry_probe_status,
)


def test_classify_telemetry_probe_when_plugin_loaded_but_mapping_missing():
    category, details = classify_telemetry_probe_status(
        TelemetryProbeStatus(
            ats_running=True,
            plugin_dll_present=True,
            plugin_dll_path="D:/Steam/.../atssharedplugin64v2.dll",
            mapping_name="SCSTelemetrySharedv2",
            mapping_present=False,
            mapping_error="OpenFileMappingW failed with WinError 2",
            game_log_plugin_loaded=True,
            game_log_initialized=False,
        )
    )

    assert category == "named shared memory missing"
    assert any("not initialized" in detail for detail in details)


def test_classify_control_probe_when_python_module_missing():
    category, details = classify_control_probe_status(
        ControlProbeStatus(
            ats_running=True,
            plugin_dll_present=False,
            python_module_present=False,
            field_mapping_ok=False,
            mapping_name=r"Local\\SCSControls",
            mapping_present=False,
            mapping_error="OpenFileMappingW failed with WinError 2",
        )
    )

    assert category == "Python control module missing"
    assert any("scscontroller" in detail for detail in details)
