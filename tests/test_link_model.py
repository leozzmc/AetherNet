import pytest

from link.link_model import LinkModel


def test_valid_link_model_creation():
    link = LinkModel(
        source="lunar-node",
        target="leo-relay",
        start_time=10,
        end_time=50,
        one_way_delay_ms=250,
        bandwidth_kbit=500,
        loss_percent=1.5,
        bidirectional=True,
        description="Test contact",
    )

    assert link.source == "lunar-node"
    assert link.target == "leo-relay"
    assert link.duration_ticks() == 40
    assert link.one_way_delay_ms == 250
    assert link.bandwidth_kbit == 500
    assert link.loss_percent == 1.5
    assert link.bidirectional is True
    assert link.description == "Test contact"


def test_invalid_link_model_creation():
    with pytest.raises(ValueError, match="start_time must be >= 0"):
        LinkModel("A", "B", start_time=-1, end_time=10)

    with pytest.raises(ValueError, match="end_time must be > start_time"):
        LinkModel("A", "B", start_time=10, end_time=10)

    with pytest.raises(ValueError, match="one_way_delay_ms must be >= 0"):
        LinkModel("A", "B", start_time=0, end_time=10, one_way_delay_ms=-1)

    with pytest.raises(ValueError, match="bandwidth_kbit must be >= 0"):
        LinkModel("A", "B", start_time=0, end_time=10, bandwidth_kbit=-5)

    with pytest.raises(ValueError, match="loss_percent must be between"):
        LinkModel("A", "B", start_time=0, end_time=10, loss_percent=-0.1)

    with pytest.raises(ValueError, match="loss_percent must be between"):
        LinkModel("A", "B", start_time=0, end_time=10, loss_percent=101.0)


def test_link_model_active_boundaries():
    link = LinkModel("A", "B", start_time=5, end_time=10)

    assert link.is_active(4) is False
    assert link.is_active(5) is True
    assert link.is_active(9) is True
    assert link.is_active(10) is False
    assert link.is_active(11) is False


def test_estimated_capacity_calculations():
    link = LinkModel("A", "B", start_time=0, end_time=10, bandwidth_kbit=1000)

    assert link.estimated_capacity_bytes() == 1_250_000

    bundle_size = 250_000
    assert link.estimated_capacity_bundles(bundle_size) == 5


def test_estimated_capacity_bundles_invalid_size():
    link = LinkModel("A", "B", start_time=0, end_time=10, bandwidth_kbit=1000)

    with pytest.raises(ValueError, match="strictly positive"):
        link.estimated_capacity_bundles(0)

    with pytest.raises(ValueError, match="strictly positive"):
        link.estimated_capacity_bundles(-100)


def test_zero_capacity_link():
    link = LinkModel("A", "B", start_time=0, end_time=10, bandwidth_kbit=0)

    assert link.estimated_capacity_bytes() == 0
    assert link.estimated_capacity_bundles(100) == 0