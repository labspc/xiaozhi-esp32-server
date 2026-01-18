import logging
import os
from typing import Iterable, List, Optional

try:
    import opuslib_next
except ImportError:  # pragma: no cover - optional dependency location
    opuslib_next = None  # type: ignore

try:
    from mojo.ffi import MojoAudioFFI
except ImportError:  # pragma: no cover - optional dependency location
    MojoAudioFFI = None  # type: ignore

logger = logging.getLogger(__name__)
_mojo_audio: Optional["MojoAudioFFI"] = None


def _get_mojo_audio() -> Optional["MojoAudioFFI"]:
    global _mojo_audio
    if _mojo_audio is not None:
        return _mojo_audio
    if MojoAudioFFI is None:
        logger.debug("MojoAudioFFI not available (import failed)")
        return None
    enabled = os.getenv("MOJO_AUDIO_ENABLED", "1") != "0"
    lib_path = os.getenv("MOJO_AUDIO_LIB")
    _mojo_audio = MojoAudioFFI(lib_path=lib_path or None, enabled=enabled)
    if not _mojo_audio.available and _mojo_audio.load_error:
        logger.info("Mojo audio disabled or unavailable: %s", _mojo_audio.load_error)
    return _mojo_audio


def decode_opus_packets(
    opus_packets: Iterable[bytes],
    sample_rate: int = 16_000,
    channels: int = 1,
) -> List[bytes]:
    """
    Try decoding opus packets via MojoAudioFFI, auto-fallback to python decode.
    Returns list of PCM frames (bytes). Silent on per-frame failures.
    """
    pcm_frames: List[bytes] = []
    mojo = _get_mojo_audio()
    decoder = None
    if mojo is None and opuslib_next:
        try:
            decoder = opuslib_next.Decoder(sample_rate, channels)
        except Exception as exc:  # pragma: no cover - initialization failure
            logger.info("Opuslib decoder init failed: %s", exc)

    for idx, packet in enumerate(opus_packets):
        if not packet:
            continue
        decoded: Optional[bytes] = None
        if mojo:
            decoded = mojo.decode_opus(packet, sample_rate=sample_rate, channels=channels)
        elif decoder:
            try:
                decoded = decoder.decode(packet, max(int(sample_rate * 0.12), 960))
            except Exception:
                decoded = None
        if decoded:
            pcm_frames.append(decoded)
        else:
            logger.debug("Opus decode failed for packet %s", idx)
    return pcm_frames
