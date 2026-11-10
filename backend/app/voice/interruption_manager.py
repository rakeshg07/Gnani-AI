"""Interruption & Turn Cancellation Manager for VoiceIQ Real-Time Sessions.

Implements instant 'Barge-In' support:
- Cancels in-flight LLM generation and Timbre TTS jobs when customer starts speaking.
- Invalidates delayed or lingering audio chunks from old turns.
- Generates monotonic, unique turn IDs to prevent overlapping audio responses.
"""
import asyncio
from typing import Optional, Set
from app.core.logging import logger


class InterruptionManager:
    """Manages active turn lifecycle, task cancellation, and barge-in tracking."""

    def __init__(self, session_id: str):
        self.session_id = session_id
        self._current_turn_counter = 0
        self._active_turn_id: str = "turn_0"
        self._active_tasks: Set[asyncio.Task] = set()
        self._is_interrupted = False

    @property
    def current_turn_id(self) -> str:
        return self._active_turn_id

    def next_turn(self) -> str:
        """Create a new turn ID for a fresh conversation turn."""
        self.cancel_current_turn()
        self._current_turn_counter += 1
        self._active_turn_id = f"turn_{self._current_turn_counter}"
        self._is_interrupted = False
        return self._active_turn_id

    def register_task(self, task: asyncio.Task, turn_id: str):
        """Associate an asyncio task (LLM or TTS) with a turn."""
        if turn_id != self._active_turn_id:
            # Already outdated, cancel immediately
            task.cancel()
            return

        self._active_tasks.add(task)
        task.add_done_callback(lambda t: self._active_tasks.discard(t))

    def cancel_current_turn(self) -> str:
        """
        Immediately cancel all pending tasks for the current turn.
        Returns the interrupted turn ID.
        """
        interrupted_turn = self._active_turn_id
        self._is_interrupted = True

        for task in list(self._active_tasks):
            if not task.done():
                logger.info(f"[{self.session_id}] Canceling task {task.get_name()} for turn {interrupted_turn}")
                task.cancel()

        self._active_tasks.clear()
        return interrupted_turn

    def is_turn_valid(self, turn_id: str) -> bool:
        """Verify whether an audio chunk or token belongs to the active, uninterrupted turn."""
        return turn_id == self._active_turn_id and not self._is_interrupted

