from pathlib import Path
import subprocess
import sys


SCRIPT_PATH = (
    Path(__file__).resolve().parents[1]
    / "scripts"
    / "run_phase6_showcase.py"
)


def run_script() -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, str(SCRIPT_PATH)],
        capture_output=True,
        text=True,
        check=False,
    )


def test_script_exists_and_exits_cleanly() -> None:
    assert SCRIPT_PATH.exists()

    result = run_script()

    assert result.returncode == 0
    assert result.stderr == ""
    assert "Traceback" not in result.stdout


def test_script_stdout_contains_required_sections() -> None:
    result = run_script()
    stdout = result.stdout

    assert "=== Phase-6 Runtime Policy Showcase ===" in stdout
    assert "[Candidate Outputs]" in stdout
    assert "[Policy Differences]" in stdout
    assert "[Interpretation]" in stdout

    assert "Baseline: L1, L2" in stdout
    assert "Conservative: L1" in stdout
    assert "Balanced: L1, L2" in stdout
    assert "Aggressive: L2, L1" in stdout
    assert "Conservative removed compared to Balanced: L2" in stdout
    assert "Aggressive order differs from Balanced: yes" in stdout


def test_script_output_is_deterministic() -> None:
    result_a = run_script()
    result_b = run_script()

    assert result_a.returncode == 0
    assert result_b.returncode == 0
    assert result_a.stdout == result_b.stdout