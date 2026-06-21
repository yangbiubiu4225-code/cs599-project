from src.graph.state import MusicAgentState


def _compact_context(context: str, limit: int = 480) -> str:
    if not context:
        return ""

    lines = []
    for line in context.splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith("#") or stripped.startswith("["):
            continue
        if stripped.lower().startswith("keywords:"):
            continue
        lines.append(stripped)

    compact = " ".join(lines)
    return compact[:limit].rstrip()


def generate_prompt(state: MusicAgentState) -> MusicAgentState:
    spec = state.get("music_spec", {})
    structure = ", ".join(spec.get("structure", []))
    instruments = ", ".join(spec.get("instruments", []))
    rag_guidance = _compact_context(state.get("retrieved_context", ""))

    generation_prompt = (
        f"Generate a {spec.get('duration_seconds', 12)} second {spec.get('style', 'music')} "
        f"piece in {spec.get('key', 'C major')} at {spec.get('tempo_bpm', 120)} BPM. "
        f"The mood should be {spec.get('mood', 'focused')}. "
        f"Use {instruments or 'a small modern ensemble'}. "
        f"Follow this structure: {structure or 'motif, development, ending'}. "
        "Prioritize a memorable motif, clear section contrast, and clean production."
    )
    if rag_guidance:
        generation_prompt += f" Reference style guidance: {rag_guidance}"

    return {"generation_prompt": generation_prompt}
