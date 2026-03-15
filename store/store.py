import json
from pathlib import Path
from typing import List

from router.bundle import Bundle, BundleStatus
from protocol.bundle import BundleProtocolV1


class DTNStore:
    """A filesystem-backed DTN object store for bundle metadata."""

    def __init__(self, root_dir: str | Path) -> None:
        self.root_dir = Path(root_dir)
        self.root_dir.mkdir(parents=True, exist_ok=True)

    def _get_path(self, bundle_id: str) -> Path:
        return self.root_dir / f"{bundle_id}.json"

    def save_bundle(self, bundle: Bundle) -> Path:
        """Serialize and persist a bundle's metadata to disk."""
        path = self._get_path(bundle.id)
        with path.open("w", encoding="utf-8") as f:
            # Delegate to the Protocol layer for canonical serialization format
            json.dump(BundleProtocolV1.to_dict(bundle), f, indent=2)
        return path

    def load_bundle(self, bundle_id: str) -> Bundle:
        """Load bundle metadata from disk and reconstruct a Bundle object."""
        path = self._get_path(bundle_id)
        if not path.exists():
            raise FileNotFoundError(f"Bundle {bundle_id} not found in store.")

        with path.open("r", encoding="utf-8") as f:
            data = json.load(f)

        try:
            # Delegate to the Protocol layer for safe deserialization
            return BundleProtocolV1.from_dict(data)
        except (KeyError, TypeError, ValueError) as e:
            raise ValueError(f"Malformed bundle data for {bundle_id}: {e}") from e

    def delete_bundle(self, bundle_id: str) -> bool:
        """Delete a bundle metadata file. Return True if deleted, else False."""
        path = self._get_path(bundle_id)
        if path.exists():
            path.unlink()
            return True
        return False

    def exists(self, bundle_id: str) -> bool:
        return self._get_path(bundle_id).exists()

    def list_bundle_ids(self) -> List[str]:
        return sorted(p.stem for p in self.root_dir.glob("*.json"))