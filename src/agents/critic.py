from src.eval.metrics import score_audio_profile
from src.graph.state import MusicState


def critique_music(state: MusicState) -> MusicState:
    generation_plan = state.get("generation_plan", "")
    analysis = state.get("audio_analysis", {})
    scores = score_audio_profile(analysis)

    recommendations: list[str] = []
    if scores["tempo_stability"] < 0.5:
        recommendations.append("Clarify the rhythmic pulse before adding dense arrangement layers.")
    else:
        recommendations.append("Use the stable pulse as a foundation for motif variation.")

    if scores["energy"] < 0.4:
        recommendations.append("Increase perceived movement through percussion, bass motion, or automation.")
    elif scores["energy"] > 0.8:
        recommendations.append("Add contrast with quieter sections so the loud moments feel earned.")
    else:
        recommendations.append("Keep the current energy contour and focus on timbral identity.")

    if scores["brightness"] > 0.75:
        recommendations.append("Balance bright elements with warmer midrange support.")
    else:
        recommendations.append("Consider a brighter lead or transient layer for more presence.")

    critique = f"""
Critique

The current plan is coherent and usable for the requested direction. Its strongest element is the explicit motif-first structure. The next revision should make the contrast strategy more concrete: define what changes between sections, what remains recognizable, and how the listener can hear progress across iterations.

Profile scores:
- Tempo stability: {scores["tempo_stability"]:.2f}
- Energy: {scores["energy"]:.2f}
- Brightness: {scores["brightness"]:.2f}

Plan reviewed:
{generation_plan}
""".strip()

    return {
        "critique": critique,
        "recommendations": recommendations,
    }
