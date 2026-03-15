import json
from typing import Dict, Any

from router.bundle import Bundle, BundleStatus


class BundleProtocolV1:
    """
    Canonical protocol-layer adapter for AetherNet bundles.

    This layer provides a stable serialization contract without
    modifying the Phase-1 domain model.
    """

    @staticmethod
    def to_dict(bundle: Bundle) -> Dict[str, Any]:
        """Serialize a Bundle into protocol format."""
        data = bundle.to_dict()

        # Protocol explicitly stores enum as string
        if isinstance(data.get("status"), BundleStatus):
            data["status"] = data["status"].value

        return data

    @staticmethod
    def from_dict(data: Dict[str, Any]) -> Bundle:
        """Deserialize protocol dictionary into Bundle object."""

        parsed = dict(data)

        # restore enum safely
        if "status" in parsed and isinstance(parsed["status"], str):
            parsed["status"] = BundleStatus(parsed["status"])

        # whitelist bundle fields only
        allowed_fields = {
            "id",
            "type",
            "source",
            "destination",
            "priority",
            "created_at",
            "ttl_sec",
            "size_bytes",
            "payload_ref",
            "status",
            "next_hop",
        }

        filtered = {k: v for k, v in parsed.items() if k in allowed_fields}

        return Bundle(**filtered)

    @staticmethod
    def size_bytes(bundle: Bundle) -> int:
        """
        Estimate total transport size.

        Transport size = metadata header + payload size.
        """

        header = BundleProtocolV1.to_dict(bundle).copy()

        # Remove payload size from metadata header
        header.pop("size_bytes", None)

        metadata_bytes = len(
            json.dumps(header, separators=(",", ":"), sort_keys=True).encode("utf-8")
        )

        return metadata_bytes + bundle.size_bytes