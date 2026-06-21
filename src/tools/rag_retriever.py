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
    keywords: tuple[str, ...]


SYNONYM_GROUPS: dict[str, set[str]] = {
    "cyberpunk": {
        "cyberpunk",
        "sci-fi",
        "science fiction",
        "futuristic",
        "future city",
        "neon",
        "night city",
        "赛博朋克",
        "赛博",
        "科幻",
        "霓虹",
        "城市夜景",
        "夜景",
        "未来感",
    },
    "cinematic": {
        "cinematic",
        "trailer",
        "film",
        "score",
        "opening",
        "short film",
        "影视",
        "电影",
        "配乐",
        "预告片",
        "开场",
        "短片",
    },
    "lofi": {
        "lo-fi",
        "lofi",
        "study",
        "chill",
        "cozy",
        "warm",
        "低保真",
        "学习",
        "放松",
        "温暖",
        "咖啡馆",
    },
    "ambient": {
        "ambient",
        "meditation",
        "calm",
        "peaceful",
        "space",
        "drone",
        "氛围",
        "冥想",
        "平静",
        "空间",
        "舒缓",
        "漂浮",
    },
    "pop_hook": {
        "pop",
        "hook",
        "catchy",
        "theme",
        "melody",
        "motif",
        "流行",
        "抓耳",
        "主旋律",
        "主题",
        "动机",
        "记忆点",
    },
    "edm": {
        "edm",
        "dance",
        "club",
        "house",
        "techno",
        "drop",
        "电子舞曲",
        "舞曲",
        "俱乐部",
        "律动",
        "鼓点",
        "drop",
    },
    "rock": {
        "rock",
        "band",
        "guitar",
        "drums",
        "摇滚",
        "乐队",
        "吉他",
        "鼓组",
        "热血",
    },
    "guofeng": {
        "chinese",
        "traditional",
        "guofeng",
        "oriental",
        "国风",
        "古风",
        "中国风",
        "笛子",
        "古筝",
        "二胡",
    },
    "sad_piano": {
        "sad",
        "piano",
        "emotional",
        "melancholy",
        "悲伤",
        "钢琴",
        "抒情",
        "忧郁",
        "治愈",
    },
    "tempo": {
        "tempo",
        "groove",
        "rhythm",
        "bpm",
        "tight",
        "driving",
        "节奏",
        "律动",
        "速度",
        "鼓点",
        "紧凑",
        "推进",
    },
    "energy": {
        "energy",
        "dynamics",
        "rms",
        "loudness",
        "powerful",
        "能量",
        "动态",
        "响度",
        "层次",
        "有力",
    },
    "brightness": {
        "timbre",
        "brightness",
        "spectral",
        "texture",
        "bright",
        "shimmer",
        "音色",
        "明亮",
        "清透",
        "频谱",
        "质感",
        "高频",
    },
}


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


def _extract_keywords(text: str) -> tuple[str, ...]:
    for line in text.splitlines():
        if line.lower().startswith("keywords:"):
            raw_keywords = line.split(":", 1)[1]
            return tuple(
                keyword.strip(" .,，。")
                for keyword in raw_keywords.split(",")
                if keyword.strip(" .,，。")
            )
    return ()


def _detect_concepts(text: str, base_terms: set[str]) -> dict[str, list[str]]:
    normalized = text.lower()
    concepts: dict[str, list[str]] = {}
    for concept, words in SYNONYM_GROUPS.items():
        hits: set[str] = set()
        for word in words:
            lowered = word.lower()
            word_terms = _tokens(lowered)
            if lowered in normalized or base_terms & word_terms:
                hits.add(word)
        if hits:
            concepts[concept] = sorted(hits)
    return concepts


def _expanded_terms(base_terms: set[str], concepts: dict[str, list[str]]) -> set[str]:
    expanded = set(base_terms)
    for concept in concepts:
        for word in SYNONYM_GROUPS.get(concept, set()):
            expanded.update(_tokens(word))
    return expanded


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
                        keywords=_extract_keywords("\n".join(current_lines)),
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
                keywords=_extract_keywords("\n".join(current_lines)),
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


def _chunk_score(
    query: str,
    base_terms: set[str],
    expanded_terms: set[str],
    chunk: KnowledgeChunk,
) -> tuple[float, list[str], list[str]]:
    title_terms = _tokens(chunk.title)
    keyword_terms = set()
    for keyword in chunk.keywords:
        keyword_terms.update(_tokens(keyword))
    text_terms = _tokens(chunk.text)
    chunk_terms = title_terms | keyword_terms | text_terms

    direct_overlap = base_terms & chunk_terms
    expanded_overlap = expanded_terms & chunk_terms
    title_overlap = expanded_terms & title_terms
    keyword_overlap = expanded_terms & keyword_terms

    exact_keyword_hits = [
        keyword
        for keyword in chunk.keywords
        if keyword and keyword.lower() in query.lower()
    ]

    score = (
        len(direct_overlap) * 2.0
        + len(expanded_overlap - direct_overlap) * 0.65
        + len(title_overlap) * 2.0
        + len(keyword_overlap) * 2.4
        + len(exact_keyword_hits) * 3.0
    )

    # Generation benefits from prompt/style knowledge; appreciation benefits from scoring knowledge.
    lowered_query = query.lower()
    if ("generation" in lowered_query or "生成" in query) and (
        "prompt_examples" in chunk.source or "music_styles" in chunk.source
    ):
        score += 1.0
    if ("appreciation" in lowered_query or "鉴赏" in query or "评价" in query) and (
        "scoring_guidelines" in chunk.source or "music_styles" in chunk.source
    ):
        score += 1.0

    readable_terms = list(dict.fromkeys(exact_keyword_hits))
    if not readable_terms:
        readable_terms.extend(
            term
            for term in sorted((keyword_overlap | title_overlap | direct_overlap), key=str.lower)
            if re.fullmatch(r"[a-zA-Z0-9+#-]+", term) or len(term) >= 4
        )
    return score, readable_terms[:14], exact_keyword_hits


def _fallback_chunks(query: str, chunks: tuple[KnowledgeChunk, ...], top_k: int) -> list[tuple[float, KnowledgeChunk, list[str], list[str], bool]]:
    lowered_query = query.lower()
    preferred_titles: list[str]
    if "appreciation" in lowered_query or "鉴赏" in query or "评价" in query:
        preferred_titles = ["Tempo And Groove", "Energy And Dynamics", "Timbre And Brightness"]
    else:
        preferred_titles = ["Cinematic Trailer / Film Score", "Motif And Memorability", "Pop Hook Prompt Example"]

    fallback: list[tuple[float, KnowledgeChunk, list[str], list[str], bool]] = []
    for title in preferred_titles:
        for chunk in chunks:
            if chunk.title == title:
                fallback.append((0.5, chunk, ["fallback"], [], True))
                break
        if len(fallback) >= top_k:
            break
    return fallback


def retrieve_music_context(query: str, top_k: int = 4) -> dict[str, Any]:
    query_terms = _tokens(query)
    chunks = _load_chunks()
    if not query_terms or not chunks:
        return {
            "rag_query": query,
            "rag_summary": "未形成有效检索词。",
            "rag_intent_profile": {},
            "retrieved_context": "",
            "rag_sources": [],
            "rag_matches": [],
        }

    concepts = _detect_concepts(query, query_terms)
    expanded = _expanded_terms(query_terms, concepts)

    scored: list[tuple[float, KnowledgeChunk, list[str], list[str], bool]] = []
    for chunk in chunks:
        score, matched_terms, exact_keyword_hits = _chunk_score(
            query=query,
            base_terms=query_terms,
            expanded_terms=expanded,
            chunk=chunk,
        )
        if score <= 0:
            continue
        scored.append((score, chunk, matched_terms, exact_keyword_hits, False))

    scored.sort(key=lambda item: item[0], reverse=True)
    if not scored:
        scored = _fallback_chunks(query, chunks, top_k)

    matches = [
        {
            "source": chunk.source,
            "title": chunk.title,
            "score": round(score, 3),
            "matched_terms": matched_terms,
            "matched_keywords": exact_keyword_hits,
            "fallback": fallback,
            "reason": (
                "兜底补充通用音乐知识"
                if fallback
                else f"匹配关键词：{', '.join(matched_terms[:8]) or '语义扩展'}"
            ),
            "text": chunk.text,
        }
        for score, chunk, matched_terms, exact_keyword_hits, fallback in scored[:top_k]
    ]

    context = "\n\n".join(
        f"[{item['source']}#{item['title']}]\n{item['text']}" for item in matches
    )
    sources = [f"{item['source']}#{item['title']}" for item in matches]
    titles = "、".join(item["title"] for item in matches[:3])
    summary = (
        f"命中 {len(matches)} 个知识片段：{titles}。"
        if matches
        else "未检索到明显相关的音乐知识。"
    )
    if concepts:
        summary += f" 识别意图：{', '.join(concepts.keys())}。"

    return {
        "rag_query": query,
        "rag_summary": summary,
        "rag_intent_profile": concepts,
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
