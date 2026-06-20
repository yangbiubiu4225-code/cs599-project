from pathlib import Path
from tempfile import NamedTemporaryFile
from typing import Any

import librosa
import numpy as np


PITCH_CLASSES = ["C", "C#", "D", "D#", "E", "F", "F#", "G", "G#", "A", "A#", "B"]


def _round_float(value: float, digits: int = 3) -> float:
    return round(float(value), digits)


def _first_float(value: Any) -> float:
    array = np.asarray(value).reshape(-1)
    if array.size == 0:
        return 0.0
    return float(array[0])


def analyze_audio(audio_path: str | Path) -> dict[str, Any]:
    path = Path(audio_path)
    y, sample_rate = librosa.load(path, sr=None, mono=True)

    duration = librosa.get_duration(y=y, sr=sample_rate)
    tempo, beat_frames = librosa.beat.beat_track(y=y, sr=sample_rate)
    chroma = librosa.feature.chroma_stft(y=y, sr=sample_rate)
    spectral_centroid = librosa.feature.spectral_centroid(y=y, sr=sample_rate)
    rms = librosa.feature.rms(y=y)
    zero_crossing_rate = librosa.feature.zero_crossing_rate(y)
    mfcc = librosa.feature.mfcc(y=y, sr=sample_rate, n_mfcc=13)

    chroma_means = chroma.mean(axis=1) if chroma.size else np.zeros(12)
    estimated_key = PITCH_CLASSES[int(np.argmax(chroma_means))]

    return {
        "file_name": path.name,
        "sample_rate": int(sample_rate),
        "duration_seconds": _round_float(duration),
        "tempo_bpm": _round_float(_first_float(tempo), 2),
        "beat_count": int(len(beat_frames)),
        "estimated_key": estimated_key,
        "rms_energy_mean": _round_float(rms.mean()),
        "zero_crossing_rate_mean": _round_float(zero_crossing_rate.mean()),
        "spectral_centroid_mean": _round_float(spectral_centroid.mean()),
        "mfcc_mean": [_round_float(value) for value in mfcc.mean(axis=1).tolist()],
    }


def save_uploaded_file(uploaded_file) -> Path:
    suffix = Path(uploaded_file.name).suffix or ".wav"
    with NamedTemporaryFile(delete=False, suffix=suffix) as tmp_file:
        tmp_file.write(uploaded_file.getbuffer())
        return Path(tmp_file.name)
