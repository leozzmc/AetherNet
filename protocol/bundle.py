import json
from typing import Dict, Any

from router.bundle import Bundle, BundleStatus


class BundleProtocolV1:
    """
    Canonical protocol-layer adapter for AetherNet Bundles.
    """

    @staticmethod
    def to_dict(bundle: Bundle) -> Dict[str, Any]:
        data = bundle.to_dict()
        if isinstance(data.get("status"), BundleStatus):
            data["status"] = data["status"].value
        return data

    @staticmethod
    def from_dict(data: Dict[str, Any]) -> Bundle:
        parsed = dict(data)

        if "status" in parsed and isinstance(parsed["status"], str):
            parsed["status"] = BundleStatus(parsed["status"])

        allowed_fields = {
            "id",
            "type",
            "source",
            "destination",
            "next_hop",
            "priority",
            "created_at",
            "ttl_sec",
            "size_bytes",
            "payload_ref",
            "status",
            "is_fragment",
            "original_bundle_id",
            "fragment_index",
            "total_fragments",
            "custody_requested", # Wave-29
            "custody_holder"     # Wave-29
        }

        filtered = {k: v for k, v in parsed.items() if k in allowed_fields}
        return Bundle(**filtered)

    @staticmethod
    def size_bytes(bundle: Bundle) -> int:
        header = BundleProtocolV1.to_dict(bundle).copy()
        header.pop("size_bytes", None)
        metadata_bytes = len(
            json.dumps(header, separators=(",", ":"), sort_keys=True).encode("utf-8")
        )
        return metadata_bytes + bundle.size_bytes