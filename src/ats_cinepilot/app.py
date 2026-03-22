from __future__ import annotations

import logging
import time
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Optional

from ats_cinepilot.bridge.capture_dxcam import DXcamCaptureSource, DXcamConfig
from ats_cinepilot.bridge.capture_mss import MSSCaptureSource, MSSConfig
from ats_cinepilot.bridge.manual_override import AlwaysFalseOverrideSource
from ats_cinepilot.bridge.scs_controls import (
    DynamicModuleControlSink,
    ModuleControlConfig,
    NoopControlSink,
    RecordingControlSink,
)
from ats_cinepilot.bridge.scs_telemetry import (
    HttpJsonTelemetrySource,
    JsonTelemetryConfig,
    ReplayTelemetrySource,
    SharedMemoryV2Config,
    SharedMemoryV2TelemetrySource,
)
from ats_cinepilot.control.lateral_pure_pursuit import AdaptivePurePursuit, AdaptivePurePursuitConfig
from ats_cinepilot.control.longitudinal_pid import PidConfig, PidSpeedController
from ats_cinepilot.control.mixer import build_vehicle_command
from ats_cinepilot.domain.enums import DisengageReason, Mode
from ats_cinepilot.domain.state_machine import AutopilotStateMachine
from ats_cinepilot.domain.types import MatchedEdge, PreviewPath, RouteHint, SafetyDecision, SpeedTarget, TelemetryFrame
from ats_cinepilot.map.cache import load_graph_cache
from ats_cinepilot.map.matcher import MatcherConfig, SimplePoseMatcher
from ats_cinepilot.map.spatial_index import SimpleSpatialIndex
from ats_cinepilot.ops.config import cfg_get
from ats_cinepilot.ops.recorder import JsonlRecorder
from ats_cinepilot.ops.telemetry_health import TelemetryFreshnessTracker
from ats_cinepilot.planner.branch_selector import BranchSelector, BranchSelectorConfig
from ats_cinepilot.planner.preview_path import PreviewPlanner, PreviewPlannerConfig
from ats_cinepilot.planner.speed_profile import SpeedPlanner, SpeedPlannerConfig
from ats_cinepilot.route.fusion import build_effective_route_hint
from ats_cinepilot.route.providers import HudRouteProvider, HudRouteProviderConfig, NullRouteProvider
from ats_cinepilot.safety.arbiter import RuleBasedSafetyPolicy, SafetyConfig

logger = logging.getLogger(__name__)


@dataclass
class RuntimeContext:
    telemetry_source: any
    control_sink: any
    route_provider: any
    matcher: SimplePoseMatcher
    preview_planner: PreviewPlanner
    speed_planner: SpeedPlanner
    lateral_controller: AdaptivePurePursuit
    longitudinal_controller: PidSpeedController
    safety_policy: RuleBasedSafetyPolicy
    manual_override: any
    recorder: Optional[JsonlRecorder]
    state_machine: AutopilotStateMachine
    telemetry_health: TelemetryFreshnessTracker
    capture_source: any = None
    status_log_interval_frames: int = 25
    loop_sleep_ms: int = 0
    graph_source: str = "graph_cache"
    alignment_mode: str = "unknown"


class AutopilotApp:
    def __init__(self, cfg: dict, mode: str = "shadow") -> None:
        self.cfg = cfg
        self.mode = mode.lower()
        self.ctx = self._build_runtime(cfg, self.mode)
        self._prev_match: Optional[MatchedEdge] = None
        self._prev_frame: Optional[TelemetryFrame] = None
        self._step_count = 0

    def _build_runtime(self, cfg: dict, mode: str) -> RuntimeContext:
        telemetry_source_name = cfg_get(cfg, "telemetry.source", "json_http")
        if telemetry_source_name == "replay":
            telemetry_source = ReplayTelemetrySource(cfg_get(cfg, "logging.replay_path"))
        elif telemetry_source_name == "shared_memory_v2":
            telemetry_source = SharedMemoryV2TelemetrySource(
                SharedMemoryV2Config(
                    mapping_name=cfg_get(cfg, "telemetry.shared_memory_name", "SCSTelemetrySharedv2_ats"),
                    absolute_x_offset=cfg_get(cfg, "telemetry.absolute_x_offset"),
                    absolute_y_offset=cfg_get(cfg, "telemetry.absolute_y_offset"),
                    absolute_z_offset=cfg_get(cfg, "telemetry.absolute_z_offset"),
                    absolute_value_format=cfg_get(cfg, "telemetry.absolute_value_format", "f64"),
                    pose_frame_mode=cfg_get(cfg, "telemetry.pose_frame_mode", "anchored_local"),
                    absolute_heading_min_distance_m=float(
                        cfg_get(cfg, "telemetry.absolute_heading_min_distance_m", 0.25)
                    ),
                    absolute_discontinuity_distance_m=float(
                        cfg_get(cfg, "telemetry.absolute_discontinuity_distance_m", 25.0)
                    ),
                )
            )
        else:
            telemetry_source = HttpJsonTelemetrySource(
                JsonTelemetryConfig(
                    endpoint=cfg_get(cfg, "telemetry.endpoint"),
                    timeout_s=float(cfg_get(cfg, "telemetry.timeout_s", 0.2)),
                    field_map=dict(cfg_get(cfg, "telemetry.field_map", {})),
                )
            )
        telemetry_source.connect()

        control_sink_name = cfg_get(cfg, "control.sink", "noop")
        if self.mode == "shadow" or control_sink_name == "noop":
            control_sink = NoopControlSink()
        elif control_sink_name == "recording":
            control_sink = RecordingControlSink(cfg_get(cfg, "logging.log_jsonl_path"))
        else:
            control_sink = DynamicModuleControlSink(
                ModuleControlConfig(
                    module_name=cfg_get(cfg, "control.module_name"),
                    class_name=cfg_get(cfg, "control.class_name"),
                    apply_method=cfg_get(cfg, "control.apply_method", ""),
                    neutral_method=cfg_get(cfg, "control.neutral_method", ""),
                    field_mapping=dict(cfg_get(cfg, "control.field_mapping", {})),
                )
            )
        control_sink.connect()

        map_cache_path = cfg_get(cfg, "map.cache_path")
        graph = load_graph_cache(map_cache_path)
        spatial_index = SimpleSpatialIndex(graph)
        matcher = SimplePoseMatcher(
            graph=graph,
            spatial_index=spatial_index,
            config=MatcherConfig(
                query_radius_m=float(cfg_get(cfg, "map.query_radius_m", 45.0)),
            ),
        )

        capture_source = None
        route_provider = NullRouteProvider()
        hud_preset = cfg_get(cfg, "hud.preset_path", "")
        if hud_preset:
            backend = cfg_get(cfg, "capture.backend", "dxcam")
            region = tuple(cfg_get(cfg, "capture.region", [0, 0, 1920, 1080]))
            if backend == "dxcam":
                capture_source = DXcamCaptureSource(
                    DXcamConfig(
                        monitor_index=int(cfg_get(cfg, "capture.monitor_index", 0)),
                        region=region,
                        target_fps=int(cfg_get(cfg, "capture.target_fps", 12)),
                    )
                )
            else:
                capture_source = MSSCaptureSource(MSSConfig(region=region))
            capture_source.start()
            route_provider = HudRouteProvider(
                capture_source,
                HudRouteProviderConfig(
                    preset_path=hud_preset,
                    signature_check=bool(cfg_get(cfg, "hud.signature_check", True)),
                ),
            )

        branch_selector = BranchSelector(graph, BranchSelectorConfig())
        preview_planner = PreviewPlanner(
            graph,
            branch_selector,
            PreviewPlannerConfig(horizon_m=float(cfg_get(cfg, "map.horizon_m", 180.0))),
        )
        speed_planner = SpeedPlanner(
            SpeedPlannerConfig(
                max_lateral_accel_mps2=float(cfg_get(cfg, "planner.max_lateral_accel_mps2", 1.8)),
                curve_speed_floor_mps=float(cfg_get(cfg, "planner.curve_speed_floor_mps", 8.0)),
                junction_speed_cap_mps=float(cfg_get(cfg, "planner.junction_speed_cap_mps", 14.0)),
                user_speed_cap_mps=float(cfg_get(cfg, "truck.preferred_speed_cap_mps", 25.0)),
            )
        )
        lateral_controller = AdaptivePurePursuit(
            AdaptivePurePursuitConfig(
                wheelbase_m=float(cfg_get(cfg, "control_tuning.wheelbase_m", 6.0)),
                steering_gain=float(cfg_get(cfg, "control_tuning.steering_gain", 1.2)),
                max_steering_cmd=float(cfg_get(cfg, "control_tuning.max_steering_cmd", 1.0)),
                min_lookahead_m=float(cfg_get(cfg, "control_tuning.min_lookahead_m", 8.0)),
                max_lookahead_m=float(cfg_get(cfg, "control_tuning.max_lookahead_m", 28.0)),
                lookahead_speed_gain=float(cfg_get(cfg, "control_tuning.lookahead_speed_gain", 1.1)),
            )
        )
        longitudinal_controller = PidSpeedController(
            PidConfig(
                kp=float(cfg_get(cfg, "control_tuning.kp", 0.45)),
                ki=float(cfg_get(cfg, "control_tuning.ki", 0.04)),
                kd=float(cfg_get(cfg, "control_tuning.kd", 0.08)),
                brake_bias=float(cfg_get(cfg, "control_tuning.brake_bias", 0.12)),
                deadband_mps=float(cfg_get(cfg, "control_tuning.deadband_mps", 0.35)),
            )
        )
        safety_policy = RuleBasedSafetyPolicy(
            SafetyConfig(
                min_map_match_confidence=float(cfg_get(cfg, "safety.min_map_match_confidence", 0.60)),
                min_route_confidence=float(cfg_get(cfg, "safety.min_route_confidence", 0.55)),
                max_cross_track_error_m=float(cfg_get(cfg, "safety.max_cross_track_error_m", 1.20)),
                max_heading_error_deg=float(cfg_get(cfg, "safety.max_heading_error_deg", 18.0)),
                overspeed_curve_margin_kph=float(cfg_get(cfg, "safety.overspeed_curve_margin_kph", 8.0)),
            )
        )
        recorder_path = cfg_get(cfg, "logging.log_jsonl_path")
        recorder = JsonlRecorder(recorder_path) if recorder_path else None
        state_machine = AutopilotStateMachine(mode=Mode.SHADOW if mode == "shadow" else Mode.ACTIVE)
        telemetry_health = TelemetryFreshnessTracker(
            timeout_ms=int(cfg_get(cfg, "safety.telemetry_timeout_ms", 250))
        )

        return RuntimeContext(
            telemetry_source=telemetry_source,
            control_sink=control_sink,
            route_provider=route_provider,
            matcher=matcher,
            preview_planner=preview_planner,
            speed_planner=speed_planner,
            lateral_controller=lateral_controller,
            longitudinal_controller=longitudinal_controller,
            safety_policy=safety_policy,
            manual_override=AlwaysFalseOverrideSource(),
            recorder=recorder,
            state_machine=state_machine,
            telemetry_health=telemetry_health,
            capture_source=capture_source,
            status_log_interval_frames=max(1, int(cfg_get(cfg, "debug.status_log_interval_frames", 25))),
            loop_sleep_ms=max(0, int(cfg_get(cfg, "debug.loop_sleep_ms", 0))),
            graph_source=str(
                graph.metadata.get("graph_source", cfg_get(cfg, "map.source_name", Path(map_cache_path).stem))
            ),
            alignment_mode=str(
                graph.metadata.get("alignment_mode", cfg_get(cfg, "map.alignment_mode", "unknown"))
            ),
        )

    def close(self) -> None:
        if self.ctx.capture_source is not None:
            try:
                self.ctx.capture_source.stop()
            except Exception:
                logger.exception("capture stop failed")
        if hasattr(self.ctx.telemetry_source, "close"):
            try:
                self.ctx.telemetry_source.close()
            except Exception:
                logger.exception("telemetry close failed")
        try:
            self.ctx.control_sink.neutralize()
        except Exception:
            logger.exception("control neutralize failed")

    def run_once(self) -> bool:
        frame: TelemetryFrame | None = self.ctx.telemetry_source.read()
        if frame is None:
            return False
        freshness_ms = self.ctx.telemetry_health.observe(frame)

        matched = self.ctx.matcher.match(frame, self._prev_match)
        raw_hint: RouteHint | None = None
        effective_hint: RouteHint | None = None
        path: PreviewPath | None = None
        target: SpeedTarget | None = None

        if matched is not None:
            raw_hint = self.ctx.route_provider.get_hint(frame, matched)
            path = self.ctx.preview_planner.build_path(frame, matched, raw_hint)
            branch_candidate_count = len(self.ctx.preview_planner.graph.outgoing_edges(matched.edge_id))
            effective_hint = build_effective_route_hint(
                raw_hint=raw_hint,
                matched=matched,
                branch_candidate_count=branch_candidate_count,
            )
            target = self.ctx.speed_planner.compute(frame, path)
        else:
            raw_hint = self.ctx.route_provider.get_hint(frame, None)
            effective_hint = raw_hint

        if target is not None and path is not None:
            steering = self.ctx.lateral_controller.steering(frame, path)
            throttle, brake = self.ctx.longitudinal_controller.command(frame, target)
            command = build_vehicle_command(steering, throttle, brake, effective_hint)
        else:
            command = build_vehicle_command(0.0, 0.0, 0.0, effective_hint)

        if self.ctx.manual_override.poll_override():
            decision = self.ctx.safety_policy.evaluate(frame, matched, effective_hint, path, command)
            decision.allow_control = False
            decision.reason = DisengageReason.USER_OVERRIDE
        elif self.ctx.telemetry_health.is_stale(freshness_ms):
            decision = SafetyDecision(False, reason=DisengageReason.TELEMETRY_STALE)
        else:
            decision = self.ctx.safety_policy.evaluate(frame, matched, effective_hint, path, command)

        if self.mode == "active" and decision.allow_control:
            self.ctx.control_sink.apply(command)
        else:
            self.ctx.control_sink.neutralize()

        if self.ctx.recorder:
            telemetry_state = getattr(self.ctx.telemetry_source, "last_state", None)
            pose_delta_m = None
            if self._prev_frame is not None:
                pose_delta_m = (
                    (
                        (frame.pose.world_x - self._prev_frame.pose.world_x) ** 2
                        + (frame.pose.world_z - self._prev_frame.pose.world_z) ** 2
                    )
                    ** 0.5
                )
            self.ctx.recorder.write({
                "frame": frame.to_dict(),
                "matched": asdict(matched) if matched else None,
                "hint": asdict(raw_hint) if raw_hint else None,
                "effective_hint": asdict(effective_hint) if effective_hint else None,
                "target": asdict(target) if target else None,
                "command": asdict(command),
                "decision": {
                    "allow_control": decision.allow_control,
                    "reason": getattr(decision.reason, "name", str(decision.reason)),
                },
                "status": {
                    "graph_source": self.ctx.graph_source,
                    "alignment_mode": self.ctx.alignment_mode,
                    "graph_candidate_count": getattr(self.ctx.matcher.last_diagnostics, "candidate_count", 0),
                    "nearest_edge_distance_m": getattr(
                        self.ctx.matcher.last_diagnostics, "nearest_edge_distance_m", None
                    ),
                    "graph_failure": getattr(self.ctx.matcher.last_diagnostics, "failure_reason", None),
                    "telemetry_freshness_ms": freshness_ms,
                    "pose_source": getattr(telemetry_state, "pose_source", "unknown"),
                    "pose_frame": getattr(telemetry_state, "pose_frame", "unknown"),
                    "heading_source": getattr(telemetry_state, "heading_source", "unknown"),
                    "absolute_heading_rad": getattr(telemetry_state, "absolute_heading_rad", None),
                    "anchor_heading_rad": getattr(telemetry_state, "anchor_heading_rad", None),
                    "anchor_heading_locked": getattr(telemetry_state, "anchor_heading_locked", False),
                    "discontinuity_detected": getattr(telemetry_state, "discontinuity_detected", False),
                    "discontinuity_distance_m": getattr(telemetry_state, "discontinuity_distance_m", None),
                    "anchor_reset_count": getattr(telemetry_state, "anchor_reset_count", 0),
                    "anchor_reset_reason": getattr(telemetry_state, "anchor_reset_reason", None),
                    "pose_delta_m": pose_delta_m,
                    "yaw_rad": frame.pose.yaw_rad,
                    "map_match_confidence": matched.confidence if matched else 0.0,
                    "cross_track_error_m": matched.cross_track_error_m if matched else None,
                    "heading_error_rad": matched.heading_error_rad if matched else None,
                    "route_confidence": effective_hint.confidence if effective_hint else 0.0,
                    "selected_branch": path.branch_id if path else None,
                    "speed_target_mps": target.target_mps if target else None,
                    "safety_decision": getattr(decision.reason, "name", str(decision.reason)),
                },
            })

        self._step_count += 1
        telemetry_state = getattr(self.ctx.telemetry_source, "last_state", None)
        if self._step_count % self.ctx.status_log_interval_frames == 0:
            logger.info(
                "step=%s mode=%s speed=%.2f fresh_ms=%.1f graph=%s/%s cand=%s near=%s fail=%s pose=%s/%s heading_src=%s anchor=%s reset=%s match=%.2f cte=%s heading=%s route=%.2f branch=%s target=%s safety=%s",
                self._step_count,
                self.mode,
                frame.speed_mps,
                freshness_ms,
                self.ctx.graph_source,
                self.ctx.alignment_mode,
                getattr(self.ctx.matcher.last_diagnostics, "candidate_count", 0),
                round(getattr(self.ctx.matcher.last_diagnostics, "nearest_edge_distance_m", 0.0), 2)
                if getattr(self.ctx.matcher.last_diagnostics, "nearest_edge_distance_m", None) is not None
                else None,
                getattr(self.ctx.matcher.last_diagnostics, "failure_reason", None),
                getattr(telemetry_state, "pose_source", "unknown"),
                getattr(telemetry_state, "pose_frame", "unknown"),
                getattr(telemetry_state, "heading_source", "unknown"),
                "locked" if getattr(telemetry_state, "anchor_heading_locked", False) else "pending",
                getattr(telemetry_state, "anchor_reset_reason", None),
                matched.confidence if matched else 0.0,
                round(matched.cross_track_error_m, 2) if matched else None,
                round(matched.heading_error_rad, 3) if matched else None,
                effective_hint.confidence if effective_hint else 0.0,
                path.branch_id if path else None,
                round(target.target_mps, 2) if target else None,
                getattr(decision.reason, "name", str(decision.reason)),
            )

        self._prev_match = matched
        self._prev_frame = frame
        return True

    def run_loop(self, steps: int | None = None) -> None:
        count = 0
        try:
            while True:
                alive = self.run_once()
                if not alive:
                    break
                count += 1
                if steps is not None and count >= steps:
                    break
                if self.ctx.loop_sleep_ms > 0:
                    time.sleep(self.ctx.loop_sleep_ms / 1000.0)
        finally:
            self.close()
