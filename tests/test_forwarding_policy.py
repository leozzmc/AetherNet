from router.policies import next_hop_for, is_final_hop

def test_next_hop_resolution():
    assert next_hop_for("lunar-node", "ground-station") == "leo-relay"
    assert next_hop_for("leo-relay", "ground-station") == "ground-station"

def test_next_hop_no_route():
    assert next_hop_for("ground-station", "mars-node") is None
    assert next_hop_for("unknown-node", "ground-station") is None

def test_final_hop_detection():
    assert is_final_hop("leo-relay", "ground-station") is True
    assert is_final_hop("lunar-node", "ground-station") is False