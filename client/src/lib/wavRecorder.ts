/**
 * In-browser PCM 16-bit mono WAV recorder using standard Web Audio API.
 * Ensures the recorded audio is native RIFF/WAVE format compatible with Gnani Prisma STT,
 * eliminating browser-specific container issues (such as WebM/Opus).
 */
export class WavRecorder {
  private audioContext: AudioContext | null = null;
  private mediaStream: MediaStream | null = null;
  private processorNode: ScriptProcessorNode | null = null;
  private sourceNode: MediaStreamAudioSourceNode | null = null;
  private pcmBuffers: Float32Array[] = [];
  private recordingLength = 0;
  private targetSampleRate = 16000;
  private inputSampleRate = 16000;

  async start(): Promise<void> {
    this.pcmBuffers = [];
    this.recordingLength = 0;

    // Request microphone access with voice optimizations
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
    this.inputSampleRate = this.audioContext.sampleRate;

    this.sourceNode = this.audioContext.createMediaStreamSource(this.mediaStream);
    // Buffer size 4096 gives smooth real-time capture
    this.processorNode = this.audioContext.createScriptProcessor(4096, 1, 1);

    this.processorNode.onaudioprocess = (e) => {
      const channelData = e.inputBuffer.getChannelData(0);
      this.pcmBuffers.push(new Float32Array(channelData));
      this.recordingLength += channelData.length;
    };

    const zeroGain = this.audioContext.createGain();
    zeroGain.gain.value = 0;
    this.sourceNode.connect(this.processorNode);
    this.processorNode.connect(zeroGain);
    zeroGain.connect(this.audioContext.destination);
  }

  async stop(): Promise<Blob> {
    this.cleanupNodes();
    return this.encodeWav();
  }

  cancel(): void {
    this.cleanupNodes();
    this.pcmBuffers = [];
    this.recordingLength = 0;
  }

  private cleanupNodes(): void {
    if (this.mediaStream) {
      this.mediaStream.getTracks().forEach((track) => track.stop());
      this.mediaStream = null;
    }

    if (this.processorNode && this.sourceNode) {
      try {
        this.processorNode.disconnect();
        this.sourceNode.disconnect();
      } catch {
        // Ignore disconnect errors
      }
      this.processorNode = null;
      this.sourceNode = null;
    }

    if (this.audioContext && this.audioContext.state !== 'closed') {
      this.audioContext.close().catch(() => {});
      this.audioContext = null;
    }
  }

  private encodeWav(): Blob {
    if (this.recordingLength === 0) {
      return new Blob([], { type: 'audio/wav' });
    }

    // Merge buffer chunks
    const merged = new Float32Array(this.recordingLength);
    let offset = 0;
    for (const buf of this.pcmBuffers) {
      merged.set(buf, offset);
      offset += buf.length;
    }

    // Downsample to 16,000 Hz if needed (optimal for speech recognition)
    let samples: Float32Array;
    let finalSampleRate = this.targetSampleRate;

    if (this.inputSampleRate !== this.targetSampleRate && this.inputSampleRate > 0) {
      const compression = this.inputSampleRate / this.targetSampleRate;
      const length = Math.floor(merged.length / compression);
      samples = new Float32Array(length);
      for (let i = 0; i < length; i++) {
        samples[i] = merged[Math.floor(i * compression)];
      }
    } else {
      samples = merged;
      finalSampleRate = this.inputSampleRate;
    }

    // Convert Float32 [-1.0, 1.0] to 16-bit signed PCM
    const pcm16 = new Int16Array(samples.length);
    for (let i = 0; i < samples.length; i++) {
      const s = Math.max(-1, Math.min(1, samples[i]));
      pcm16[i] = s < 0 ? s * 0x8000 : s * 0x7fff;
    }

    // Build RIFF/WAVE header (44 bytes)
    const buffer = new ArrayBuffer(44 + pcm16.length * 2);
    const view = new DataView(buffer);

    // RIFF chunk descriptor
    this.writeString(view, 0, 'RIFF');
    view.setUint32(4, 36 + pcm16.length * 2, true);
    this.writeString(view, 8, 'WAVE');

    // "fmt " sub-chunk
    this.writeString(view, 12, 'fmt ');
    view.setUint32(16, 16, true); // Subchunk1Size (16 for PCM)
    view.setUint16(20, 1, true); // AudioFormat (1 = PCM)
    view.setUint16(22, 1, true); // NumChannels (1 = Mono)
    view.setUint32(24, finalSampleRate, true); // SampleRate
    view.setUint32(28, finalSampleRate * 2, true); // ByteRate (SampleRate * 1 * 2)
    view.setUint16(32, 2, true); // BlockAlign (1 * 2)
    view.setUint16(34, 16, true); // BitsPerSample (16-bit)

    // "data" sub-chunk
    this.writeString(view, 36, 'data');
    view.setUint32(40, pcm16.length * 2, true);

    // Write PCM samples
    const pcmBytes = new Uint8Array(pcm16.buffer);
    new Uint8Array(buffer, 44).set(pcmBytes);

    return new Blob([buffer], { type: 'audio/wav' });
  }

  private writeString(view: DataView, offset: number, string: string): void {
    for (let i = 0; i < string.length; i++) {
      view.setUint8(offset + i, string.charCodeAt(i));
    }
  }
}
