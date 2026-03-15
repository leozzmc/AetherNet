import json
from typing import Dict, Any

from router.bundle import Bundle
from protocol.bundle import BundleProtocolV1


class BundleSerializerV1:
    """
    Serialization layer for AetherNet bundles.

    Provides safe, deterministic conversion between Bundle objects
    and dict, JSON string, or UTF-8 encoded JSON bytes.

    Current wire format:
    - canonical JSON string
    - UTF-8 encoded JSON bytes

    This is intentionally conservative for Phase-2.
    """

    @staticmethod
    def to_dict(bundle: Bundle) -> Dict[str, Any]:
        """Convert a Bundle to a canonical protocol dictionary."""
        return BundleProtocolV1.to_dict(bundle)

    @staticmethod
    def from_dict(data: Dict[str, Any]) -> Bundle:
        """Reconstruct a Bundle from a canonical protocol dictionary."""
        return BundleProtocolV1.from_dict(data)

    @staticmethod
    def to_json(bundle: Bundle) -> str:
        """
        Serialize a Bundle to a deterministic JSON string.

        Determinism is ensured with:
        - sort_keys=True
        - compact separators
        """
        data = BundleSerializerV1.to_dict(bundle)
        return json.dumps(data, separators=(",", ":"), sort_keys=True)

    @staticmethod
    def from_json(raw: str) -> Bundle:
        """
        Deserialize a JSON string back into a Bundle.

        Raises:
            ValueError: if JSON is malformed, top-level type is invalid,
            or the bundle data is invalid.
        """
        try:
            data = json.loads(raw)
        except json.JSONDecodeError as e:
            raise ValueError(f"Malformed JSON string: {e}") from e

        if not isinstance(data, dict):
            raise ValueError("Invalid bundle JSON: top-level value must be an object")

        try:
            return BundleSerializerV1.from_dict(data)
        except (TypeError, KeyError, ValueError) as e:
            raise ValueError(f"Invalid bundle data in JSON: {e}") from e

    @staticmethod
    def to_bytes(bundle: Bundle) -> bytes:
        """
        Serialize a Bundle to UTF-8 encoded JSON bytes.
        """
        return BundleSerializerV1.to_json(bundle).encode("utf-8")

    @staticmethod
    def from_bytes(raw: bytes) -> Bundle:
        """
        Deserialize UTF-8 encoded JSON bytes back into a Bundle.

        Raises:
            ValueError: if bytes are not valid UTF-8 or do not contain valid bundle JSON.
        """
        try:
            json_str = raw.decode("utf-8")
        except UnicodeDecodeError as e:
            raise ValueError(f"Invalid UTF-8 bytes: {e}") from e

        return BundleSerializerV1.from_json(json_str)