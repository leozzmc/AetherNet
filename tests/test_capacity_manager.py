import pytest

from router.contact_manager import Contact
from link.capacity_manager import ContactWindowCapacityManager


@pytest.fixture
def manager() -> ContactWindowCapacityManager:
    return ContactWindowCapacityManager()


@pytest.fixture
def unlimited_contact() -> Contact:
    return Contact("earth", "moon", 0, 10, 100, 1000)


@pytest.fixture
def finite_contact() -> Contact:
    return Contact("earth", "moon", 0, 10, 100, 1000, capacity_bundles=2)


@pytest.fixture
def zero_contact() -> Contact:
    return Contact("earth", "moon", 0, 10, 100, 1000, capacity_bundles=0)


def test_unlimited_capacity(manager, unlimited_contact):
    assert manager.can_forward(unlimited_contact) is True
    assert manager.remaining_bundle_capacity(unlimited_contact) is None

    manager.record_forward(unlimited_contact)
    manager.record_forward(unlimited_contact)
    assert manager.can_forward(unlimited_contact) is True
    assert manager.remaining_bundle_capacity(unlimited_contact) is None


def test_zero_capacity(manager, zero_contact):
    assert manager.can_forward(zero_contact) is False
    assert manager.remaining_bundle_capacity(zero_contact) == 0


def test_finite_capacity_exhaustion(manager, finite_contact):
    assert manager.can_forward(finite_contact) is True
    assert manager.remaining_bundle_capacity(finite_contact) == 2

    manager.record_forward(finite_contact)
    assert manager.can_forward(finite_contact) is True
    assert manager.remaining_bundle_capacity(finite_contact) == 1

    manager.record_forward(finite_contact)
    assert manager.can_forward(finite_contact) is False
    assert manager.remaining_bundle_capacity(finite_contact) == 0


def test_record_forward_on_exhausted_contact_raises(manager):
    contact = Contact("earth", "moon", 0, 10, 100, 1000, capacity_bundles=1)
    manager.record_forward(contact)

    with pytest.raises(ValueError, match="exhausted contact window"):
        manager.record_forward(contact)


def test_different_windows_do_not_interfere(manager):
    contact_w1 = Contact("earth", "moon", 0, 10, 100, 1000, capacity_bundles=1)
    contact_w2 = Contact("earth", "moon", 20, 30, 100, 1000, capacity_bundles=1)

    manager.record_forward(contact_w1)

    assert manager.can_forward(contact_w1) is False
    assert manager.can_forward(contact_w2) is True


def test_reset_clears_usage(manager):
    contact = Contact("earth", "moon", 0, 10, 100, 1000, capacity_bundles=1)

    manager.record_forward(contact)
    assert manager.can_forward(contact) is False

    manager.reset()
    assert manager.can_forward(contact) is True
    assert manager.remaining_bundle_capacity(contact) == 1