import logging
import os
from typing import Iterable, List, Mapping, Optional

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
_preferred_enabled: Optional[bool] = None
_preferred_lib_path: Optional[str] = None


def _get_mojo_audio() -> Optional["MojoAudioFFI"]:
    global _mojo_audio
    if _mojo_audio is not None:
        return _mojo_audio
    if MojoAudioFFI is None:
        logger.debug("MojoAudioFFI not available (import failed)")
        return None
    env_enabled = os.getenv("MOJO_AUDIO_ENABLED")
    enabled = _preferred_enabled if env_enabled is None else env_enabled != "0"
    env_lib = os.getenv("MOJO_AUDIO_LIB")
    lib_path = env_lib or _preferred_lib_path
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


def configure_mojo_audio(config: Optional[Mapping] = None) -> None:
    """
    Set preferred enable/lib_path from config. Env vars still override.
    Expected config structure:
    mojo:
      audio_enabled: true|false
      audio_lib: /path/to/libmojo_audio.so
    """
    global _preferred_enabled, _preferred_lib_path, _mojo_audio
    if config and isinstance(config, Mapping):
        mojo_cfg = config.get("mojo", {}) if isinstance(config.get("mojo", {}), Mapping) else {}
        if "audio_enabled" in mojo_cfg:
            _preferred_enabled = bool(mojo_cfg.get("audio_enabled"))
        if "audio_lib" in mojo_cfg:
            _preferred_lib_path = mojo_cfg.get("audio_lib") or None
        _mojo_audio = None  # reset so next access reloads with new config


def log_mojo_audio_status(logger_obj: Optional[logging.Logger] = None) -> None:
    log = logger_obj or logger
    mojo = _get_mojo_audio()
    if mojo is None:
        log.info("Audio accelerator (Rust ABI, Mojo-compatible) not loaded (module missing or disabled)")
        return
    if mojo.available:
        log.info(
            "Audio accelerator enabled (Rust ABI, Mojo-compatible) lib=%s, load_error=%s",
            getattr(mojo, "_lib_path", None),
            mojo.load_error,
        )
    else:
        log.info("Audio accelerator unavailable: %s", mojo.load_error or "unknown reason")


def encode_opus_frame(
    pcm_data: bytes,
    sample_rate: int = 16_000,
    channels: int = 1,
) -> Optional[bytes]:
    """
    Encode a PCM frame to Opus using Mojo if available, otherwise opuslib_next.
    pcm_data: int16 little-endian PCM bytes.
    """
    if not pcm_data:
        return b""
    mojo = _get_mojo_audio()
    if mojo:
        encoded = mojo.encode_opus(pcm_data, sample_rate=sample_rate, channels=channels)
        if encoded:
            return encoded
        logger.debug("Mojo opus_encode fallback to python")
    if opuslib_next:
        try:
            encoder = opuslib_next.Encoder(sample_rate, channels, opuslib_next.APPLICATION_AUDIO)
            frame_size = max((len(pcm_data) // 2) // max(channels, 1), 1)
            return encoder.encode(pcm_data, frame_size)
        except Exception as exc:
            logger.debug("Opuslib encode failed: %s", exc)
            return None
    logger.info("No Opus encoder available (Mojo disabled and opuslib_next missing)")
    return None
