import re

from src.graph.state import MusicAgentState


STYLE_KEYWORDS = {
    "cinematic": ["cinematic", "film", "trailer", "score", "short film", "电影", "影视", "配乐", "开场"],
    "electronic": ["electronic", "synth", "edm", "techno", "ambient", "电子", "合成器", "赛博"],
    "jazz": ["jazz", "swing", "blue note", "爵士", "摇摆"],
    "classical": ["classical", "orchestral", "piano", "strings", "古典", "管弦", "钢琴", "弦乐"],
    "pop": ["pop", "catchy", "hook", "radio", "流行", "抓耳", "主旋律"],
    "lofi": ["lofi", "lo-fi", "chill", "study", "低保真", "学习", "放松"],
}

MOOD_KEYWORDS = {
    "uplifting": ["uplifting", "hopeful", "bright", "happy", "明亮", "希望", "积极", "轻快"],
    "dark": ["dark", "tense", "noir", "sad", "黑暗", "紧张", "压抑", "阴暗"],
    "calm": ["calm", "peaceful", "ambient", "soft", "平静", "安静", "柔和", "舒缓"],
    "energetic": ["energetic", "driving", "powerful", "dance", "有力", "动感", "推进", "紧凑"],
    "mysterious": ["mysterious", "dream", "space", "unknown", "神秘", "梦幻", "太空", "未知"],
}

BRIGHT_WORDS = ["更明亮", "明亮", "清亮", "通透", "bright", "brighter"]
TIGHT_WORDS = ["更紧凑", "紧凑", "更快", "加快", "推进", "driving", "faster", "tighter"]
DARK_WORDS = ["更暗", "黑暗", "阴暗", "压抑", "dark", "darker"]
CALM_WORDS = ["更平静", "舒缓", "柔和", "慢一点", "放松", "calmer", "softer"]
HOOK_WORDS = ["主旋律", "旋律更明显", "更抓耳", "hook", "catchy", "memorable"]
GENERIC_REVISION_WORDS = [
    "继续优化",
    "再优化",
    "再改",
    "改一下",
    "换一版",
    "重新来",
    "再来一版",
    "继续改",
    "revise",
    "another version",
]


def _match_keyword(text: str, keyword_map: dict[str, list[str]], default: str) -> str:
    lowered = text.lower()
    for label, keywords in keyword_map.items():
        if any(keyword in lowered for keyword in keywords):
            return label
    return default


def _has_any(text: str, keywords: list[str]) -> bool:
    lowered = text.lower()
    return any(keyword.lower() in lowered for keyword in keywords)


def _base_tempo(style: str, mood: str) -> int:
    tempo_bpm = 128 if style in {"electronic", "pop"} else 96
    if mood == "calm":
        tempo_bpm = 78
    elif mood == "energetic":
        tempo_bpm = 140
    return tempo_bpm


def _parse_duration(text: str) -> int | None:
    match = re.search(r"(?:约|时长[:：]?\s*)?(\d{1,2})\s*秒", text)
    if not match:
        return None
    return max(1, min(int(match.group(1)), 30))


def _parse_tempo(text: str) -> int | None:
    match = re.search(r"(\d{2,3})\s*(?:BPM|bpm|拍)", text)
    if not match:
        return None
    return max(50, min(int(match.group(1)), 180))


def _parse_key(text: str) -> str | None:
    match = re.search(r"\b([A-G])\s*(major|minor)\b", text, re.IGNORECASE)
    if match:
        root = match.group(1).upper()
        mode = match.group(2).lower()
        return f"{root} {mode}"

    match = re.search(r"([A-G])\s*(大调|小调)", text, re.IGNORECASE)
    if match:
        root = match.group(1).upper()
        mode = "major" if match.group(2) == "大调" else "minor"
        return f"{root} {mode}"

    return None


def generate_music_spec(state: MusicAgentState) -> MusicAgentState:
    requirement = state.get("user_requirement", "")
    latest = state.get("latest_user_message", "")
    intent_text = f"{requirement}\n{latest}"

    style = _match_keyword(intent_text, STYLE_KEYWORDS, "cinematic electronic")
    mood = _match_keyword(intent_text, MOOD_KEYWORDS, "focused")

    # In multi-turn mode, the latest user message should have more weight than old context.
    if _has_any(latest, BRIGHT_WORDS):
        mood = "uplifting"
    elif _has_any(latest, DARK_WORDS):
        mood = "dark"
    elif _has_any(latest, CALM_WORDS):
        mood = "calm"
    elif _has_any(latest, TIGHT_WORDS):
        mood = "energetic"
    elif _has_any(latest, GENERIC_REVISION_WORDS):
        if "明亮度不足" in requirement:
            mood = "uplifting"
        elif "节奏偏慢" in requirement or "起音不够明确" in requirement:
            mood = "energetic"
        elif "能量偏满" in requirement or "瞬态过密" in requirement:
            mood = "focused"

    tempo_bpm = _base_tempo(style, mood)
    if _has_any(latest, TIGHT_WORDS):
        tempo_bpm = min(160, tempo_bpm + 16)
    if _has_any(latest, CALM_WORDS):
        tempo_bpm = max(64, tempo_bpm - 18)
    if _has_any(latest, GENERIC_REVISION_WORDS):
        if "节奏偏慢" in requirement:
            tempo_bpm = min(160, tempo_bpm + 12)
        if "瞬态过密" in requirement:
            tempo_bpm = max(72, tempo_bpm - 8)
    parsed_tempo = _parse_tempo(latest)
    if parsed_tempo:
        tempo_bpm = parsed_tempo

    instruments = ["synth lead", "warm pad", "bass", "light percussion"]
    structure = ["intro motif", "main groove", "variation", "short ending"]
    if _has_any(latest, BRIGHT_WORDS):
        instruments = ["bright synth lead", "shimmer pad", "sub bass", "crisp percussion"]
        structure = ["clear motif intro", "brighter groove", "lifted variation", "resolved ending"]
    if _has_any(latest, TIGHT_WORDS):
        instruments = ["punchy synth lead", "short pluck arpeggio", "tight bass", "driving percussion"]
        structure = ["short motif intro", "tight main groove", "rhythmic break", "impact ending"]
    if _has_any(latest, HOOK_WORDS):
        structure = ["memorable hook intro", "hook repeat", "contrast variation", "hook ending"]
        if "lead hook layer" not in instruments:
            instruments.append("lead hook layer")
    if _has_any(latest, GENERIC_REVISION_WORDS):
        if "明亮度不足" in requirement:
            instruments = ["bright synth lead", "shimmer pad", "sub bass", "crisp percussion"]
        if "能量偏满" in requirement or "瞬态过密" in requirement:
            structure = ["short motif intro", "main groove", "contrast variation", "resolved ending"]
            if "light percussion" not in instruments:
                instruments[-1:] = ["light percussion"]

    key = "A minor" if mood in {"dark", "mysterious"} else "C major"
    if _has_any(latest, BRIGHT_WORDS):
        key = "D major"
    elif _has_any(latest, DARK_WORDS):
        key = "D minor"
    elif _has_any(latest, GENERIC_REVISION_WORDS) and "明亮度不足" in requirement:
        key = "D major"
    parsed_key = _parse_key(latest)
    if parsed_key:
        key = parsed_key

    duration_seconds = _parse_duration(latest) or 12

    music_spec = {
        "style": style,
        "mood": mood,
        "tempo_bpm": tempo_bpm,
        "key": key,
        "duration_seconds": duration_seconds,
        "structure": structure,
        "instruments": instruments,
        "reference_requirement": requirement,
        "latest_user_message": latest,
    }

    return {"music_spec": music_spec}
