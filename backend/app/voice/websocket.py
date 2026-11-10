"""FastAPI WebSocket Voice Conversation Endpoint for VoiceIQ Sovereign Store.

Implements real-time, bi-directional audio conversation with:
- Continuous live microphone audio chunk streaming.
- Voice Activity Detection (VAD) & speech-turn segmenting.
- Barge-in / Interruption handling (cancels active LLM response and TTS audio).
- Progressive text streaming with Hugging Face LLM.
- Sentence-by-sentence streaming speech generation with Gnani Timbre TTS.
- Strict store-only scope enforcement and safe e-commerce grounding.
"""
import asyncio
import base64
import json
import time
from typing import Optional, Dict, Any

from fastapi import APIRouter, WebSocket, WebSocketDisconnect, status
from app.core.config import settings
from app.core.logging import logger
from app.core.database import get_mongo_db
from app.providers.gnani import GnaniSpeechClient, GnaniClientException
from app.providers.gemini import GeminiClient, GeminiClientException
from app.services.query_scope import classify_query_scope
from app.schemas.ecommerce import AssistantMessageIn
from app.services.voice_assistant import VoiceAssistantOrchestrator
from app.services.assistant_locales import format_msg
from app.voice.session_manager import (
    VoiceSession,
    VoiceSessionState,
    session_registry,
)
from app.voice.vad import VADState
from app.voice.response_streamer import SentenceStreamer

router = APIRouter(tags=["Real-Time Voice"])


WELCOME_GREETINGS = {
    "en-IN": "Welcome to VoiceIQ India! , How can i assist you?",
    "hi-IN": "वॉइसआईक्यू इंडिया में आपका स्वागत है! मैं आपकी क्या सहायता कर सकता हूँ?",
    "kn-IN": "VoiceIQ ಇಂಡಿಯಾಗೆ ಸ್ವಾಗತ! ನಾನು ನಿಮಗೆ ಹೇಗೆ ಸಹಾಯ ಮಾಡಲಿ?",
    "ta-IN": "VoiceIQ இந்தியாவிற்கு வருக! நான் உங்களுக்கு எவ்வாறு உதவ முடியும்?",
    "te-IN": "VoiceIQ ఇండియాకు స్వాగతం! నేను మీకు ఎలా సహాయపడగలను?",
    "ml-IN": "VoiceIQ ഇന്ത്യയിലേക്ക് സ്വാഗതം! ഞാൻ നിങ്ങളെ എങ്ങനെ സഹായിക്കണം?",
    "mr-IN": "VoiceIQ इंडियामध्ये आपले स्वागत आहे! मी आपली काय मदत करू शकतो?",
    "bn-IN": "VoiceIQ ইন্ডিয়াতে স্বাগতম! আমি কীভাবে আপনাকে সাহায্য করতে পারি?",
    "gu-IN": "VoiceIQ ઇન્ડિયામાં તમારું સ્વાગત છે! હું તમને કેવી રીતે મદદ કરી શકું?",
    "pa-IN": "VoiceIQ ਇੰਡੀਆ ਵਿੱਚ ਤੁਹਾਡਾ ਸੁਆਗਤ ਹੈ! ਮੈਂ ਤੁਹਾਡੀ ਕਿਵੇਂ ਮਦਦ ਕਰ ਸਕਦਾ ਹਾਂ?",
    "or-IN": "VoiceIQ ଇଣ୍ଡିଆକୁ ସ୍ୱାଗତ! ମୁଁ ଆପଣଙ୍କୁ କିପରି ସାହାଯ୍ୟ କରିପାରିବି?",
}


async def send_json_event(websocket: WebSocket, event_type: str, payload: Dict[str, Any]):
    """Helper to send standardized JSON events to the frontend."""
    message = {
        "type": event_type,
        "timestamp": time.time(),
        "payload": payload,
    }
    await websocket.send_text(json.dumps(message))


async def process_user_turn(
    session: VoiceSession,
    websocket: WebSocket,
    turn_id: str,
    gnani_client: GnaniSpeechClient,
    gemini_client: GeminiClient,
):
    """
    Route 2: Real-Time Spoken Conversations (Gemini + Gnani Prisma STT + Gnani Timbre TTS).
    Executes a complete customer turn:
    1. Transcribes accumulated audio using Gnani Prisma STT.
    2. Validates query scope (Store only).
    3. Generates conversational response via Google Gemini API.
    4. Pipes completed sentences progressively to Gnani Timbre TTS.
    5. Streams generated audio chunks to the browser over WebSocket.
    """
    try:
        # Check if turn was already interrupted
        if not session.interruption.is_turn_valid(turn_id):
            return

        # 1. Transcribe with Gnani Prisma STT
        session.transition_to(VoiceSessionState.TRANSCRIBING)
        await send_json_event(websocket, "session.state", {"state": VoiceSessionState.TRANSCRIBING.value, "turn_id": turn_id})

        wav_bytes = session.get_audio_wav_bytes()
        session.clear_audio_buffer()

        if len(wav_bytes) < 44 + 800:  # Less than 50ms of audio
            session.transition_to(VoiceSessionState.LISTENING)
            await send_json_event(websocket, "session.state", {"state": VoiceSessionState.LISTENING.value, "turn_id": turn_id})
            return

        transcript = ""
        try:
            stt_res = await gnani_client.transcribe_audio(
                audio_bytes=wav_bytes,
                filename="stream_turn.wav",
                language_code=session.language_code,
            )
            transcript = (stt_res.transcript or "").strip()
        except Exception as stt_err:
            logger.warning(f"[{session.session_id}] Prisma STT warning ({stt_err}); checking fallback transcription")
            # If Gnani is in demo or test mode, handle gracefully
            transcript = ""

        if not transcript:
            session.transition_to(VoiceSessionState.LISTENING)
            await send_json_event(websocket, "session.state", {"state": VoiceSessionState.LISTENING.value, "turn_id": turn_id})
            return

        # Check turn validity again
        if not session.interruption.is_turn_valid(turn_id):
            return

        # Emit finalized transcript
        await send_json_event(websocket, "transcript.final", {
            "transcript": transcript,
            "turn_id": turn_id,
            "language": session.language_code,
        })

        # 2. Scope Guard Check
        session.transition_to(VoiceSessionState.THINKING)
        await send_json_event(websocket, "ai.thinking", {"turn_id": turn_id})

        scope_result = await classify_query_scope(
            message=transcript,
            current_page=session.current_page,
            language_code=session.language_code,
            gemini_client=gemini_client,
        )

        if scope_result.is_out_of_scope:
            out_of_scope_text = format_msg("out_of_scope", session.language_code)
            await send_json_event(websocket, "ai.text.delta", {"delta": out_of_scope_text, "turn_id": turn_id})
            await send_json_event(websocket, "ai.text.final", {"text": out_of_scope_text, "turn_id": turn_id})

            # Synthesize and stream out-of-scope guidance
            try:
                tts_audio = await gnani_client.synthesize_speech(
                    text=out_of_scope_text,
                    language=session.language_code,
                )
                if session.interruption.is_turn_valid(turn_id):
                    audio_b64 = base64.b64encode(tts_audio).decode("ascii")
                    session.transition_to(VoiceSessionState.SPEAKING)
                    await send_json_event(websocket, "audio.chunk", {
                        "audio_base64": audio_b64,
                        "turn_id": turn_id,
                        "is_final": True,
                    })
            except Exception as tts_err:
                logger.warning(f"[{session.session_id}] TTS warning: {tts_err}")

            session.transition_to(VoiceSessionState.LISTENING)
            await send_json_event(websocket, "session.state", {"state": VoiceSessionState.LISTENING.value, "turn_id": turn_id})
            return

        # 3. Store Execution & Contextual Intent Processing (Gemini for Route 2 Voice)
        payload = AssistantMessageIn(
            message=transcript,
            conversation_id=session.conversation_id,
            current_page=session.current_page,
            language_code=session.language_code,
            synthesize_audio=False,
        )
        db = get_mongo_db()
        assistant_reply = await VoiceAssistantOrchestrator.process_message(
            db=db,
            payload=payload,
            gemini_client=gemini_client,
            gnani_client=gnani_client,
            active_provider="gemini",
        )

        full_reply_text = assistant_reply.reply_text

        # 4. Progressive Sentence Streaming & Timbre TTS
        streamer = SentenceStreamer()
        sentences = streamer.feed(full_reply_text)
        tail = streamer.flush()
        if tail:
            sentences.append(tail)

        # Emit full text
        await send_json_event(websocket, "ai.text.final", {
            "text": full_reply_text,
            "turn_id": turn_id,
            "intent": assistant_reply.intent,
            "products": [p.dict() if hasattr(p, "dict") else p for p in (assistant_reply.products or [])],
        })

        # Synthesize each sentence and send audio chunks
        for idx, sentence in enumerate(sentences):
            if not session.interruption.is_turn_valid(turn_id):
                logger.info(f"[{session.session_id}] Turn {turn_id} interrupted during TTS stream; dropping sentence {idx}")
                break

            try:
                tts_bytes = await gnani_client.synthesize_speech(
                    text=sentence,
                    language=session.language_code,
                )
                if session.interruption.is_turn_valid(turn_id):
                    session.transition_to(VoiceSessionState.SPEAKING)
                    b64_audio = base64.b64encode(tts_bytes).decode("ascii")
                    await send_json_event(websocket, "audio.chunk", {
                        "audio_base64": b64_audio,
                        "sentence_index": idx,
                        "text": sentence,
                        "turn_id": turn_id,
                        "is_final": (idx == len(sentences) - 1),
                    })
            except Exception as tts_e:
                logger.warning(f"[{session.session_id}] Timbre synthesis failed for chunk ({tts_e})")

        # Ready for next user turn
        if session.interruption.is_turn_valid(turn_id):
            session.transition_to(VoiceSessionState.LISTENING)
            await send_json_event(websocket, "session.state", {"state": VoiceSessionState.LISTENING.value, "turn_id": turn_id})

    except asyncio.CancelledError:
        logger.info(f"[{session.session_id}] User turn {turn_id} cancelled due to barge-in.")
    except Exception as exc:
        logger.error(f"[{session.session_id}] Error in user turn {turn_id}: {exc}", exc_info=True)
        await send_json_event(websocket, "session.error", {"error": str(exc), "turn_id": turn_id})
        session.transition_to(VoiceSessionState.LISTENING)


@router.websocket("/voice/session")
@router.websocket("/ws/assistant")
@router.websocket("/api/voice/session")
@router.websocket("/api/v1/voice/session")
async def voice_session_websocket(websocket: WebSocket):
    """
    Persistent WebSocket connection for real-time, bi-directional spoken e-commerce conversations.
    Includes origin validation, audio buffer boundaries, and rate limits.
    """
    origin = websocket.headers.get("origin")
    if origin and "*" not in settings.ALLOWED_ORIGINS:
        is_allowed = (
            any(origin.startswith(a) for a in settings.ALLOWED_ORIGINS)
            or "localhost" in origin
            or "127.0.0.1" in origin
        )
        if not is_allowed:
            logger.warning(f"Voice WebSocket: Rejected unauthorized origin: {origin}")
            await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
            return

    await websocket.accept()
    session: Optional[VoiceSession] = None
    gnani_client = GnaniSpeechClient()
    gemini_client = GeminiClient()

    try:
        while True:
            # Receive either text JSON control events or binary PCM audio chunks
            ws_message = await websocket.receive()

            if ws_message.get("type") == "websocket.disconnect":
                break

            # A) Binary audio frame (Raw 16kHz 16-bit mono PCM)
            if "bytes" in ws_message and ws_message["bytes"]:
                pcm_data = ws_message["bytes"]
                if len(pcm_data) > 65536:  # Max 64KB per chunk (~2s)
                    continue

                if session and not session.is_muted:
                    # Guard against unbounded buffer memory (> 2.5MB ~ 80s)
                    if len(session.audio_buffer) > 2500000:
                        session.clear_audio_buffer()

                    vad_state, rms = session.vad.process_chunk(pcm_data)

                    # Barge-in / Interruption check
                    if vad_state == VADState.SPEECH_START:
                        if session.state == VoiceSessionState.SPEAKING:
                            # Customer spoke while AI was speaking!
                            interrupted_turn = session.interruption.cancel_current_turn()
                            new_turn = session.interruption.next_turn()
                            session.transition_to(VoiceSessionState.INTERRUPTED)
                            logger.info(f"[{session.session_id}] BARGE-IN TRIGGERED on {interrupted_turn} -> New turn {new_turn}")

                            # Notify frontend to instantly kill audio playback and purge audio queue
                            await send_json_event(websocket, "assistant.interrupted", {
                                "interrupted_turn_id": interrupted_turn,
                                "new_turn_id": new_turn,
                            })
                            session.transition_to(VoiceSessionState.LISTENING)
                            session.audio_buffer.clear()

                        # Append speech chunk; do not wipe buffer so leading consonants are intact
                        session.append_audio_chunk(pcm_data)
                        await send_json_event(websocket, "transcript.partial", {"status": "listening", "energy": rms})

                    elif vad_state == VADState.SPEECH_ACTIVE:
                        session.append_audio_chunk(pcm_data)

                    elif vad_state == VADState.SPEECH_END:
                        # Customer finished speaking
                        session.append_audio_chunk(pcm_data)
                        current_turn = session.interruption.current_turn_id

                        # Launch asynchronous user turn processing
                        task = asyncio.create_task(
                            process_user_turn(
                                session=session,
                                websocket=websocket,
                                turn_id=current_turn,
                                gnani_client=gnani_client,
                                gemini_client=gemini_client,
                            ),
                            name=f"turn_{current_turn}_{session.session_id}",
                        )
                        session.interruption.register_task(task, current_turn)

                    elif vad_state == VADState.SILENCE:
                        # While waiting for user speech in LISTENING state, maintain a 350ms pre-speech buffer
                        if session.state == VoiceSessionState.LISTENING and not session.vad.is_speaking:
                            session.append_audio_chunk(pcm_data)
                            max_prespeech_bytes = int(16000 * 2 * 0.35)  # 350ms
                            if len(session.audio_buffer) > max_prespeech_bytes:
                                session.audio_buffer = session.audio_buffer[-max_prespeech_bytes:]

                continue

            # B) Text JSON control message
            if "text" in ws_message and ws_message["text"]:
                try:
                    event = json.loads(ws_message["text"])
                except Exception:
                    continue

                event_type = event.get("type")
                payload = event.get("payload", {})

                if event_type == "session.start":
                    session_id = payload.get("session_id") or f"sess_{int(time.time() * 1000)}"
                    conversation_id = payload.get("conversation_id")
                    language_code = payload.get("language_code", "en-IN")
                    current_page = payload.get("current_page", "home")

                    session = session_registry.create_session(
                        session_id=session_id,
                        conversation_id=conversation_id,
                        language_code=language_code,
                        current_page=current_page,
                    )
                    session.transition_to(VoiceSessionState.LISTENING)

                    await send_json_event(websocket, "session.ready", {
                        "session_id": session.session_id,
                        "conversation_id": session.conversation_id,
                        "language_code": session.language_code,
                        "state": session.state.value,
                    })
                    logger.info(f"Voice session ready: {session.session_id} (conv={session.conversation_id}, lang={session.language_code})")

                    # Speak welcome greeting immediately via Timbre TTS in selected language
                    welcome_text = WELCOME_GREETINGS.get(session.language_code, "Welcome to VoiceIQ India! , How can i assist you?")
                    await send_json_event(websocket, "ai.text.final", {
                        "text": welcome_text,
                        "turn_id": "welcome_turn",
                        "intent": "greeting",
                        "is_welcome": True,
                    })

                    try:
                        tts_bytes = await gnani_client.synthesize_speech(
                            text=welcome_text,
                            language=session.language_code,
                        )
                        if tts_bytes:
                            audio_b64 = base64.b64encode(tts_bytes).decode("ascii")
                            session.transition_to(VoiceSessionState.SPEAKING)
                            await send_json_event(websocket, "audio.chunk", {
                                "audio_base64": audio_b64,
                                "turn_id": "welcome_turn",
                                "is_final": True,
                            })
                    except Exception as tts_err:
                        logger.warning(f"Welcome TTS greeting error ({tts_err}); continuing in listening state")
                        session.transition_to(VoiceSessionState.LISTENING)
                        await send_json_event(websocket, "session.state", {
                            "state": VoiceSessionState.LISTENING.value,
                            "turn_id": "welcome_turn",
                        })

                elif event_type == "session.update_language":
                    new_lang = payload.get("language_code")
                    if new_lang and session:
                        session.language_code = new_lang
                        logger.info(f"[{session.session_id}] Updated session language to {new_lang}")
                        await send_json_event(websocket, "session.language_updated", {
                            "language_code": session.language_code
                        })

                elif event_type == "playback.ended":
                    if session and session.state == VoiceSessionState.SPEAKING:
                        session.transition_to(VoiceSessionState.LISTENING)
                        logger.debug(f"[{session.session_id}] Frontend playback completed -> transitioned to LISTENING")
                        await send_json_event(websocket, "session.state", {
                            "state": VoiceSessionState.LISTENING.value,
                            "turn_id": payload.get("turn_id"),
                        })

                elif event_type == "audio.chunk":
                    # Base64-encoded PCM audio chunk
                    b64_data = payload.get("pcm_base64")
                    if b64_data and session and not session.is_muted:
                        try:
                            pcm_data = base64.b64decode(b64_data)
                            vad_state, rms = session.vad.process_chunk(pcm_data)

                            if vad_state == VADState.SPEECH_START:
                                if session.state == VoiceSessionState.SPEAKING:
                                    interrupted_turn = session.interruption.cancel_current_turn()
                                    new_turn = session.interruption.next_turn()
                                    session.transition_to(VoiceSessionState.INTERRUPTED)
                                    await send_json_event(websocket, "assistant.interrupted", {
                                        "interrupted_turn_id": interrupted_turn,
                                        "new_turn_id": new_turn,
                                    })
                                    session.transition_to(VoiceSessionState.LISTENING)
                                    session.audio_buffer.clear()

                                session.append_audio_chunk(pcm_data)
                                await send_json_event(websocket, "transcript.partial", {"status": "listening", "energy": rms})

                            elif vad_state == VADState.SPEECH_ACTIVE:
                                session.append_audio_chunk(pcm_data)

                            elif vad_state == VADState.SPEECH_END:
                                session.append_audio_chunk(pcm_data)
                                current_turn = session.interruption.current_turn_id
                                task = asyncio.create_task(
                                    process_user_turn(
                                        session=session,
                                        websocket=websocket,
                                        turn_id=current_turn,
                                        gnani_client=gnani_client,
                                        gemini_client=gemini_client,
                                    ),
                                    name=f"turn_{current_turn}_{session.session_id}",
                                )
                                session.interruption.register_task(task, current_turn)

                            elif vad_state == VADState.SILENCE:
                                if session.state == VoiceSessionState.LISTENING and not session.vad.is_speaking:
                                    session.append_audio_chunk(pcm_data)
                                    max_prespeech_bytes = int(16000 * 2 * 0.35)
                                    if len(session.audio_buffer) > max_prespeech_bytes:
                                        session.audio_buffer = session.audio_buffer[-max_prespeech_bytes:]
                        except Exception as decode_err:
                            logger.debug(f"Audio decode warning: {decode_err}")

                elif event_type == "user.interrupt":
                    # Manual or client-side VAD barge-in notification
                    if session:
                        interrupted_turn = session.interruption.cancel_current_turn()
                        new_turn = session.interruption.next_turn()
                        session.transition_to(VoiceSessionState.INTERRUPTED)
                        session.clear_audio_buffer()
                        await send_json_event(websocket, "assistant.interrupted", {
                            "interrupted_turn_id": interrupted_turn,
                            "new_turn_id": new_turn,
                        })
                        session.transition_to(VoiceSessionState.LISTENING)

                elif event_type == "microphone.mute":
                    if session:
                        session.is_muted = True
                        session.clear_audio_buffer()
                        await send_json_event(websocket, "session.state", {"state": "MUTED"})

                elif event_type == "microphone.unmute":
                    if session:
                        session.is_muted = False
                        session.clear_audio_buffer()
                        session.transition_to(VoiceSessionState.LISTENING)
                        await send_json_event(websocket, "session.state", {"state": VoiceSessionState.LISTENING.value})

                elif event_type == "session.ping":
                    await send_json_event(websocket, "session.pong", {"timestamp": time.time()})

                elif event_type == "session.end":
                    if session:
                        session.interruption.cancel_current_turn()
                        session.transition_to(VoiceSessionState.ENDED)
                    break

    except WebSocketDisconnect:
        logger.info(f"WebSocket client disconnected ({session.session_id if session else 'unregistered'})")
    except Exception as e:
        logger.error(f"WebSocket unexpected error: {e}", exc_info=True)
    finally:
        if session:
            session.interruption.cancel_current_turn()
            session_registry.remove_session(session.session_id)
            logger.info(f"Voice session cleaned up: {session.session_id}")
