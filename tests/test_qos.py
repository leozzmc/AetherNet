from router.bundle import Bundle
from router.qos import QoSConfig, QoSPolicyHelper


def make_bundle(b_id: str, b_type: str, priority: int = 0, created_at: int = 0) -> Bundle:
    return Bundle(
        id=b_id,
        type=b_type,
        source="A",
        destination="B",
        priority=priority,
        created_at=created_at,
        ttl_sec=3600,
        size_bytes=100,
        payload_ref="ref",
    )


# --- Base Priority Differentiation Tests ---


def test_qos_differentiates_service_classes():
    config = QoSConfig(honor_intrinsic_priority=False)
    helper = QoSPolicyHelper(config)

    b_tel = make_bundle("1", "telemetry")
    b_sci = make_bundle("2", "science")
    b_blk = make_bundle("3", "bulk")
    b_unk = make_bundle("4", "unknown")

    assert helper.base_priority(b_tel) == 100
    assert helper.base_priority(b_sci) == 50
    assert helper.base_priority(b_blk) == 10
    assert helper.base_priority(b_unk) == 0


def test_qos_honors_intrinsic_priority_by_default():
    helper = QoSPolicyHelper()

    b = make_bundle("1", "bulk", priority=99)
    assert helper.base_priority(b) == 99


def test_qos_can_ignore_intrinsic_priority_when_configured():
    config = QoSConfig(honor_intrinsic_priority=False)
    helper = QoSPolicyHelper(config)

    b = make_bundle("1", "bulk", priority=99)
    assert helper.base_priority(b) == 10


# --- Priority Aging Tests ---


def test_qos_aging_increases_effective_priority_over_time():
    config = QoSConfig(
        honor_intrinsic_priority=False,
        bulk_priority=10,
        aging_interval=10,
        aging_step=5,
    )
    helper = QoSPolicyHelper(config)

    b = make_bundle("1", "bulk", created_at=0)

    assert helper.effective_priority(b, current_time=0) == 10
    assert helper.effective_priority(b, current_time=9) == 10
    assert helper.effective_priority(b, current_time=10) == 15
    assert helper.effective_priority(b, current_time=25) == 20


def test_qos_aging_respects_deterministic_cap():
    config = QoSConfig(
        honor_intrinsic_priority=False,
        bulk_priority=10,
        aging_interval=10,
        aging_step=50,
        aging_cap=100,
    )
    helper = QoSPolicyHelper(config)

    b = make_bundle("1", "bulk", created_at=0)

    assert helper.effective_priority(b, current_time=10) == 60
    assert helper.effective_priority(b, current_time=20) == 100
    assert helper.effective_priority(b, current_time=100) == 100


def test_qos_aging_is_disabled_when_interval_is_zero_or_negative():
    config_zero = QoSConfig(
        honor_intrinsic_priority=False,
        bulk_priority=10,
        aging_interval=0,
        aging_step=50,
    )
    helper_zero = QoSPolicyHelper(config_zero)
    bundle_zero = make_bundle("1", "bulk", created_at=0)

    assert helper_zero.effective_priority(bundle_zero, current_time=100) == 10

    config_negative = QoSConfig(
        honor_intrinsic_priority=False,
        bulk_priority=10,
        aging_interval=-5,
        aging_step=50,
    )
    helper_negative = QoSPolicyHelper(config_negative)
    bundle_negative = make_bundle("2", "bulk", created_at=0)

    assert helper_negative.effective_priority(bundle_negative, current_time=100) == 10


def test_qos_aging_is_pure_and_deterministic():
    helper = QoSPolicyHelper()
    b = make_bundle("1", "telemetry", priority=100, created_at=0)

    result_1 = helper.effective_priority(b, 50)
    result_2 = helper.effective_priority(b, 50)

    assert result_1 == result_2
    assert b.priority == 100


def test_qos_aging_handles_future_current_time_gracefully():
    helper = QoSPolicyHelper()
    b = make_bundle("1", "telemetry", priority=100, created_at=50)

    assert helper.effective_priority(b, current_time=0) == 100