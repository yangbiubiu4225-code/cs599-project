# Architecture

## Overview

MusicAgent Studio uses Streamlit for the UI and LangGraph for workflow orchestration. The system has two user-facing modes: AI music generation and AI music appreciation. Each graph node delegates work to a focused agent or tool module.

```mermaid
flowchart TD
    A["Streamlit UI"] --> B{"Run Mode"}
    B -->|"AI Music Generation"| C["Generation StateGraph"]
    B -->|"AI Music Appreciation"| D["Appreciation StateGraph"]
    C --> E["Requirement Agent"]
    D --> E
    E --> F["Spec Agent"]
    F --> G["Prompt Agent"]
    G -->|"Generation mode only"| H["Music Generator Tool"]
    H --> I["Audio Analyzer Tool"]
    G -->|"Appreciation mode skips generation"| I
    I --> J["Appreciation Agent"]
    J --> K["Revision Agent"]
    K --> L["Memory Store Tool"]
```

## State

The shared state is `MusicAgentState` in `src/graph/state.py`. It contains run mode, generator backend, user requirements, generated specifications, prompt text, audio paths, generation result, audio features, appreciation output, revision suggestions, optimized prompt, and history ID.

## Modules

- `src/app.py`: Streamlit course demo interface.
- `src/graph/music_graph.py`: LangGraph workflow definition for both modes.
- `src/agents/`: Reasoning stages for requirement understanding, spec creation, prompt generation, appreciation, and revision.
- `src/tools/`: Side-effect or IO functions for audio generation, audio analysis, history storage, and report writing.
- `src/prompts/`: Prompt templates for later LLM integration.
- `src/eval/`: Lightweight test cases and evaluation runner.

## Generation Mode Data Flow

1. User submits requirement.
2. Requirement Agent normalizes the request.
3. Spec Agent creates a structured Music Spec.
4. Prompt Agent creates a music generation prompt.
5. Music Generator creates audio with either the local mock backend or MusicGen.
6. Audio Analyzer extracts librosa features.
7. Appreciation Agent critiques the result.
8. Revision Agent creates an optimized prompt.
9. Memory Store writes a JSON history record.

## Appreciation Mode Data Flow

1. User submits target requirement and uploads an audio file.
2. Requirement Agent normalizes the target scene.
3. Spec Agent creates a target Music Spec.
4. Prompt Agent creates the reference generation prompt for comparison.
5. Audio Analyzer extracts librosa features from the uploaded audio.
6. Appreciation Agent evaluates the audio against the target Music Spec.
7. Revision Agent creates improvement suggestions.
8. Memory Store writes a JSON history record.

## Music Generation Backend

`src/tools/music_generator.py` supports:

- `mock`: local deterministic `.wav` generation for fast classroom demos.
- `musicgen`: optional Hugging Face Transformers MusicGen integration.

If MusicGen is selected but dependencies are missing, the model download fails, or loading fails, the tool falls back to `mock` by default and records the fallback reason in `generation_result`.
