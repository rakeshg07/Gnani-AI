"""Voice Activity Detection (VAD) module for VoiceIQ real-time voice sessions.

Analyzes raw 16-bit linear PCM audio chunks (16kHz mono) to distinguish:
- Speech Start (customer begins speaking -> triggers Barge-In / Interruption if AI is speaking)
- Speech Ongoing (customer speaking or taking brief natural pauses)
- Speech End (customer finished turn after sustained silence -> triggers STT transcription & LLM turn)
- Pure Silence / Background Noise
"""
import math
import struct
from enum import Enum
from typing import Optional, Tuple


class VADState(str, Enum):
    SILENCE = "silence"
    SPEECH_START = "speech_start"
    SPEECH_ACTIVE = "speech_active"
    SPEECH_END = "speech_end"


class VoiceActivityDetector:
    """
    Lightweight, low-latency audio energy and zero-crossing VAD.
    Optimized for Windows/Linux without requiring heavy external binary dependencies or GPU.
    """

    def __init__(
        self,
        sample_rate: int = 16000,
        sample_width: int = 2,  # 16-bit PCM (2 bytes per sample)
        energy_threshold: float = 0.003,  # Sensitive normalized RMS threshold for laptop/headset mics
        silence_timeout_ms: int = 900,  # 900ms silence to finalize speech turn
        min_speech_ms: int = 100,  # 100ms to qualify as speech start (captures leading consonants)
        noise_floor_alpha: float = 0.03,  # Moving average smoothing for noise floor
    ):
        self.sample_rate = sample_rate
        self.sample_width = sample_width
        self.energy_threshold = energy_threshold
        self.silence_timeout_ms = silence_timeout_ms
        self.min_speech_ms = min_speech_ms
        self.noise_floor_alpha = noise_floor_alpha

        self.is_speaking = False
        self.speech_duration_ms = 0.0
        self.silence_duration_ms = 0.0
        self.noise_floor = energy_threshold * 0.35

    def reset(self):
        """Reset internal state machine for a new turn."""
        self.is_speaking = False
        self.speech_duration_ms = 0.0
        self.silence_duration_ms = 0.0

    def calculate_rms(self, pcm_bytes: bytes) -> float:
        """Calculate Root Mean Square (RMS) energy normalized between 0.0 and 1.0."""
        num_samples = len(pcm_bytes) // self.sample_width
        if num_samples == 0:
            return 0.0

        fmt = f"<{num_samples}h"
        try:
            samples = struct.unpack(fmt, pcm_bytes[: num_samples * 2])
        except struct.error:
            return 0.0

        sum_squares = sum(s * s for s in samples)
        mean_square = sum_squares / num_samples
        rms = math.sqrt(mean_square)
        return rms / 32768.0

    def process_chunk(self, pcm_bytes: bytes) -> Tuple[VADState, float]:
        """
        Processes an incoming PCM audio chunk and returns the VAD state and RMS energy.
        """
        chunk_duration_ms = (len(pcm_bytes) / (self.sample_rate * self.sample_width)) * 1000.0
        rms = self.calculate_rms(pcm_bytes)

        # Dynamic threshold based on current noise floor, capped to prevent speech suppression
        dynamic_threshold = min(0.006, max(self.energy_threshold, self.noise_floor * 1.3))

        if rms > dynamic_threshold:
            # Active voice detected in this chunk
            self.silence_duration_ms = 0.0
            self.speech_duration_ms += chunk_duration_ms

            if not self.is_speaking and self.speech_duration_ms >= self.min_speech_ms:
                self.is_speaking = True
                return VADState.SPEECH_START, rms
            elif self.is_speaking:
                return VADState.SPEECH_ACTIVE, rms
            else:
                return VADState.SILENCE, rms
        else:
            # Ambient noise / silence update
            self.noise_floor = (
                (1.0 - self.noise_floor_alpha) * self.noise_floor
                + self.noise_floor_alpha * rms
            )

            if self.is_speaking:
                self.silence_duration_ms += chunk_duration_ms

                # Check if customer has finished speaking
                if self.silence_duration_ms >= self.silence_timeout_ms:
                    self.is_speaking = False
                    self.speech_duration_ms = 0.0
                    self.silence_duration_ms = 0.0
                    return VADState.SPEECH_END, rms
                else:
                    return VADState.SPEECH_ACTIVE, rms
            else:
                self.speech_duration_ms = 0.0
                return VADState.SILENCE, rms

