from __future__ import annotations

from typing import Any, Optional, TypedDict


class MusicAgentState(TypedDict, total=False):
    """Shared state passed between MusicAgent Studio LangGraph nodes."""

    run_mode: str
    generator_backend: str
    user_requirement: str
    latest_user_message: str
    music_spec: dict[str, Any]
    generation_prompt: str
    audio_path: Optional[str]
    generation_result: dict[str, Any]
    audio_features: dict[str, Any]
    appreciation_result: dict[str, Any]
    revision_suggestion: str
    optimized_prompt: str
    history_id: str


class MusicState(MusicAgentState, total=False):
    """Backward-compatible state fields used by the initial Streamlit scaffold."""

    user_prompt: str
    audio_path: Optional[str]
    audio_analysis: dict[str, Any]
    generation_plan: str
    critique: str
    recommendations: list[str]
    iteration: int
    max_iterations: int
    final_summary: str
