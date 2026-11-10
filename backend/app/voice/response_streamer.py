"""Sentence-Boundary Streamer for VoiceIQ Progressive Text-to-Speech Pipelining.

Splits incoming LLM token streams into speakable sentence chunks as early as possible.
Enables Gnani Timbre to begin synthesizing and streaming spoken audio while the rest of
the LLM response is still being generated.
"""
import re
from typing import AsyncGenerator, List, Optional


# Sentence boundary terminators for English and Indian languages (including Devanagari purna viram '।')
SENTENCE_TERMINATORS = re.compile(r"([.?!।\n]+)")
MIN_SENTENCE_WORDS = 3


class SentenceStreamer:
    """Buffers streamed tokens and yields complete, speakable sentences."""

    def __init__(self, min_words: int = MIN_SENTENCE_WORDS):
        self.min_words = min_words
        self.buffer = ""

    def feed(self, delta: str) -> List[str]:
        """
        Accepts a newly streamed token/delta and returns any complete sentences ready for TTS.
        """
        self.buffer += delta
        ready_sentences: List[str] = []

        # Check for sentence terminators
        parts = SENTENCE_TERMINATORS.split(self.buffer)
        if len(parts) >= 3:
            # We have at least one complete sentence + terminator + remainder
            # parts will look like: [sentence1, terminator1, sentence2, terminator2, ..., remainder]
            i = 0
            while i < len(parts) - 1:
                sentence_text = (parts[i] + parts[i + 1]).strip()
                words = sentence_text.split()
                if len(words) >= self.min_words:
                    ready_sentences.append(sentence_text)
                    i += 2
                else:
                    # Too short (e.g. "Dr." or "Rs."), keep in buffer with following parts
                    break

            # The remainder of unfinalized text stays in buffer
            self.buffer = "".join(parts[i:]).strip()

        return ready_sentences

    def flush(self) -> Optional[str]:
        """Flushes any remaining text in the buffer as a final sentence chunk."""
        remaining = self.buffer.strip()
        self.buffer = ""
        return remaining if remaining else None

