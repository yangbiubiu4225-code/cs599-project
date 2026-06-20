from __future__ import annotations

from pathlib import Path
from typing import Any

import librosa
import numpy as np


def _as_float(value: Any, digits: int = 6) -> float:
    return round(float(value), digits)


def _mean_feature(value: Any) -> float:
    array = np.asarray(value)
    if array.size == 0:
        return 0.0
    return _as_float(array.mean())


def _first_value(value: Any) -> float:
    array = np.asarray(value).reshape(-1)
    if array.size == 0:
        return 0.0
    return _as_float(array[0])


def analyze_audio(audio_path: str | Path) -> dict[str, Any]:
    """Analyze an audio file and return JSON-serializable feature data."""
    path = Path(audio_path)

    try:
        if not path.exists():
            raise FileNotFoundError(f"Audio file not found: {path}")
        if not path.is_file():
            raise ValueError(f"Audio path is not a file: {path}")

        y, sample_rate = librosa.load(path, sr=None, mono=True)
        if y.size == 0:
            raise ValueError(f"Audio file is empty: {path}")

        duration = librosa.get_duration(y=y, sr=sample_rate)
        tempo, _ = librosa.beat.beat_track(y=y, sr=sample_rate)
        rms = librosa.feature.rms(y=y)
        spectral_centroid = librosa.feature.spectral_centroid(y=y, sr=sample_rate)
        zero_crossing_rate = librosa.feature.zero_crossing_rate(y)
        onset_strength = librosa.onset.onset_strength(y=y, sr=sample_rate)

        return {
            "success": True,
            "audio_path": str(path),
            "features": {
                "duration": _as_float(duration),
                "tempo": _first_value(tempo),
                "rms_energy": _mean_feature(rms),
                "spectral_centroid_mean": _mean_feature(spectral_centroid),
                "zero_crossing_rate_mean": _mean_feature(zero_crossing_rate),
                "onset_strength_mean": _mean_feature(onset_strength),
            },
            "error": None,
        }
    except Exception as exc:
        return {
            "success": False,
            "audio_path": str(path),
            "features": {},
            "error": {
                "type": exc.__class__.__name__,
                "message": str(exc),
            },
        }
