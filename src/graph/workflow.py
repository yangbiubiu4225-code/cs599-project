from langgraph.graph import END, StateGraph

from src.agents.critic import critique_music
from src.agents.curator import finalize_session
from src.agents.generator import draft_music_idea
from src.graph.state import MusicState
from src.tools.audio_analysis import analyze_audio


def analyze_reference_audio(state: MusicState) -> MusicState:
    audio_path = state.get("audio_path")
    if not audio_path:
        return {"audio_analysis": {}}

    return {"audio_analysis": analyze_audio(audio_path)}


def route_after_critique(state: MusicState) -> str:
    iteration = int(state.get("iteration", 0))
    max_iterations = int(state.get("max_iterations", 1))
    if iteration < max_iterations:
        return "iterate"
    return "finalize"


def build_graph():
    graph = StateGraph(MusicState)
    graph.add_node("analyze", analyze_reference_audio)
    graph.add_node("generate", draft_music_idea)
    graph.add_node("critique", critique_music)
    graph.add_node("finalize", finalize_session)

    graph.set_entry_point("analyze")
    graph.add_edge("analyze", "generate")
    graph.add_edge("generate", "critique")
    graph.add_conditional_edges(
        "critique",
        route_after_critique,
        {
            "iterate": "generate",
            "finalize": "finalize",
        },
    )
    graph.add_edge("finalize", END)

    return graph.compile()


def run_music_workflow(
    user_prompt: str,
    audio_path: str | None = None,
    max_iterations: int = 2,
) -> MusicState:
    app = build_graph()
    initial_state: MusicState = {
        "user_prompt": user_prompt,
        "audio_path": audio_path,
        "iteration": 0,
        "max_iterations": max_iterations,
    }
    return app.invoke(initial_state)
