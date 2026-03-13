from dataclasses import dataclass
from typing import Optional
from router.bundle import Bundle

@dataclass
class StoreEntry:
    """Represents a bundle stored locally on disk within the DTN Object Store."""
    bundle: Bundle
    local_file_path: str
    persisted_at: int
    is_locked: bool = False  # Used to prevent reading while writing or forwarding