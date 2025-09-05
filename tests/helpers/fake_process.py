"""Fake subprocess implementation for testing async process calls."""

from __future__ import annotations

import asyncio
from dataclasses import dataclass, field
from typing import Any, Callable, Optional


@dataclass
class FakeProcess:
    """Mock asyncio subprocess with scriptable output."""
    
    stdout: str = ""
    stderr: str = ""
    returncode: int = 0
    delay: float = 0.0
    _communicate_called: bool = field(default=False, init=False)
    
    async def communicate(self) -> tuple[bytes, bytes]:
        """Simulate process communication."""
        if self.delay > 0:
            await asyncio.sleep(self.delay)
        self._communicate_called = True
        return self.stdout.encode(), self.stderr.encode()
    
    async def wait(self) -> int:
        """Wait for process completion."""
        if self.delay > 0:
            await asyncio.sleep(self.delay)
        return self.returncode


@dataclass
class ProcessSpec:
    """Specification for a fake process behavior."""
    
    command_pattern: str
    stdout: str = ""
    stderr: str = ""
    returncode: int = 0
    delay: float = 0.0
    side_effect: Optional[Callable[[], None]] = None


class FakeProcessFactory:
    """Factory for creating fake subprocess instances."""
    
    def __init__(self):
        self.specs: list[ProcessSpec] = []
        self.call_history: list[dict[str, Any]] = []
        self.default_spec = ProcessSpec(
            command_pattern="*",
            stdout="",
            stderr="",
            returncode=0
        )
    
    def register(
        self,
        command_pattern: str,
        stdout: str = "",
        stderr: str = "",
        returncode: int = 0,
        delay: float = 0.0,
        side_effect: Optional[Callable[[], None]] = None
    ) -> None:
        """Register a process specification."""
        spec = ProcessSpec(
            command_pattern=command_pattern,
            stdout=stdout,
            stderr=stderr,
            returncode=returncode,
            delay=delay,
            side_effect=side_effect
        )
        self.specs.append(spec)
    
    def set_default(
        self,
        stdout: str = "",
        stderr: str = "",
        returncode: int = 0,
        delay: float = 0.0
    ) -> None:
        """Set default behavior for unmatched commands."""
        self.default_spec = ProcessSpec(
            command_pattern="*",
            stdout=stdout,
            stderr=stderr,
            returncode=returncode,
            delay=delay
        )
    
    async def create_subprocess_shell(
        self,
        cmd: str,
        stdout: Any = None,
        stderr: Any = None,
        **kwargs: Any
    ) -> FakeProcess:
        """Create a fake subprocess matching registered specs."""
        # Record the call
        self.call_history.append({
            "cmd": cmd,
            "stdout": stdout,
            "stderr": stderr,
            "kwargs": kwargs
        })
        
        # Find matching spec
        spec = self._find_spec(cmd)
        
        # Execute side effect if any
        if spec.side_effect:
            spec.side_effect()
        
        # Create fake process
        return FakeProcess(
            stdout=spec.stdout,
            stderr=spec.stderr,
            returncode=spec.returncode,
            delay=spec.delay
        )
    
    def _find_spec(self, cmd: str) -> ProcessSpec:
        """Find the first matching spec for a command."""
        for spec in self.specs:
            if spec.command_pattern == "*":
                continue
            if spec.command_pattern in cmd:
                return spec
        return self.default_spec
    
    def assert_called_with(self, command_pattern: str) -> None:
        """Assert that a command matching the pattern was called."""
        for call in self.call_history:
            if command_pattern in call["cmd"]:
                return
        raise AssertionError(
            f"No call found matching pattern: {command_pattern}\n"
            f"Actual calls: {[c['cmd'] for c in self.call_history]}"
        )
    
    def assert_not_called_with(self, command_pattern: str) -> None:
        """Assert that no command matching the pattern was called."""
        for call in self.call_history:
            if command_pattern in call["cmd"]:
                raise AssertionError(
                    f"Unexpected call found matching pattern: {command_pattern}\n"
                    f"Call: {call['cmd']}"
                )
    
    def reset(self) -> None:
        """Reset the factory state."""
        self.specs.clear()
        self.call_history.clear()
    
    @property
    def call_count(self) -> int:
        """Get the number of subprocess calls made."""
        return len(self.call_history)