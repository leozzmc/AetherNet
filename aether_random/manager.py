import hashlib
import random
from typing import Dict


def derive_stream_seed(master_seed: int, stream_name: str) -> int:
    """
    Derive a deterministic per-stream seed from a master seed and stream name.

    This intentionally avoids Python's built-in hash(), which is not stable
    across interpreter runs.
    """
    seed_material = f"{master_seed}::{stream_name}".encode("utf-8")
    digest = hashlib.sha256(seed_material).digest()
    return int.from_bytes(digest[:8], byteorder="big", signed=False)


class SeedRegistry:
    """
    Lightweight registry for recording named stream seeds.

    Wave-73 keeps this intentionally simple so it can later be attached to
    artifact / manifest export without affecting simulator behavior.
    """

    def __init__(self) -> None:
        self._registry: Dict[str, int] = {}

    def register(self, stream_name: str, seed: int) -> None:
        self._registry[stream_name] = seed

    def export(self) -> Dict[str, int]:
        return dict(self._registry)


class RandomStream:
    """
    Isolated deterministic random number stream.

    Each instance owns its own random.Random(seed), so stream state is isolated
    and never touches Python's global random state.
    """

    def __init__(self, seed: int) -> None:
        self._seed = seed
        self._rng = random.Random(seed)

    @property
    def seed(self) -> int:
        return self._seed

    def random(self) -> float:
        return self._rng.random()

    def randint(self, a: int, b: int) -> int:
        return self._rng.randint(a, b)


class RandomManager:
    """
    Deterministic randomness foundation for Phase-6 Wave-73.

    Contract:
    - master_seed is the deterministic root
    - each named stream gets a deterministic derived seed
    - get_stream(name) returns a cached, stateful stream
    - create_stream(name) returns a fresh stream from the same derived seed

    This module must have zero integration impact in Wave-73.
    """

    def __init__(self, master_seed: int) -> None:
        self.master_seed = master_seed
        self._registry = SeedRegistry()
        self._streams: Dict[str, RandomStream] = {}

    @property
    def registry(self) -> SeedRegistry:
        return self._registry

    def get_stream_seed(self, name: str) -> int:
        return derive_stream_seed(self.master_seed, name)

    def get_stream(self, name: str) -> RandomStream:
        """
        Return a cached, stateful RandomStream.

        Repeated calls with the same name on the same manager return the same
        object, so stream state continues advancing.
        """
        if name not in self._streams:
            derived_seed = self.get_stream_seed(name)
            self._registry.register(name, derived_seed)
            self._streams[name] = RandomStream(derived_seed)
        return self._streams[name]

    def create_stream(self, name: str) -> RandomStream:
        """
        Return a fresh RandomStream initialized from the deterministic seed.

        This does not reuse cached stream state.
        """
        derived_seed = self.get_stream_seed(name)
        self._registry.register(name, derived_seed)
        return RandomStream(derived_seed)