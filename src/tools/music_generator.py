import hashlib
import os
from functools import lru_cache
from pathlib import Path
from typing import Any
from uuid import uuid4

import numpy as np
import soundfile as sf

from src.graph.state import MusicAgentState


NOTE_TO_FREQUENCY = {
    "C": 261.63,
    "C#": 277.18,
    "D": 293.66,
    "D#": 311.13,
    "E": 329.63,
    "F": 349.23,
    "F#": 369.99,
    "G": 392.00,
    "G#": 415.30,
    "A": 440.00,
    "A#": 466.16,
    "B": 493.88,
}


def _root_frequency(key: str) -> float:
    root = key.split()[0].upper()
    return NOTE_TO_FREQUENCY.get(root, NOTE_TO_FREQUENCY["C"])


def _adsr_envelope(length: int, sample_rate: int) -> np.ndarray:
    attack = min(int(0.02 * sample_rate), length)
    release = min(int(0.08 * sample_rate), max(0, length - attack))
    sustain = max(0, length - attack - release)

    envelope = np.concatenate(
        [
            np.linspace(0.0, 1.0, attack, endpoint=False),
            np.full(sustain, 0.75),
            np.linspace(0.75, 0.0, release, endpoint=True),
        ]
    )
    if envelope.size < length:
        envelope = np.pad(envelope, (0, length - envelope.size))
    return envelope[:length]


def _safe_duration(value: Any, default: int = 8) -> int:
    try:
        duration = int(float(value))
    except (TypeError, ValueError):
        return default
    return max(1, min(duration, 30))


def _seed_from_state(state: MusicAgentState) -> int:
    prompt = state.get("generation_prompt", "")
    spec = state.get("music_spec", {})
    source = f"{prompt}|{spec.get('mood')}|{spec.get('tempo_bpm')}|{spec.get('key')}"
    digest = hashlib.sha256(source.encode("utf-8")).hexdigest()
    return int(digest[:8], 16)


def _interval_pattern(mood: str, key: str) -> list[int]:
    is_minor = "minor" in key.lower()
    if mood == "uplifting":
        return [0, 4, 7, 12, 9, 7, 4, 2]
    if mood == "energetic":
        return [0, 7, 5, 7, 10 if is_minor else 11, 7, 5, 3]
    if mood in {"dark", "mysterious"} or is_minor:
        return [0, 3, 7, 10, 8, 7, 3, 2]
    if mood == "calm":
        return [0, 2, 4, 7, 4, 2, 0, -5]
    return [0, 2, 4, 7, 9, 7, 4, 2]


def _write_mock_audio(state: MusicAgentState, history_id: str) -> str:
    spec = state.get("music_spec", {})
    mood = str(spec.get("mood", "focused"))
    key = str(spec.get("key", "C major"))
    rng = np.random.default_rng(_seed_from_state(state))
    output_dir = Path("data/generated")
    output_dir.mkdir(parents=True, exist_ok=True)

    sample_rate = 22_050
    duration = float(_safe_duration(spec.get("duration_seconds", 8), default=8))
    tempo_bpm = float(spec.get("tempo_bpm", 120))
    seconds_per_beat = 60.0 / tempo_bpm
    root = _root_frequency(key)
    intervals = _interval_pattern(mood, key)

    lead_gain = {
        "calm": 0.22,
        "uplifting": 0.32,
        "energetic": 0.38,
        "dark": 0.28,
        "mysterious": 0.26,
    }.get(mood, 0.30)
    pad_gain = 0.20 if mood in {"calm", "mysterious"} else 0.12
    brightness_gain = {
        "uplifting": 0.18,
        "energetic": 0.12,
        "calm": 0.06,
        "dark": 0.04,
        "mysterious": 0.08,
    }.get(mood, 0.10)

    total_samples = int(sample_rate * duration)
    audio = np.zeros(total_samples, dtype=np.float32)
    beat_samples = max(1, int(sample_rate * seconds_per_beat))

    for index, interval in enumerate(intervals * 8):
        start = index * beat_samples
        if start >= total_samples:
            break
        end = min(start + beat_samples, total_samples)
        length = end - start
        detune = rng.uniform(-0.004, 0.004)
        frequency = root * (2 ** (interval / 12)) * (1.0 + detune)
        t = np.arange(length) / sample_rate
        tone = lead_gain * np.sin(2 * np.pi * frequency * t)
        harmonic = brightness_gain * np.sin(2 * np.pi * frequency * 2.0 * t)
        pad = pad_gain * np.sin(2 * np.pi * (root / 2) * t)
        audio[start:end] += (tone + harmonic + pad) * _adsr_envelope(length, sample_rate)

    subdivision = 4 if mood == "energetic" else 2
    if mood == "calm":
        subdivision = 1
    click_interval = max(1, beat_samples // subdivision)
    click_gain = {
        "calm": 0.12,
        "uplifting": 0.24,
        "energetic": 0.36,
        "dark": 0.20,
        "mysterious": 0.18,
    }.get(mood, 0.22)
    for start in range(0, total_samples, click_interval):
        end = min(start + int(0.015 * sample_rate), total_samples)
        click = np.linspace(click_gain, 0.0, end - start, endpoint=True)
        audio[start:end] += click * rng.uniform(0.85, 1.15)

    if mood == "uplifting":
        shimmer = 0.04 * np.sin(2 * np.pi * (root * 4) * np.arange(total_samples) / sample_rate)
        audio += shimmer.astype(np.float32)

    peak = float(np.max(np.abs(audio)))
    if peak > 0:
        audio = audio / peak * 0.85

    audio_path = output_dir / f"{history_id}.wav"
    sf.write(audio_path, audio, sample_rate)
    return str(audio_path)


@lru_cache(maxsize=1)
def _load_musicgen_model(model_name: str):
    cache_dir = Path(os.getenv("MUSICGEN_CACHE_DIR", "data/model_cache"))
    cache_dir.mkdir(parents=True, exist_ok=True)
    os.environ.setdefault("HF_HOME", str(cache_dir))
    os.environ.setdefault("TRANSFORMERS_CACHE", str(cache_dir))

    import torch
    from transformers import AutoProcessor, MusicgenForConditionalGeneration

    processor = AutoProcessor.from_pretrained(model_name)
    model = MusicgenForConditionalGeneration.from_pretrained(model_name)

    requested_device = os.getenv("MUSICGEN_DEVICE", "auto").lower()
    if requested_device == "auto":
        device = "mps" if torch.backends.mps.is_available() else "cpu"
    else:
        device = requested_device

    model.to(device)
    model.eval()
    return processor, model, device


def _write_musicgen_audio(state: MusicAgentState, history_id: str) -> str:
    spec = state.get("music_spec", {})
    prompt = state.get("generation_prompt") or state.get("user_requirement", "")
    output_dir = Path("data/generated")
    output_dir.mkdir(parents=True, exist_ok=True)

    model_name = os.getenv("MUSICGEN_MODEL", "facebook/musicgen-small")
    default_duration = os.getenv("MUSICGEN_DURATION") or spec.get("duration_seconds", 8)
    duration = _safe_duration(default_duration, default=8)

    processor, model, device = _load_musicgen_model(model_name)
    inputs = processor(
        text=[prompt],
        padding=True,
        return_tensors="pt",
    ).to(device)

    frame_rate = getattr(model.config.audio_encoder, "frame_rate", 50)
    max_new_tokens = int(duration * frame_rate)
    audio_values = model.generate(
        **inputs,
        max_new_tokens=max_new_tokens,
    )

    sampling_rate = model.config.audio_encoder.sampling_rate
    audio = audio_values[0, 0].detach().cpu().numpy()
    audio_path = output_dir / f"{history_id}.wav"
    sf.write(audio_path, audio, sampling_rate)
    return str(audio_path)


def generate_music(state: MusicAgentState) -> MusicAgentState:
    history_id = state.get("history_id") or str(uuid4())
    requested_backend = (
        state.get("generator_backend")
        or os.getenv("MUSIC_GENERATOR_BACKEND", "mock")
    ).lower()

    if requested_backend not in {"mock", "musicgen"}:
        requested_backend = "mock"

    generation_result: dict[str, Any] = {
        "requested_backend": requested_backend,
        "used_backend": requested_backend,
        "status": "success",
        "error": None,
        "fallback_used": False,
    }

    try:
        if requested_backend == "musicgen":
            audio_path = _write_musicgen_audio(state, history_id)
        else:
            audio_path = _write_mock_audio(state, history_id)
    except Exception as exc:
        fallback_enabled = os.getenv("MUSICGEN_FALLBACK_TO_MOCK", "true").lower()
        if requested_backend != "musicgen" or fallback_enabled not in {"1", "true", "yes"}:
            raise

        audio_path = _write_mock_audio(state, history_id)
        generation_result.update(
            {
                "used_backend": "mock",
                "status": "fallback",
                "error": {
                    "type": exc.__class__.__name__,
                    "message": str(exc),
                },
                "fallback_used": True,
            }
        )

    return {
        "audio_path": audio_path,
        "generation_result": generation_result,
        "history_id": history_id,
    }
