"""Time control utilities for deterministic testing."""

from __future__ import annotations

import time
from datetime import datetime, timedelta, timezone
from typing import Any, Generator

import pytest
from freezegun import freeze_time


# Standard test time: Monday, September 1, 2025, 9:00 AM UTC
STANDARD_TEST_TIME = datetime(2025, 9, 1, 9, 0, 0, tzinfo=timezone.utc)


class FakeClock:
    """Controllable clock for testing time-dependent code."""
    
    def __init__(self, start_time: datetime | None = None):
        self.current_time = start_time or STANDARD_TEST_TIME
        self._frozen = False
        self._ticks = 0
    
    def now(self) -> datetime:
        """Get the current time."""
        if not self._frozen:
            # Auto-advance by 1 second per call if not frozen
            self.tick(seconds=1)
        return self.current_time
    
    def tick(self, **kwargs: Any) -> datetime:
        """Advance the clock by the specified amount."""
        self._ticks += 1
        delta = timedelta(**kwargs)
        self.current_time += delta
        return self.current_time
    
    def freeze(self) -> None:
        """Freeze the clock at the current time."""
        self._frozen = True
    
    def unfreeze(self) -> None:
        """Unfreeze the clock."""
        self._frozen = False
    
    def set_time(self, new_time: datetime) -> None:
        """Set the clock to a specific time."""
        self.current_time = new_time
    
    def reset(self) -> None:
        """Reset the clock to the standard test time."""
        self.current_time = STANDARD_TEST_TIME
        self._frozen = False
        self._ticks = 0
    
    @property
    def tick_count(self) -> int:
        """Get the number of times the clock has ticked."""
        return self._ticks


@pytest.fixture
def frozen_clock() -> Generator[FakeClock, None, None]:
    """Fixture providing a frozen test clock."""
    clock = FakeClock()
    clock.freeze()
    yield clock
    clock.reset()


@pytest.fixture
def auto_clock() -> Generator[FakeClock, None, None]:
    """Fixture providing an auto-advancing test clock."""
    clock = FakeClock()
    yield clock
    clock.reset()


def frozen_test_time(
    dt: datetime | None = None
) -> Generator[Any, None, None]:
    """Context manager for freezing time at a specific point."""
    target_time = dt or STANDARD_TEST_TIME
    with freeze_time(target_time) as frozen:
        yield frozen


def measure_duration(func: Any) -> tuple[Any, float]:
    """Measure the execution time of a function."""
    start = time.perf_counter()
    result = func()
    duration = time.perf_counter() - start
    return result, duration


async def measure_async_duration(func: Any) -> tuple[Any, float]:
    """Measure the execution time of an async function."""
    start = time.perf_counter()
    result = await func()
    duration = time.perf_counter() - start
    return result, duration


class TimeTravel:
    """Helper for testing time-dependent behavior."""
    
    def __init__(self, clock: FakeClock):
        self.clock = clock
        self.checkpoints: dict[str, datetime] = {}
    
    def checkpoint(self, name: str) -> datetime:
        """Mark a named checkpoint in time."""
        current = self.clock.now()
        self.checkpoints[name] = current
        return current
    
    def elapsed_since(self, checkpoint: str) -> timedelta:
        """Get elapsed time since a checkpoint."""
        if checkpoint not in self.checkpoints:
            raise ValueError(f"Unknown checkpoint: {checkpoint}")
        return self.clock.now() - self.checkpoints[checkpoint]
    
    def advance_to_next_hour(self) -> datetime:
        """Advance clock to the next hour boundary."""
        current = self.clock.now()
        next_hour = current.replace(
            hour=current.hour + 1,
            minute=0,
            second=0,
            microsecond=0
        )
        self.clock.set_time(next_hour)
        return next_hour
    
    def advance_to_next_day(self) -> datetime:
        """Advance clock to midnight of the next day."""
        current = self.clock.now()
        next_day = (current + timedelta(days=1)).replace(
            hour=0,
            minute=0,
            second=0,
            microsecond=0
        )
        self.clock.set_time(next_day)
        return next_day
    
    def simulate_work_hours(self, days: int = 1) -> None:
        """Simulate work hours (9 AM - 5 PM) for the specified days."""
        for _ in range(days):
            # Start at 9 AM
            work_start = self.clock.now().replace(hour=9, minute=0)
            self.clock.set_time(work_start)
            
            # Work for 8 hours with hourly ticks
            for hour in range(8):
                self.clock.tick(hours=1)
            
            # Jump to next day 9 AM
            next_day = work_start + timedelta(days=1)
            self.clock.set_time(next_day)