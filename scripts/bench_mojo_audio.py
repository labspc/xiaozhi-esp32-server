#!/usr/bin/env python3
"""
Quick benchmark for MojoAudioFFI vs opuslib_next.
Requires: opuslib_next, (optional) libmojo_audio present.
Usage: python scripts/bench_mojo_audio.py
"""
import math
import time
from array import array
from statistics import mean

from mojo.ffi import MojoAudioFFI

try:
    import opuslib_next
except ImportError as exc:  # pragma: no cover
    raise SystemExit(f"opuslib_next required for benchmark: {exc}")


SAMPLE_RATE = 16_000
CHANNELS = 1
FRAME_MS = 60
FRAME_SIZE = int(SAMPLE_RATE * FRAME_MS / 1000)  # samples per frame
NUM_FRAMES = 100


def gen_pcm_frames(num_frames=NUM_FRAMES):
    pcm_frames = []
    for f_idx in range(num_frames):
        pcm = array(
            "h",
            [
                int(
                    12000
                    * math.sin(2 * math.pi * (440 + f_idx) * t / SAMPLE_RATE)
                )
                for t in range(FRAME_SIZE)
            ],
        )
        pcm_frames.append(pcm.tobytes())
    return pcm_frames


def bench_decode(opus_frames, mojo: MojoAudioFFI):
    decoder = opuslib_next.Decoder(SAMPLE_RATE, CHANNELS)
    # Python baseline
    start = time.perf_counter()
    for frame in opus_frames:
        decoder.decode(frame, FRAME_SIZE)
    python_time = time.perf_counter() - start

    # Mojo path (with fallback)
    start = time.perf_counter()
    for frame in opus_frames:
        mojo.decode_opus(frame, sample_rate=SAMPLE_RATE, channels=CHANNELS)
    mojo_time = time.perf_counter() - start
    return python_time, mojo_time


def bench_encode(pcm_frames, mojo: MojoAudioFFI):
    encoder = opuslib_next.Encoder(SAMPLE_RATE, CHANNELS, opuslib_next.APPLICATION_AUDIO)
    # Python baseline
    start = time.perf_counter()
    py_out = []
    for frame in pcm_frames:
        py_out.append(encoder.encode(frame, FRAME_SIZE))
    python_time = time.perf_counter() - start

    # Mojo path (with fallback)
    start = time.perf_counter()
    mojo_out = []
    for frame in pcm_frames:
        encoded = mojo.encode_opus(frame, sample_rate=SAMPLE_RATE, channels=CHANNELS)
        if encoded:
            mojo_out.append(encoded)
    mojo_time = time.perf_counter() - start
    return python_time, mojo_time, py_out, mojo_out


def main():
    mojo = MojoAudioFFI()
    pcm_frames = gen_pcm_frames()

    py_time, mojo_time, py_opus, mojo_opus = bench_encode(pcm_frames, mojo)
    decode_py_time, decode_mojo_time = bench_decode(py_opus, mojo)

    print(
        {
            "encode_python_s": round(py_time, 4),
            "encode_mojo_s": round(mojo_time, 4),
            "encode_speedup": round(py_time / mojo_time, 2) if mojo_time else None,
            "decode_python_s": round(decode_py_time, 4),
            "decode_mojo_s": round(decode_mojo_time, 4),
            "decode_speedup": round(decode_py_time / decode_mojo_time, 2)
            if decode_mojo_time
            else None,
            "mojo_available": mojo.available,
            "load_error": mojo.load_error,
        }
    )


if __name__ == "__main__":
    main()
