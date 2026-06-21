# API Spec

This project currently exposes Python function interfaces rather than a network API.

## `run_generation_workflow`

Location: `src/graph/music_graph.py`

```python
run_generation_workflow(
    user_requirement: str,
    generator_backend: str = "mock",
) -> MusicAgentState
```

Runs the full AI music generation workflow and returns the final state.
The workflow includes a RAG retrieval node before Music Spec generation.

## `run_appreciation_workflow`

Location: `src/graph/music_graph.py`

```python
run_appreciation_workflow(
    user_requirement: str,
    audio_path: str,
) -> MusicAgentState
```

Runs the AI music appreciation workflow. This skips the music generation node and analyzes the provided audio path.
The workflow still retrieves relevant style and appreciation knowledge before analysis.

## `retrieve_music_context`

Location: `src/tools/rag_retriever.py`

```python
retrieve_music_context(
    query: str,
    top_k: int = 3,
) -> dict
```

Retrieves relevant Markdown chunks from `src/knowledge/` and returns:

```json
{
  "retrieved_context": "matched knowledge text",
  "rag_sources": ["src/knowledge/music_styles.md#Cyberpunk / Sci-Fi Electronic"],
  "rag_matches": [
    {
      "source": "src/knowledge/music_styles.md",
      "title": "Cyberpunk / Sci-Fi Electronic",
      "score": 4.5,
      "text": "..."
    }
  ]
}
```

## `generate_music`

Location: `src/tools/music_generator.py`

```python
generate_music(state: MusicAgentState) -> MusicAgentState
```

Supports two backends:

- `mock`
- `musicgen`

Backend choice is read from `state["generator_backend"]` or `MUSIC_GENERATOR_BACKEND`.

## `analyze_audio`

Location: `src/tools/audio_analyzer.py`

```python
analyze_audio(audio_path: str) -> dict
```

Returns JSON-serializable audio analysis output:

```json
{
  "success": true,
  "audio_path": "data/generated/example.wav",
  "features": {
    "duration": 12.0,
    "tempo": 120.0,
    "rms_energy": 0.1,
    "spectral_centroid_mean": 1200.0,
    "zero_crossing_rate_mean": 0.04,
    "onset_strength_mean": 0.8
  },
  "error": null
}
```

## `save_history`

Location: `src/tools/memory_store.py`

```python
save_history(state: MusicAgentState) -> MusicAgentState
```

Writes a JSON history file under `data/history/` and returns the `history_id`.
