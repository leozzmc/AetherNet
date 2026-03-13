from typing import Generator

class SimulationClock:
    """A deterministic, tick-based simulation clock."""
    
    def __init__(self, start_time: int = 0, end_time: int = 0, tick_size: int = 1) -> None:
        if end_time < start_time:
            raise ValueError("end_time must be >= start_time")
        if tick_size < 1:
            raise ValueError("tick_size must be >= 1")
            
        self.start_time = start_time
        self.end_time = end_time
        self.tick_size = tick_size

    def ticks(self) -> Generator[int, None, None]:
        """Yields simulation times inclusively."""
        current = self.start_time
        while current <= self.end_time:
            yield current
            current += self.tick_size

    def duration(self) -> int:
        """Returns the total duration of the simulation."""
        return self.end_time - self.start_time