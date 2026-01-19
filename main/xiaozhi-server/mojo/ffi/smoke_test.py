"""
Minimal smoke test for MojoAudioFFI.
Run: `python -m mojo.ffi.smoke_test`
Requires: `opuslib_next` for generating a sample opus packet.
"""
import math
from array import array

from mojo.ffi import MojoAudioFFI
from mojo.ffi.mojo_audio import split_frames

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
    encoded = ffi.encode_opus(pcm)
    assert encoded, "encode_opus returned empty"
    # batch decode exercise
    joined = b"".join([packet, packet])
    frame_lens = [len(packet), len(packet)]
    pcm_batch = ffi.decode_opus_batch(joined, frame_lens)
    assert pcm_batch, "decode_opus_batch returned empty"
    print(
        "MojoAudioFFI smoke test ok",
        {
            "pcm_len": len(pcm or b""),
            "energy": energy,
            "encoded_len": len(encoded or b""),
            "batch_len": len(pcm_batch or b""),
        },
    )


if __name__ == "__main__":
    main()
