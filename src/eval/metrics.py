def _clamp(value: float, low: float = 0.0, high: float = 1.0) -> float:
    return max(low, min(high, value))


def score_audio_profile(analysis: dict) -> dict[str, float]:
    if not analysis:
        return {
            "tempo_stability": 0.5,
            "energy": 0.5,
            "brightness": 0.5,
        }

    tempo = float(analysis.get("tempo_bpm") or 120.0)
    energy = float(analysis.get("rms_energy_mean") or 0.0)
    brightness = float(analysis.get("spectral_centroid_mean") or 0.0)

    tempo_stability = 1.0 if 60.0 <= tempo <= 180.0 else 0.4
    normalized_energy = _clamp(energy * 12.0)
    normalized_brightness = _clamp(brightness / 5000.0)

    return {
        "tempo_stability": tempo_stability,
        "energy": normalized_energy,
        "brightness": normalized_brightness,
    }
