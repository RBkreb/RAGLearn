"""Memory monitoring module for detecting memory leaks during indexing."""

from __future__ import annotations

import gc
import tracemalloc
from dataclasses import dataclass, field
from typing import Any


@dataclass
class MemorySnapshot:
    """Immutable memory snapshot at a point in time.

    Attributes:
        operation: Name of the operation that was performed.
        current_mb: Current memory usage in MB.
        peak_mb: Peak memory usage in MB.
        delta_mb: Change in memory since last snapshot.
        timestamp: Operation label or description.
    """

    operation: str
    current_mb: float
    peak_mb: float
    delta_mb: float = 0.0
    timestamp: str = ""


class MemoryMonitor:
    """Tracks memory usage during indexing operations.

    This class provides memory tracking capabilities to detect
    potential memory leaks during long-running indexing operations.

    Attributes:
        threshold_mb: Memory threshold in MB that triggers leak warnings.
        snapshots: List of memory snapshots taken during operation.
        _baseline_mb: Baseline memory usage at start.
    """

    def __init__(self, threshold_mb: float = 500.0) -> None:
        """Initialize MemoryMonitor.

        Args:
            threshold_mb: Memory threshold in MB. Default 500MB.
        """
        self.threshold_mb = threshold_mb
        self.snapshots: list[MemorySnapshot] = []
        self._baseline_mb: float = 0.0
        self._last_mb: float = 0.0
        self._enabled: bool = False

    def start(self) -> None:
        """Start memory tracking."""
        if not self._enabled:
            gc.collect()
            tracemalloc.start()
            current, _ = tracemalloc.get_traced_memory()
            self._baseline_mb = current / (1024 * 1024)
            self._last_mb = self._baseline_mb
            self._enabled = True

    def stop(self) -> None:
        """Stop memory tracking and cleanup."""
        if self._enabled:
            tracemalloc.stop()
            self._enabled = False

    def take_snapshot(self, operation: str) -> MemorySnapshot:
        """Take a memory snapshot with current memory usage.

        Args:
            operation: Name/label for this operation.

        Returns:
            MemorySnapshot with current memory stats.
        """
        if not self._enabled:
            self.start()

        gc.collect()
        current, peak = tracemalloc.get_traced_memory()
        current_mb = current / (1024 * 1024)
        peak_mb = peak / (1024 * 1024)
        delta_mb = current_mb - self._last_mb

        snapshot = MemorySnapshot(
            operation=operation,
            current_mb=current_mb,
            peak_mb=peak_mb,
            delta_mb=delta_mb,
            timestamp=operation,
        )

        self.snapshots.append(snapshot)
        self._last_mb = current_mb

        return snapshot

    def check_leak(self) -> bool:
        """Detect if memory is growing without release.

        Returns:
            True if memory growth exceeds threshold since baseline.
        """
        if not self._enabled:
            return False

        current, _ = tracemalloc.get_traced_memory()
        current_mb = current / (1024 * 1024)
        growth_mb = current_mb - self._baseline_mb

        return growth_mb > self.threshold_mb

    def get_leak_warning(self) -> str | None:
        """Get a warning message if memory leak detected.

        Returns:
            Warning message or None if no leak detected.
        """
        if not self.check_leak():
            return None

        current, _ = tracemalloc.get_traced_memory()
        current_mb = current / (1024 * 1024)
        growth_mb = current_mb - self._baseline_mb

        return (
            f"Memory leak detected: "
            f"Current {current_mb:.1f}MB, "
            f"Baseline {self._baseline_mb:.1f}MB, "
            f"Growth {growth_mb:.1f}MB "
            f"(threshold: {self.threshold_mb}MB)"
        )

    def get_report(self) -> str:
        """Return formatted memory usage report.

        Returns:
            Formatted string with memory usage across all snapshots.
        """
        if not self.snapshots:
            return "No memory snapshots recorded."

        lines = ["Memory Usage Report:", "-" * 40]
        lines.append(f"Baseline: {self._baseline_mb:.1f}MB")

        for i, snap in enumerate(self.snapshots):
            lines.append(
                f"  {i + 1}. {snap.operation}: "
                f"current={snap.current_mb:.1f}MB, "
                f"delta={snap.delta_mb:+.1f}MB, "
                f"peak={snap.peak_mb:.1f}MB"
            )

        current, peak = tracemalloc.get_traced_memory()
        current_mb = current / (1024 * 1024)
        peak_mb = peak / (1024 * 1024)
        growth_mb = current_mb - self._baseline_mb

        lines.append("-" * 40)
        lines.append(
            f"Current: {current_mb:.1f}MB, "
            f"Peak: {peak_mb:.1f}MB, "
            f"Growth: {growth_mb:+.1f}MB"
        )

        warning = self.get_leak_warning()
        if warning:
            lines.append(f"WARNING: {warning}")

        return "\n".join(lines)

    def reset(self) -> None:
        """Reset all snapshots and baseline."""
        self.snapshots.clear()
        self._last_mb = self._baseline_mb

    def __enter__(self) -> "MemoryMonitor":
        """Enter context manager."""
        self.start()
        return self

    def __exit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        """Exit context manager."""
        self.stop()