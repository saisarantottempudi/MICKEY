import sounddevice as sd
import numpy as np
import wave
import tempfile


def record_until_silence(sample_rate=16000, silence_threshold=0.01, silence_duration=1.5) -> str:
    chunks = []
    silent_chunks = 0
    chunk_size = int(sample_rate * 0.1)
    max_silent = int(silence_duration / 0.1)

    print("🎙  Listening...")
    with sd.InputStream(samplerate=sample_rate, channels=1, dtype="float32") as stream:
        while True:
            data, _ = stream.read(chunk_size)
            chunks.append(data.copy())
            volume = np.abs(data).mean()
            if volume < silence_threshold:
                silent_chunks += 1
            else:
                silent_chunks = 0
            if silent_chunks >= max_silent and len(chunks) > max_silent:
                break

    audio = np.concatenate(chunks)
    path = tempfile.mktemp(suffix=".wav")
    with wave.open(path, "wb") as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)
        wf.setframerate(sample_rate)
        wf.writeframes((audio * 32767).astype(np.int16).tobytes())
    print("🔇  Done recording.")
    return path
