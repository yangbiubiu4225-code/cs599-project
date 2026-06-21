from __future__ import annotations

import re
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path
from typing import Any

from src.graph.state import MusicAgentState


KNOWLEDGE_DIR = Path(__file__).resolve().parents[1] / "knowledge"
WORD_RE = re.compile(r"[a-zA-Z0-9+#-]+|[\u4e00-\u9fff]{2,}")


@dataclass(frozen=True)
class KnowledgeChunk:
    source: str
    title: str
    text: str


def _tokens(text: str) -> set[str]:
    normalized = text.lower()
    terms: set[str] = set()
    for token in WORD_RE.findall(normalized):
        token = token.strip()
        if len(token) < 2:
            continue
        terms.add(token)
        if re.fullmatch(r"[\u4e00-\u9fff]+", token):
            for size in (2, 3, 4):
                for index in range(0, max(0, len(token) - size + 1)):
                    terms.add(token[index : index + size])
    return terms


def _split_markdown(path: Path) -> list[KnowledgeChunk]:
    chunks: list[KnowledgeChunk] = []
    current_title = path.stem
    current_lines: list[str] = []

    for line in path.read_text(encoding="utf-8").splitlines():
        if line.startswith("## "):
            if current_lines:
                chunks.append(
                    KnowledgeChunk(
                        source=str(path.relative_to(KNOWLEDGE_DIR.parent.parent)),
                        title=current_title,
                        text="\n".join(current_lines).strip(),
                    )
                )
            current_title = line.lstrip("#").strip()
            current_lines = [line]
        else:
            current_lines.append(line)

    if current_lines:
        chunks.append(
            KnowledgeChunk(
                source=str(path.relative_to(KNOWLEDGE_DIR.parent.parent)),
                title=current_title,
                text="\n".join(current_lines).strip(),
            )
        )

    return [chunk for chunk in chunks if chunk.text]


@lru_cache(maxsize=1)
def _load_chunks() -> tuple[KnowledgeChunk, ...]:
    if not KNOWLEDGE_DIR.exists():
        return ()

    chunks: list[KnowledgeChunk] = []
    for path in sorted(KNOWLEDGE_DIR.glob("*.md")):
        chunks.extend(_split_markdown(path))
    return tuple(chunks)


def retrieve_music_context(query: str, top_k: int = 3) -> dict[str, Any]:
    query_terms = _tokens(query)
    chunks = _load_chunks()
    if not query_terms or not chunks:
        return {
            "retrieved_context": "",
            "rag_sources": [],
            "rag_matches": [],
        }

    scored: list[tuple[float, KnowledgeChunk]] = []
    for chunk in chunks:
        haystack = f"{chunk.title}\n{chunk.text}"
        chunk_terms = _tokens(haystack)
        overlap = query_terms & chunk_terms
        if not overlap:
            continue
        title_bonus = 1.5 if query_terms & _tokens(chunk.title) else 0.0
        score = len(overlap) + title_bonus
        scored.append((score, chunk))

    scored.sort(key=lambda item: item[0], reverse=True)
    matches = [
        {
            "source": chunk.source,
            "title": chunk.title,
            "score": round(score, 3),
            "text": chunk.text,
        }
        for score, chunk in scored[:top_k]
    ]

    context = "\n\n".join(
        f"[{item['source']}#{item['title']}]\n{item['text']}" for item in matches
    )
    sources = [f"{item['source']}#{item['title']}" for item in matches]

    return {
        "retrieved_context": context,
        "rag_sources": sources,
        "rag_matches": matches,
    }


def retrieve_music_context_for_state(state: MusicAgentState) -> MusicAgentState:
    query = "\n".join(
        [
            state.get("user_requirement", ""),
            state.get("latest_user_message", ""),
            state.get("run_mode", ""),
        ]
    )
    return retrieve_music_context(query)
