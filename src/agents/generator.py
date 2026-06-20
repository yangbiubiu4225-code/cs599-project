from src.graph.state import MusicState


def _format_audio_hint(analysis: dict) -> str:
    if not analysis:
        return "No reference audio was provided, so the plan should rely on the creative brief."

    tempo = analysis.get("tempo_bpm", "unknown")
    key = analysis.get("estimated_key", "unknown")
    energy = analysis.get("rms_energy_mean", "unknown")
    brightness = analysis.get("spectral_centroid_mean", "unknown")
    return (
        f"Reference audio suggests tempo around {tempo} BPM, pitch center {key}, "
        f"energy {energy}, and brightness {brightness}."
    )


def draft_music_idea(state: MusicState) -> MusicState:
    iteration = int(state.get("iteration", 0)) + 1
    user_prompt = state.get("user_prompt", "").strip()
    analysis = state.get("audio_analysis", {})
    previous_critique = state.get("critique", "")

    refinement = ""
    if previous_critique:
        refinement = f"\n\nRefinement focus from critique:\n{previous_critique}"

    generation_plan = f"""
Iteration {iteration} composition plan

Creative brief:
{user_prompt}

Audio-aware direction:
{_format_audio_hint(analysis)}

Arrangement proposal:
- Establish a concise motif in the first 8 bars.
- Build a clear A/B structure with contrast in register, density, or timbre.
- Reserve one sonic signature for identity, such as a lead texture, rhythmic hook, or harmonic color.
- Leave space for critique-driven revision in the next iteration.
{refinement}
""".strip()

    return {
        "generation_plan": generation_plan,
        "iteration": iteration,
    }
