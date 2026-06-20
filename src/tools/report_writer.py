from __future__ import annotations

from pathlib import Path

from src.graph.state import MusicAgentState


def write_markdown_report(state: MusicAgentState, output_path: str | Path) -> Path:
    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)

    content = f"""# MusicAgent Studio Report

## User Requirement

{state.get("user_requirement", "")}

## Run Mode

{state.get("run_mode", "")}

## Generation Backend

{state.get("generation_result", {}).get("used_backend", state.get("generator_backend", ""))}

## Music Spec

```json
{state.get("music_spec", {})}
```

## Generation Prompt

{state.get("generation_prompt", "")}

## Audio Path

{state.get("audio_path", "")}

## Generation Result

```json
{state.get("generation_result", {})}
```

## Audio Features

```json
{state.get("audio_features", {})}
```

## Appreciation Result

```json
{state.get("appreciation_result", {})}
```

## Revision Suggestion

{state.get("revision_suggestion", "")}
"""
    path.write_text(content, encoding="utf-8")
    return path
