import json
import pytest

from router.bundle import Bundle, BundleStatus
from protocol.serializer import BundleSerializerV1


@pytest.fixture
def sample_bundle() -> Bundle:
    return Bundle(
        id="serialize-test-1",
        type="telemetry",
        source="lunar-node",
        destination="ground-station",
        priority=100,
        created_at=10,
        ttl_sec=3600,
        size_bytes=250,
        payload_ref="payloads/telemetry/test.json",
        status=BundleStatus.FORWARDING,
        next_hop="leo-relay",
    )


def test_serializer_dict_roundtrip(sample_bundle):
    data = BundleSerializerV1.to_dict(sample_bundle)
    assert isinstance(data, dict)

    restored = BundleSerializerV1.from_dict(data)
    assert restored.id == sample_bundle.id
    assert restored.status == BundleStatus.FORWARDING
    assert restored.next_hop == sample_bundle.next_hop


def test_serializer_json_deterministic(sample_bundle):
    json_str1 = BundleSerializerV1.to_json(sample_bundle)
    json_str2 = BundleSerializerV1.to_json(sample_bundle)

    assert json_str1 == json_str2

    expected = json.dumps(
        BundleSerializerV1.to_dict(sample_bundle),
        separators=(",", ":"),
        sort_keys=True,
    )
    assert json_str1 == expected


def test_serializer_json_roundtrip(sample_bundle):
    json_str = BundleSerializerV1.to_json(sample_bundle)
    assert isinstance(json_str, str)

    restored = BundleSerializerV1.from_json(json_str)
    assert restored.id == sample_bundle.id
    assert restored.size_bytes == 250
    assert restored.type == "telemetry"


def test_serializer_bytes_roundtrip(sample_bundle):
    raw_bytes = BundleSerializerV1.to_bytes(sample_bundle)
    assert isinstance(raw_bytes, bytes)

    restored = BundleSerializerV1.from_bytes(raw_bytes)
    assert restored.id == sample_bundle.id
    assert restored.type == "telemetry"


def test_from_json_malformed_raises_value_error():
    with pytest.raises(ValueError, match="Malformed JSON string"):
        BundleSerializerV1.from_json("{bad_json: true}")


def test_from_json_non_object_raises_value_error():
    with pytest.raises(ValueError, match="top-level value must be an object"):
        BundleSerializerV1.from_json('["not", "a", "bundle"]')


def test_from_bytes_invalid_utf8_raises_value_error():
    bad_bytes = b"\xff\xfe\xfd"
    with pytest.raises(ValueError, match="Invalid UTF-8 bytes"):
        BundleSerializerV1.from_bytes(bad_bytes)


def test_from_bytes_malformed_json_raises_value_error():
    bad_json_bytes = b'{"missing_quote: 123}'
    with pytest.raises(ValueError, match="Malformed JSON string"):
        BundleSerializerV1.from_bytes(bad_json_bytes)