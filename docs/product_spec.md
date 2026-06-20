# MusicAgent Studio Product Spec

## Goal

MusicAgent Studio is a course demo for an AI music generation and appreciation agent. It supports two operating modes: AI music generation and AI music appreciation. It turns a user requirement into a structured music specification, a generation prompt, audio features, appreciation results, and revision suggestions.

## Target Users

- CS599 instructors and classmates reviewing the final project.
- Students exploring AI-assisted music creation workflows.
- Developers who want a small LangGraph example with audio analysis.

## Core Modes

### AI Music Generation Mode

The user enters a music requirement. The system generates a Music Spec, builds a generation prompt, creates audio, analyzes the audio, appreciates the result, generates revision suggestions, and saves history.

The music generation backend can be either:

- Local mock generation for reliable demos.
- Optional MusicGen generation through Hugging Face Transformers.

### AI Music Appreciation Mode

The user enters a target music requirement and uploads an audio file. The system skips the music generation node, analyzes the uploaded audio, evaluates it against the inferred Music Spec, generates suggestions, and saves history.

## Shared Modules

Both modes reuse:

- Audio Analyzer Tool
- Appreciation Agent
- Revision Agent
- Memory Store Tool

This design keeps the workflow modular and makes it easy to replace only the music generation backend later.

## Main Outputs

- Music Spec
- Generation Prompt
- Audio playback
- Audio features
- Appreciation result
- Revision suggestion
- History ID

## Non-Goals

- This version does not provide multi-track editing or DAW integration.
- This version does not require API keys for the local mock path.
- MusicGen is optional because it requires heavier local dependencies.
