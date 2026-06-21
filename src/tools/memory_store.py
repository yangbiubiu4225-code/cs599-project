import json
from pathlib import Path
from uuid import uuid4

from src.graph.state import MusicAgentState


def save_history(state: MusicAgentState) -> MusicAgentState:
    history_id = state.get("history_id") or str(uuid4())
    history_dir = Path("data/history")
    history_dir.mkdir(parents=True, exist_ok=True)

    snapshot = {
        "history_id": history_id,
        "run_mode": state.get("run_mode", ""),
        "generator_backend": state.get("generator_backend", ""),
        "user_requirement": state.get("user_requirement", ""),
        "rag_query": state.get("rag_query", ""),
        "rag_summary": state.get("rag_summary", ""),
        "rag_intent_profile": state.get("rag_intent_profile", {}),
        "retrieved_context": state.get("retrieved_context", ""),
        "rag_sources": state.get("rag_sources", []),
        "rag_matches": state.get("rag_matches", []),
        "music_spec": state.get("music_spec", {}),
        "generation_prompt": state.get("generation_prompt", ""),
        "audio_path": state.get("audio_path"),
        "generation_result": state.get("generation_result", {}),
        "audio_features": state.get("audio_features", {}),
        "appreciation_result": state.get("appreciation_result", {}),
        "revision_suggestion": state.get("revision_suggestion", ""),
        "optimized_prompt": state.get("optimized_prompt", ""),
    }

    history_path = history_dir / f"{history_id}.json"
    history_path.write_text(
        json.dumps(snapshot, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )

    return {"history_id": history_id}


def load_history(history_id: str) -> dict:
    history_path = Path("data/history") / f"{history_id}.json"
    if not history_path.exists():
        raise FileNotFoundError(f"History record not found: {history_id}")
    return json.loads(history_path.read_text(encoding="utf-8"))
