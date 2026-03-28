from ats_cinepilot.app import _apply_cv_guard_to_decision, _should_apply_active_control
from ats_cinepilot.domain.enums import DisengageReason
from ats_cinepilot.domain.types import SafetyDecision


def test_demo_override_only_applies_for_route_or_match_failures():
    decision = SafetyDecision(False, reason=DisengageReason.MATCH_LOST)

    assert _should_apply_active_control(
        decision,
        demo_control_allowed=True,
        demo_brake_assist_active=False,
    )


def test_demo_override_does_not_ignore_telemetry_stale():
    decision = SafetyDecision(False, reason=DisengageReason.TELEMETRY_STALE)

    assert not _should_apply_active_control(
        decision,
        demo_control_allowed=True,
        demo_brake_assist_active=True,
    )


def test_demo_brake_assist_can_run_for_demo_guard_only():
    decision = SafetyDecision(False, reason=DisengageReason.DEMO_GUARD)

    assert _should_apply_active_control(
        decision,
        demo_control_allowed=False,
        demo_brake_assist_active=True,
    )


def test_cv_observer_exception_disengages_when_cv_guard_is_enabled():
    decision = SafetyDecision(True, reason=None)

    resolved = _apply_cv_guard_to_decision(
        decision,
        cv_guard_triggered=False,
        cv_guard_enabled=True,
        observer_exception=True,
    )

    assert resolved.allow_control is False
    assert resolved.reason == DisengageReason.DEMO_GUARD


def test_cv_guard_disabled_keeps_decision_on_observer_exception():
    decision = SafetyDecision(True, reason=None)

    resolved = _apply_cv_guard_to_decision(
        decision,
        cv_guard_triggered=False,
        cv_guard_enabled=False,
        observer_exception=True,
    )

    assert resolved is decision
