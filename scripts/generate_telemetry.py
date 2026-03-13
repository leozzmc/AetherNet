import json
import time
import uuid
from pathlib import Path


def generate() -> Path:
    repo_root = Path(__file__).resolve().parents[1]
    output_dir = repo_root / "payloads" / "telemetry"
    output_dir.mkdir(parents=True, exist_ok=True)

    payload = {
        "sensor_id": "lunar-rover-therm",
        "temperature_c": -18.5,
        "battery_pct": 87.2,
        "timestamp": int(time.time())
    }

    filename = output_dir / f"telemetry_{uuid.uuid4().hex[:8]}.json"
    with filename.open("w", encoding="utf-8") as f:
        json.dump(payload, f, indent=2)

    print(f"Generated telemetry payload: {filename}")
    return filename


if __name__ == "__main__":
    generate()