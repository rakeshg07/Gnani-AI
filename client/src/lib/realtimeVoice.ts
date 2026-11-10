/**
 * Real-Time Continuous Voice Streaming & WebSocket Client for VoiceIQ Sovereign Store.
 *
 * Implements:
 * - Continuous 16kHz 16-bit mono PCM microphone streaming.
 * - Live volume / waveform calculation.
 * - WebSocket event communication with FastAPI voice session.
 * - Immediate Barge-In / Interruption cancellation for audio playback.
 */

export type RealtimeVoiceState =
  | 'IDLE'
  | 'CONNECTING'
  | 'LISTENING'
  | 'TRANSCRIBING'
  | 'THINKING'
  | 'SPEAKING'
  | 'INTERRUPTED'
  | 'ERROR'
  | 'ENDED';

const WELCOME_MESSAGES: Record<string, string> = {
  'en-IN': 'Welcome to VoiceIQ India! , How can i assist you?',
  'hi-IN': 'वॉइसआईक्यू इंडिया में आपका स्वागत है! मैं आपकी क्या सहायता कर सकता हूँ?',
  'ta-IN': 'VoiceIQ இந்தியாவிற்கு வருக! நான் உங்களுக்கு எவ்வாறு உதவ முடியும்?',
  'te-IN': 'VoiceIQ ఇండియాకు స్వాగతం! నేను మీకు ఎలా సహాయపడగలను?',
  'kn-IN': 'VoiceIQ ಇಂಡಿಯಾಗೆ ಸ್ವಾಗತ! ನಾನು ನಿಮಗೆ ಹೇಗೆ ಸಹಾಯ ಮಾಡಲಿ?',
  'ml-IN': 'VoiceIQ ഇന്ത്യയിലേക്ക് സ്വാഗതം! ഞാൻ നിങ്ങളെ എങ്ങനെ സഹായിക്കണം?',
  'mr-IN': 'VoiceIQ इंडियामध्ये आपले स्वागत आहे! मी आपली काय मदत करू शकतो?',
  'bn-IN': 'VoiceIQ ইন্ডিয়াতে স্বাগতম! আমি কীভাবে আপনাকে সাহায্য করতে পারি?',
  'gu-IN': 'VoiceIQ ઇન્ડિયામાં તમારું સ્વાગત છે! હું તમને કેવી રીતે મદદ કરી શકું?',
  'pa-IN': 'VoiceIQ ਇੰਡੀਆ ਵਿੱਚ ਤੁਹਾਡਾ ਸੁਆਗਤ ਹੈ! ਮੈਂ ਤੁਹਾਡੀ ਕਿਵੇਂ ਮਦਦ ਕਰ ਸਕਦਾ ਹਾਂ?',
  'or-IN': 'VoiceIQ ଇଣ୍ଡିଆକୁ ସ୍ୱାଗତ! ମୁଁ ଆପଣଙ୍କୁ କିପରି ସାହାଯ୍ୟ କରିପାରିବି?',
};

export interface VoiceEventCallbacks {
  onStateChange: (state: RealtimeVoiceState) => void;
  onPartialTranscript: (text: string, energy?: number) => void;
  onFinalTranscript: (text: string) => void;
  onAiThinking: () => void;
  onAiTextDelta: (delta: string) => void;
  onAiTextFinal: (text: string, products?: any[]) => void;
  onInterrupted: () => void;
  onError: (error: string) => void;
  onVolumeChange: (volume: number) => void;
}

/**
 * High-performance, low-latency audio queue for playing streaming Timbre TTS chunks.
 * Supports instant interruption / barge-in cancellation.
 */
export class StreamAudioPlayer {
  private queue: string[] = [];
  private currentAudio: HTMLAudioElement | null = null;
  private isPlaying = false;
  private onPlaybackStateChange?: (isPlaying: boolean) => void;
  private hasPlayed = false;

  constructor(onPlaybackStateChange?: (isPlaying: boolean) => void) {
    this.onPlaybackStateChange = onPlaybackStateChange;
  }

  hasEverPlayed(): boolean {
    return this.hasPlayed;
  }

  enqueue(base64Wav: string, turnId: string) {
    this.hasPlayed = true;
    this.queue.push(base64Wav);
    if (!this.isPlaying) {
      this.playNext();
    }
  }

  interrupt() {
    // Immediately stop current audio
    if (this.currentAudio) {
      try {
        this.currentAudio.pause();
        this.currentAudio.currentTime = 0;
        this.currentAudio.src = '';
      } catch {
        // Ignore pause errors
      }
      this.currentAudio = null;
    }
    // Discard any queued sentences from the interrupted turn
    this.queue = [];
    this.isPlaying = false;
    this.onPlaybackStateChange?.(false);
  }

  private playNext() {
    if (this.queue.length === 0) {
      this.isPlaying = false;
      this.onPlaybackStateChange?.(false);
      return;
    }

    const nextBase64 = this.queue.shift();
    if (!nextBase64) return;

    this.isPlaying = true;
    this.onPlaybackStateChange?.(true);

    try {
      const audioUrl = `data:audio/wav;base64,${nextBase64}`;
      const audio = new Audio(audioUrl);
      this.currentAudio = audio;

      audio.onended = () => {
        this.currentAudio = null;
        this.playNext();
      };

      audio.onerror = (e) => {
        console.warn('Audio playback error:', e);
        this.currentAudio = null;
        this.playNext();
      };

      audio.play().catch((err) => {
        console.warn('Audio play rejected (e.g. autoplay restriction):', err);
        this.currentAudio = null;
        this.playNext();
      });
    } catch (err) {
      console.warn('Failed to initialize audio element:', err);
      this.playNext();
    }
  }
}

/**
 * Continuous 16kHz PCM Microphone Audio Streamer.
 */
export class ContinuousMicrophoneStreamer {
  private audioContext: AudioContext | null = null;
  private mediaStream: MediaStream | null = null;
  private sourceNode: MediaStreamAudioSourceNode | null = null;
  private processorNode: ScriptProcessorNode | null = null;
  private onChunkCallback: (pcmBytes: ArrayBuffer) => void;
  private onVolumeCallback?: (volume: number) => void;
  private isStreaming = false;

  constructor(
    onChunk: (pcmBytes: ArrayBuffer) => void,
    onVolume?: (volume: number) => void
  ) {
    this.onChunkCallback = onChunk;
    this.onVolumeCallback = onVolume;
  }

  async start(): Promise<void> {
    if (this.isStreaming) return;

    // Request microphone stream with voice-optimized constraints
    this.mediaStream = await navigator.mediaDevices.getUserMedia({
      audio: {
        channelCount: 1,
        echoCancellation: true,
        noiseSuppression: true,
        autoGainControl: true,
      },
    });

    const AudioContextClass = window.AudioContext || (window as any).webkitAudioContext;
    this.audioContext = new AudioContextClass();
    if (this.audioContext.state === 'suspended') {
      await this.audioContext.resume();
    }

    this.sourceNode = this.audioContext.createMediaStreamSource(this.mediaStream);

    // Buffer size 2048 at 44.1kHz / 48kHz gives ~45ms per chunk
    this.processorNode = this.audioContext.createScriptProcessor(2048, 1, 1);

    this.processorNode.onaudioprocess = (e) => {
      if (!this.isStreaming) return;

      const inputBuffer = e.inputBuffer.getChannelData(0);

      // 1. Calculate live volume (RMS) for UI waveforms
      let sum = 0;
      for (let i = 0; i < inputBuffer.length; i++) {
        sum += inputBuffer[i] * inputBuffer[i];
      }
      const rms = Math.sqrt(sum / inputBuffer.length);
      this.onVolumeCallback?.(Math.min(1.0, rms * 6.0));

      // 2. Downsample and convert to 16kHz 16-bit linear PCM
      const inputSampleRate = this.audioContext?.sampleRate || 48000;
      const targetSampleRate = 16000;
      const ratio = inputSampleRate / targetSampleRate;
      const newLength = Math.round(inputBuffer.length / ratio);

      const pcm16 = new Int16Array(newLength);
      for (let i = 0; i < newLength; i++) {
        const index = Math.min(inputBuffer.length - 1, Math.round(i * ratio));
        const s = Math.max(-1, Math.min(1, inputBuffer[index] || 0));
        pcm16[i] = s < 0 ? s * 0x8000 : s * 0x7fff;
      }

      this.onChunkCallback(pcm16.buffer);
    };

    // Route processor to a zero-gain node before destination to prevent acoustic speaker feedback
    const zeroGain = this.audioContext.createGain();
    zeroGain.gain.value = 0;
    this.sourceNode.connect(this.processorNode);
    this.processorNode.connect(zeroGain);
    zeroGain.connect(this.audioContext.destination);
    this.isStreaming = true;
  }

  stop(): void {
    this.isStreaming = false;

    if (this.mediaStream) {
      this.mediaStream.getTracks().forEach((t) => t.stop());
      this.mediaStream = null;
    }

    if (this.processorNode && this.sourceNode) {
      try {
        this.processorNode.disconnect();
        this.sourceNode.disconnect();
      } catch {
        // ignore
      }
      this.processorNode = null;
      this.sourceNode = null;
    }

    if (this.audioContext && this.audioContext.state !== 'closed') {
      this.audioContext.close().catch(() => {});
      this.audioContext = null;
    }
  }
}

/**
 * Complete Real-Time Voice Conversation Client managing WebSocket,
 * continuous microphone streaming, audio playback, and interruption.
 */
export class RealtimeVoiceConversation {
  private socket: WebSocket | null = null;
  private micStreamer: ContinuousMicrophoneStreamer | null = null;
  private audioPlayer: StreamAudioPlayer;
  private callbacks: VoiceEventCallbacks;
  private sessionId: string;
  private conversationId: string;
  private languageCode: string;
  private currentPage: string;
  private pingInterval: any = null;

  constructor(
    languageCode = 'en-IN',
    currentPage = 'home',
    conversationId = '',
    callbacks: VoiceEventCallbacks
  ) {
    this.languageCode = languageCode;
    this.currentPage = currentPage;
    this.conversationId = conversationId || `conv_${Date.now()}`;
    this.sessionId = `sess_${Date.now()}`;
    this.callbacks = callbacks;

    this.audioPlayer = new StreamAudioPlayer((isPlaying) => {
      if (isPlaying) {
        this.callbacks.onStateChange('SPEAKING');
      } else {
        this.callbacks.onStateChange('LISTENING');
        if (this.socket && this.socket.readyState === WebSocket.OPEN) {
          try {
            this.socket.send(JSON.stringify({ type: 'playback.ended', payload: {} }));
          } catch {
            // ignore
          }
        }
      }
    });
  }

  async start(): Promise<void> {
    this.callbacks.onStateChange('CONNECTING');

    // Build WebSocket URL: connect directly to backend port 8000 when running locally
    const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
    const isLocal =
      window.location.hostname === 'localhost' ||
      window.location.hostname === '127.0.0.1' ||
      window.location.hostname === '0.0.0.0';
    const wsUrl = isLocal
      ? `ws://127.0.0.1:8000/api/v1/voice/session`
      : `${protocol}//${window.location.host}/api/v1/voice/session`;

    return new Promise((resolve, reject) => {
      try {
        this.socket = new WebSocket(wsUrl);
      } catch (err) {
        this.callbacks.onError(`Failed to establish WebSocket: ${err}`);
        this.callbacks.onStateChange('ERROR');
        reject(err);
        return;
      }

      this.socket.binaryType = 'arraybuffer';

      this.socket.onopen = async () => {
        // 1. Send session.start
        this.socket?.send(
          JSON.stringify({
            type: 'session.start',
            payload: {
              session_id: this.sessionId,
              conversation_id: this.conversationId,
              language_code: this.languageCode,
              current_page: this.currentPage,
            },
          })
        );

        // 2. Start continuous microphone capture
        try {
          this.micStreamer = new ContinuousMicrophoneStreamer(
            (pcmBytes) => {
              if (this.socket && this.socket.readyState === WebSocket.OPEN) {
                this.socket.send(pcmBytes);
              }
            },
            (volume) => {
              this.callbacks.onVolumeChange(volume);
            }
          );

          await this.micStreamer.start();
          this.callbacks.onStateChange('LISTENING');
          resolve();
        } catch (micErr) {
          this.callbacks.onError(`Microphone permission denied or device error: ${micErr}`);
          this.callbacks.onStateChange('ERROR');
          this.stop();
          reject(micErr);
        }

        // Heartbeat ping
        this.pingInterval = setInterval(() => {
          if (this.socket && this.socket.readyState === WebSocket.OPEN) {
            this.socket.send(JSON.stringify({ type: 'session.ping', payload: {} }));
          }
        }, 15000);
      };

      this.socket.onmessage = (event) => {
        if (typeof event.data === 'string') {
          try {
            const data = JSON.parse(event.data);
            this.handleServerEvent(data);
          } catch (e) {
            console.warn('Failed to parse voice server message:', e);
          }
        }
      };

      this.socket.onerror = (e) => {
        console.error('Voice WebSocket error:', e);
        this.callbacks.onError('Voice connection error occurred.');
        this.callbacks.onStateChange('ERROR');
      };

      this.socket.onclose = () => {
        this.callbacks.onStateChange('ENDED');
        this.stop();
      };
    });
  }

  interrupt(): void {
    // 1. Instant client-side audio kill
    this.audioPlayer.interrupt();

    // 2. Notify backend of user barge-in
    if (this.socket && this.socket.readyState === WebSocket.OPEN) {
      this.socket.send(JSON.stringify({ type: 'user.interrupt', payload: {} }));
    }

    this.callbacks.onInterrupted();
    this.callbacks.onStateChange('LISTENING');
  }

  setLanguage(lang: string): void {
    this.languageCode = lang;
    if (this.socket && this.socket.readyState === WebSocket.OPEN) {
      this.socket.send(
        JSON.stringify({
          type: 'session.update_language',
          payload: { language_code: lang },
        })
      );
    }
  }

  stop(): void {
    if (this.pingInterval) {
      clearInterval(this.pingInterval);
      this.pingInterval = null;
    }

    this.audioPlayer.interrupt();

    if (this.micStreamer) {
      this.micStreamer.stop();
      this.micStreamer = null;
    }

    if (this.socket) {
      try {
        if (this.socket.readyState === WebSocket.OPEN) {
          this.socket.send(JSON.stringify({ type: 'session.end', payload: {} }));
        }
        this.socket.close();
      } catch {
        // ignore
      }
      this.socket = null;
    }

    this.callbacks.onStateChange('ENDED');
  }

  private handleServerEvent(event: any) {
    const { type, payload } = event;

    switch (type) {
      case 'session.ready':
        this.callbacks.onStateChange('LISTENING');
        // Immediate spoken greeting fallback: if Timbre TTS audio hasn't started playing within 2.8s, speak via SpeechSynthesis
        setTimeout(() => {
          if (!this.audioPlayer.hasEverPlayed() && typeof window !== 'undefined' && 'speechSynthesis' in window) {
            try {
              const greeting = WELCOME_MESSAGES[this.languageCode] || 'Welcome to VoiceIQ India! , How can i assist you?';
              const utter = new SpeechSynthesisUtterance(greeting);
              utter.lang = this.languageCode;
              utter.onstart = () => this.callbacks.onStateChange('SPEAKING');
              utter.onend = () => this.callbacks.onStateChange('LISTENING');
              window.speechSynthesis.speak(utter);
            } catch (err) {
              console.warn('SpeechSynthesis fallback error:', err);
            }
          }
        }, 2800);
        break;

      case 'session.state':
        if (payload?.state) {
          this.callbacks.onStateChange(payload.state as RealtimeVoiceState);
        }
        break;

      case 'transcript.partial':
        this.callbacks.onPartialTranscript(payload?.status || '', payload?.energy);
        break;

      case 'transcript.final':
        if (payload?.transcript) {
          this.callbacks.onFinalTranscript(payload.transcript);
        }
        break;

      case 'ai.thinking':
        this.callbacks.onAiThinking();
        this.callbacks.onStateChange('THINKING');
        break;

      case 'ai.text.delta':
        if (payload?.delta) {
          this.callbacks.onAiTextDelta(payload.delta);
        }
        break;

      case 'ai.text.final':
        if (payload?.text) {
          this.callbacks.onAiTextFinal(payload.text, payload.products);
        }
        break;

      case 'audio.chunk':
        if (payload?.audio_base64) {
          this.audioPlayer.enqueue(payload.audio_base64, payload.turn_id || '');
        }
        break;

      case 'assistant.interrupted':
        // Server confirmed barge-in
        this.audioPlayer.interrupt();
        this.callbacks.onInterrupted();
        this.callbacks.onStateChange('LISTENING');
        break;

      case 'session.error':
        if (payload?.error) {
          this.callbacks.onError(payload.error);
        }
        break;

      case 'session.pong':
        // Heartbeat received
        break;
    }
  }
}

