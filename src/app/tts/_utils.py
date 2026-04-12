import io
import struct


def _pcm_to_wav(pcm: bytes, sr: int = 24000, ch: int = 1, bits: int = 16) -> bytes:
    """Wrap raw LINEAR16 PCM into a WAV container."""
    byte_rate = sr * ch * bits // 8
    block_align = ch * bits // 8
    header = struct.pack(
        "<4sI4s4sIHHIIHH4sI",
        b"RIFF", 36 + len(pcm), b"WAVE",
        b"fmt ", 16, 1, ch,
        sr, byte_rate, block_align, bits,
        b"data", len(pcm),
    )
    return header + pcm


def _pad(text: str) -> str:
    """Ensure text has enough length for Gemini TTS."""
    text = text.strip()
    if not text:
        return "Nội dung trống."
    return text if len(text) >= 10 else text + "."


def _merge_wav(wav_list: list) -> bytes:
    """Merge multiple WAV bytes into one WAV file."""
    import numpy as np
    import soundfile as sf

    arrays = []
    sr = None
    for i, wav in enumerate(wav_list):
        try:
            data, sample_rate = sf.read(io.BytesIO(wav), dtype="float32", always_2d=False)
            arrays.append(data.mean(axis=1) if data.ndim == 2 else data)
            sr = sample_rate if sr is None else sr
        except Exception as e:
            print(f"[TTS] Chunk {i} error: {e}")

    if not arrays or sr is None:
        raise RuntimeError("No valid WAV chunks to merge.")

    out = io.BytesIO()
    sf.write(out, np.concatenate(arrays), sr, format="WAV")
    return out.getvalue()
