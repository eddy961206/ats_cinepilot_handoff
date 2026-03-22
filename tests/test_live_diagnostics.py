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
            mapping_name="SCSTelemetrySharedv2_ats",
            mapping_present=False,
            mapping_error="OpenFileMappingW failed with WinError 2",
            game_log_plugin_loaded=True,
            game_log_initialized=False,
        )
    )

    assert category == "named shared memory missing"
    assert any("not initialized" in detail for detail in details)


def test_classify_telemetry_probe_when_layout_is_unsupported():
    category, details = classify_telemetry_probe_status(
        TelemetryProbeStatus(
            ats_running=True,
            plugin_dll_present=True,
            mapping_name="SCSTelemetrySharedv2_ats",
            mapping_present=True,
            decode_supported=False,
            decode_error="unexpected shared memory game tag: 'ets' != 'ats'",
        )
    )

    assert category == "mapping visible but unsupported layout"
    assert any("unexpected shared memory game tag" in detail for detail in details)


def test_classify_telemetry_probe_when_mapping_is_stale():
    category, details = classify_telemetry_probe_status(
        TelemetryProbeStatus(
            ats_running=True,
            plugin_dll_present=True,
            mapping_name="SCSTelemetrySharedv2_ats",
            mapping_present=True,
            decode_supported=True,
            tick_advanced=False,
        )
    )

    assert category == "mapping visible but stale/non-updating"
    assert any("did not change" in detail for detail in details)


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
