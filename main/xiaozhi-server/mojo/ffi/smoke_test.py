"""
Minimal smoke test for MojoAudioFFI.
Run: `python -m mojo.ffi.smoke_test`
Requires: `opuslib_next` for generating a sample opus packet.
"""
import math
from array import array

from mojo.ffi import MojoAudioFFI

try:
    import opuslib_next
except ImportError as exc:  # pragma: no cover - optional
    raise SystemExit(f"opuslib_next is required for this smoke test: {exc}")


def _make_opus_packet(frame_size: int = 320, sample_rate: int = 16_000) -> bytes:
    encoder = opuslib_next.Encoder(sample_rate, 1, opuslib_next.APPLICATION_AUDIO)
    # Simple sine wave
    pcm = array(
        "h",
        [
            int(16000 * math.sin(2 * math.pi * 440 * t / sample_rate))
            for t in range(frame_size)
        ],
    )
    return encoder.encode(pcm.tobytes(), frame_size)


def main() -> None:
    packet = _make_opus_packet()
    ffi = MojoAudioFFI()
    pcm = ffi.decode_opus(packet)
    assert pcm, "decode_opus returned empty"
    floats = ffi.pcm_to_float(pcm)
    assert floats, "pcm_to_float returned empty"
    energy = ffi.vad_energy(floats)
    assert energy is not None
    print("MojoAudioFFI smoke test ok", {"pcm_len": len(pcm or b''), "energy": energy})


if __name__ == "__main__":
    main()
