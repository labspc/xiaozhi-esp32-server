import ctypes
import logging
import os
import sys
from array import array
from pathlib import Path
from typing import Optional

logger = logging.getLogger(__name__)


class MojoAudioFFI:
    """Load `libmojo_audio` with ctypes and provide python fallbacks."""

    def __init__(
        self,
        lib_path: Optional[str] = None,
        enabled: bool = True,
        max_frame_ms: int = 120,
    ) -> None:
        env_enabled = os.getenv("MOJO_AUDIO_ENABLED")
        self.enabled = enabled and env_enabled != "0"
        self.max_frame_ms = max_frame_ms
        self._lib_path = lib_path
        self._lib: Optional[ctypes.CDLL] = None
        self._load_error: Optional[str] = None
        if self.enabled:
            self._load()
        else:
            self._load_error = "disabled by config/env"

    @property
    def available(self) -> bool:
        return self._lib is not None

    @property
    def load_error(self) -> Optional[str]:
        return self._load_error

    def decode_opus(
        self,
        opus_data: bytes,
        sample_rate: int = 16_000,
        channels: int = 1,
    ) -> Optional[bytes]:
        if not opus_data:
            return b""
        if self._lib:
            out_samples = max(int(sample_rate * self.max_frame_ms / 1000) * max(channels, 1), 1)
            out_buf = (ctypes.c_short * out_samples)()
            in_buf = (ctypes.c_ubyte * len(opus_data)).from_buffer_copy(opus_data)
            rc = self._lib.opus_decode(
                in_buf,
                len(opus_data),
                sample_rate,
                channels,
                out_buf,
                out_samples,
            )
            if rc >= 0:
                total = rc * channels
                return array("h", out_buf[:total]).tobytes()
            logger.debug("mojo opus_decode fallback, rc=%s", rc)
        return _decode_opus_python(opus_data, sample_rate, channels, self.max_frame_ms)

    def pcm_to_float(self, pcm_data: bytes) -> Optional[bytes]:
        if not pcm_data:
            return b""
        samples = len(pcm_data) // 2
        if samples == 0:
            return b""
        if self._lib:
            in_buf = (ctypes.c_short * samples).from_buffer_copy(pcm_data)
            out_buf = (ctypes.c_float * samples)()
            rc = self._lib.pcm_to_float(in_buf, samples, out_buf)
            if rc >= 0:
                return array("f", out_buf[:rc]).tobytes()
            logger.debug("mojo pcm_to_float fallback, rc=%s", rc)
        return _pcm_to_float_python(pcm_data)

    def vad_energy(self, float_data: bytes) -> Optional[float]:
        if not float_data:
            return 0.0
        elements = len(float_data) // 4
        if elements == 0:
            return 0.0
        if self._lib:
            in_buf = (ctypes.c_float * elements).from_buffer_copy(float_data)
            energy = self._lib.vad_energy(in_buf, elements)
            return float(energy)
        return _vad_energy_python(float_data)

    def _load(self) -> None:
        path = self._resolve_lib_path()
        if not path:
            self._load_error = "libmojo_audio not found"
            return
        try:
            lib = ctypes.cdll.LoadLibrary(str(path))
            lib.opus_decode.argtypes = [
                ctypes.POINTER(ctypes.c_ubyte),
                ctypes.c_int,
                ctypes.c_int,
                ctypes.c_int,
                ctypes.POINTER(ctypes.c_short),
                ctypes.c_int,
            ]
            lib.opus_decode.restype = ctypes.c_int
            lib.pcm_to_float.argtypes = [
                ctypes.POINTER(ctypes.c_short),
                ctypes.c_int,
                ctypes.POINTER(ctypes.c_float),
            ]
            lib.pcm_to_float.restype = ctypes.c_int
            lib.vad_energy.argtypes = [ctypes.POINTER(ctypes.c_float), ctypes.c_int]
            lib.vad_energy.restype = ctypes.c_float
            self._lib = lib
            self._lib_path = str(path)
            self._load_error = None
            logger.info("Loaded libmojo_audio from %s", path)
        except OSError as exc:
            self._load_error = str(exc)
            self._lib = None
            logger.warning("Failed to load libmojo_audio: %s", exc)

    def _resolve_lib_path(self) -> Optional[Path]:
        env_path = os.getenv("MOJO_AUDIO_LIB")
        if env_path:
            env_candidate = Path(env_path)
            if env_candidate.exists():
                return env_candidate
        if self._lib_path:
            candidate = Path(self._lib_path)
            if candidate.exists():
                return candidate
        base = Path(__file__).resolve().parents[1]
        lib_name = _platform_lib_name()
        for profile in ("release", "debug"):
            candidate = base / "target" / profile / lib_name
            if candidate.exists():
                return candidate
        return None


def _platform_lib_name() -> str:
    if sys.platform.startswith("darwin"):
        return "libmojo_audio.dylib"
    if sys.platform.startswith("win"):
        return "mojo_audio.dll"
    return "libmojo_audio.so"


def _decode_opus_python(
    opus_data: bytes,
    sample_rate: int,
    channels: int,
    max_frame_ms: int,
) -> Optional[bytes]:
    try:
        import opuslib_next
    except ImportError:
        logger.warning("opuslib_next missing; cannot decode opus without libmojo_audio")
        return None
    frame_size = max(int(sample_rate * max_frame_ms / 1000), 1)
    decoder = opuslib_next.Decoder(sample_rate, channels)
    try:
        pcm = decoder.decode(opus_data, frame_size)
        return pcm
    except opuslib_next.OpusError as exc:
        logger.warning("python opus decode failed: %s", exc)
        return None


def _pcm_to_float_python(pcm_data: bytes) -> Optional[bytes]:
    pcm = array("h")
    pcm.frombytes(pcm_data)
    floats = array("f", (sample / 32768.0 for sample in pcm))
    return floats.tobytes()


def _vad_energy_python(float_data: bytes) -> float:
    floats = array("f")
    floats.frombytes(float_data)
    return float(sum(v * v for v in floats))
