import json
import time
import uuid
from pathlib import Path


def generate() -> Path:
    repo_root = Path(__file__).resolve().parents[1]
    output_dir = repo_root / "payloads" / "science"
    output_dir.mkdir(parents=True, exist_ok=True)

    payload = {
        "instrument": "high-res-cam",
        "target": "crater-tycho",
        "exposure_ms": 1500,
        "resolution": "4096x4096",
        "raw_data_pointer": "/dev/null",
        "timestamp": int(time.time())
    }

    filename = output_dir / f"science_{uuid.uuid4().hex[:8]}.json"
    with filename.open("w", encoding="utf-8") as f:
        json.dump(payload, f, indent=2)

    print(f"Generated science payload: {filename}")
    return filename


if __name__ == "__main__":
    generate()