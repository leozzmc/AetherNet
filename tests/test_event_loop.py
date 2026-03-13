import pytest
from sim.event_loop import SimulationClock

def test_inclusive_tick_generation():
    clock = SimulationClock(start_time=2, end_time=5, tick_size=1)
    ticks = list(clock.ticks())
    assert ticks == [2, 3, 4, 5]

def test_invalid_constructor_arguments():
    with pytest.raises(ValueError, match="end_time must be >= start_time"):
        SimulationClock(start_time=10, end_time=5)
        
    with pytest.raises(ValueError, match="tick_size must be >= 1"):
        SimulationClock(start_time=0, end_time=10, tick_size=0)

def test_clock_duration():
    clock = SimulationClock(start_time=5, end_time=20, tick_size=2)
    assert clock.duration() == 15