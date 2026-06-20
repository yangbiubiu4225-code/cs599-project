from src.graph.state import MusicState


def finalize_session(state: MusicState) -> MusicState:
    iteration = state.get("iteration", 0)
    recommendations = state.get("recommendations", [])
    recommendation_text = "\n".join(f"- {item}" for item in recommendations)

    final_summary = f"""
Final session summary

Completed {iteration} agent iteration(s). The latest plan is ready for a generation backend or manual production pass. Use the critique recommendations as the revision checklist:

{recommendation_text or "- No recommendations were produced."}
""".strip()

    return {"final_summary": final_summary}
