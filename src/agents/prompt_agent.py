from src.graph.state import MusicAgentState


def generate_prompt(state: MusicAgentState) -> MusicAgentState:
    spec = state.get("music_spec", {})
    structure = ", ".join(spec.get("structure", []))
    instruments = ", ".join(spec.get("instruments", []))

    generation_prompt = (
        f"Generate a {spec.get('duration_seconds', 12)} second {spec.get('style', 'music')} "
        f"piece in {spec.get('key', 'C major')} at {spec.get('tempo_bpm', 120)} BPM. "
        f"The mood should be {spec.get('mood', 'focused')}. "
        f"Use {instruments or 'a small modern ensemble'}. "
        f"Follow this structure: {structure or 'motif, development, ending'}. "
        "Prioritize a memorable motif, clear section contrast, and clean production."
    )

    return {"generation_prompt": generation_prompt}
