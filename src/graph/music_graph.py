from __future__ import annotations

from langgraph.graph import END, StateGraph

from src.agents.appreciation_agent import appreciate_music as appreciate_music_agent
from src.agents.prompt_agent import generate_prompt as generate_prompt_agent
from src.agents.requirement_agent import (
    understand_requirement as understand_requirement_agent,
)
from src.agents.revision_agent import generate_revision as generate_revision_agent
from src.agents.spec_agent import generate_music_spec as generate_music_spec_agent
from src.graph.state import MusicAgentState
from src.tools.audio_analyzer import analyze_audio as analyze_audio_tool
from src.tools.memory_store import save_history as save_history_tool
from src.tools.music_generator import generate_music as generate_music_tool
from src.tools.rag_retriever import (
    retrieve_music_context_for_state as retrieve_music_context_tool,
)


def _initial_state(
    user_requirement: str,
    run_mode: str,
    audio_path: str | None = None,
    generator_backend: str = "mock",
    latest_user_message: str = "",
) -> MusicAgentState:
    return {
        "run_mode": run_mode,
        "generator_backend": generator_backend,
        "user_requirement": user_requirement,
        "latest_user_message": latest_user_message or user_requirement,
        "retrieved_context": "",
        "rag_sources": [],
        "rag_matches": [],
        "music_spec": {},
        "generation_prompt": "",
        "audio_path": audio_path,
        "generation_result": {},
        "audio_features": {},
        "appreciation_result": {},
        "revision_suggestion": "",
        "optimized_prompt": "",
        "history_id": "",
    }


def understand_requirement(state: MusicAgentState) -> MusicAgentState:
    return understand_requirement_agent(state)


def retrieve_music_context(state: MusicAgentState) -> MusicAgentState:
    return retrieve_music_context_tool(state)


def generate_music_spec(state: MusicAgentState) -> MusicAgentState:
    return generate_music_spec_agent(state)


def generate_prompt(state: MusicAgentState) -> MusicAgentState:
    return generate_prompt_agent(state)


def generate_music(state: MusicAgentState) -> MusicAgentState:
    return generate_music_tool(state)


def analyze_audio(state: MusicAgentState) -> MusicAgentState:
    audio_path = state.get("audio_path")
    if not audio_path:
        return {"audio_features": {}}

    analysis_result = analyze_audio_tool(audio_path)
    if analysis_result["success"]:
        return {"audio_features": analysis_result["features"]}

    return {
        "audio_features": {
            "analysis_error": analysis_result["error"],
            "audio_path": audio_path,
        }
    }


def appreciate_music(state: MusicAgentState) -> MusicAgentState:
    return appreciate_music_agent(state)


def generate_revision(state: MusicAgentState) -> MusicAgentState:
    return generate_revision_agent(state)


def save_history(state: MusicAgentState) -> MusicAgentState:
    return save_history_tool(state)


def build_generation_graph():
    graph = StateGraph(MusicAgentState)

    graph.add_node("understand_requirement", understand_requirement)
    graph.add_node("retrieve_music_context", retrieve_music_context)
    graph.add_node("generate_music_spec", generate_music_spec)
    graph.add_node("generate_prompt", generate_prompt)
    graph.add_node("generate_music", generate_music)
    graph.add_node("analyze_audio", analyze_audio)
    graph.add_node("appreciate_music", appreciate_music)
    graph.add_node("generate_revision", generate_revision)
    graph.add_node("save_history", save_history)

    graph.set_entry_point("understand_requirement")
    graph.add_edge("understand_requirement", "retrieve_music_context")
    graph.add_edge("retrieve_music_context", "generate_music_spec")
    graph.add_edge("generate_music_spec", "generate_prompt")
    graph.add_edge("generate_prompt", "generate_music")
    graph.add_edge("generate_music", "analyze_audio")
    graph.add_edge("analyze_audio", "appreciate_music")
    graph.add_edge("appreciate_music", "generate_revision")
    graph.add_edge("generate_revision", "save_history")
    graph.add_edge("save_history", END)

    return graph.compile()


def build_appreciation_graph():
    graph = StateGraph(MusicAgentState)

    graph.add_node("understand_requirement", understand_requirement)
    graph.add_node("retrieve_music_context", retrieve_music_context)
    graph.add_node("generate_music_spec", generate_music_spec)
    graph.add_node("analyze_audio", analyze_audio)
    graph.add_node("appreciate_music", appreciate_music)
    graph.add_node("save_history", save_history)

    graph.set_entry_point("understand_requirement")
    graph.add_edge("understand_requirement", "retrieve_music_context")
    graph.add_edge("retrieve_music_context", "generate_music_spec")
    graph.add_edge("generate_music_spec", "analyze_audio")
    graph.add_edge("analyze_audio", "appreciate_music")
    graph.add_edge("appreciate_music", "save_history")
    graph.add_edge("save_history", END)

    return graph.compile()


def build_music_graph(run_mode: str = "generation"):
    if run_mode == "appreciation":
        return build_appreciation_graph()
    return build_generation_graph()


def run_generation_workflow(
    user_requirement: str,
    generator_backend: str = "mock",
    latest_user_message: str = "",
) -> MusicAgentState:
    app = build_generation_graph()
    initial_state = _initial_state(
        user_requirement=user_requirement,
        run_mode="generation",
        generator_backend=generator_backend,
        latest_user_message=latest_user_message,
    )
    return app.invoke(initial_state)


def run_appreciation_workflow(
    user_requirement: str,
    audio_path: str,
    latest_user_message: str = "",
) -> MusicAgentState:
    app = build_appreciation_graph()
    initial_state = _initial_state(
        user_requirement=user_requirement,
        run_mode="appreciation",
        audio_path=audio_path,
        latest_user_message=latest_user_message,
    )
    return app.invoke(initial_state)


def run_music_agent(user_requirement: str) -> MusicAgentState:
    return run_generation_workflow(user_requirement)
