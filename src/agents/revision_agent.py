from src.graph.state import MusicAgentState


STYLE_ZH = {
    "cinematic": "影视配乐",
    "electronic": "电子音乐",
    "cinematic electronic": "影视电子音乐",
    "jazz": "爵士",
    "classical": "古典",
    "pop": "流行",
    "lofi": "低保真氛围音乐",
}

MOOD_ZH = {
    "uplifting": "明亮积极",
    "dark": "阴暗紧张",
    "calm": "平静舒缓",
    "energetic": "紧凑有推进感",
    "mysterious": "神秘",
    "focused": "聚焦克制",
}

INSTRUMENT_ZH = {
    "synth lead": "合成器主奏",
    "warm pad": "温暖铺底",
    "bass": "低音",
    "light percussion": "轻打击乐",
    "bright synth lead": "明亮合成器主奏",
    "shimmer pad": "闪亮铺底",
    "sub bass": "次低音",
    "crisp percussion": "清脆打击乐",
    "punchy synth lead": "有冲击力的合成器主奏",
    "short pluck arpeggio": "短促拨奏琶音",
    "tight bass": "紧实低音",
    "driving percussion": "推进型鼓组",
    "lead hook layer": "主旋律叠加层",
    "dark synth lead": "暗色合成器主奏",
    "industrial percussion": "工业打击乐",
    "ambient pad": "空间氛围铺底",
    "warm keys": "温暖键盘",
    "vinyl texture": "低保真颗粒质感",
    "mellow bass": "柔和低音",
    "soft drums": "轻柔鼓组",
    "slow pad": "缓慢铺底",
    "soft drone": "柔和持续音",
    "gentle low bass": "轻柔低频",
    "long reverb texture": "长混响质感",
}

STRUCTURE_ZH = {
    "intro motif": "动机引入",
    "main groove": "主体律动",
    "variation": "变化段",
    "short ending": "短收束",
    "clear motif intro": "清晰动机引入",
    "brighter groove": "更明亮的主体律动",
    "lifted variation": "上扬变化段",
    "resolved ending": "稳定收束",
    "short motif intro": "短前奏动机",
    "tight main groove": "紧凑主体律动",
    "rhythmic break": "节奏断点",
    "impact ending": "有冲击力的结尾",
    "memorable hook intro": "可记忆主题引入",
    "hook repeat": "主题重复",
    "contrast variation": "对比变化段",
    "hook ending": "主题收束",
    "neon atmosphere intro": "霓虹氛围引入",
    "bass pulse groove": "低频脉冲律动",
    "contrast tension": "张力对比段",
    "soft loop intro": "柔和循环引入",
    "stable groove": "稳定律动",
    "gentle variation": "轻柔变化段",
    "loopable ending": "可循环收束",
    "texture fade in": "质感淡入",
    "slow evolution": "缓慢演进",
    "wide space": "宽阔空间段",
    "soft fade out": "柔和淡出",
}


def _intent_directives(latest: str) -> list[str]:
    directives: list[str] = []
    if "更明亮" in latest or "明亮" in latest:
        directives.append("提高主奏合成器的明亮度，加入清透的中高频层")
    if "更紧凑" in latest or "紧凑" in latest:
        directives.append("缩短前奏，让主体律动更早进入")
    if "主旋律" in latest or "hook" in latest.lower() or "抓耳" in latest:
        directives.append("写出可重复的两小节主题，并把主旋律放在前景")
    if "更暗" in latest or "黑暗" in latest or "压抑" in latest:
        directives.append("使用更暗的和声、低音区铺底，并减少高频闪光感")
    if "舒缓" in latest or "柔和" in latest or "慢一点" in latest:
        directives.append("降低节奏密度，使用更柔和的起音")
    return directives


def _rag_directives(context: str) -> list[str]:
    directives: list[str] = []
    lowered = context.lower()
    if "cyberpunk" in lowered or "赛博朋克" in context:
        directives.append("保留暗色合成器、低频脉冲和空间混响")
    if "lo-fi" in lowered or "lofi" in lowered or "低保真" in context:
        directives.append("保持温暖颗粒感和稳定低疲劳律动")
    if "ambient" in lowered or "冥想" in context or "氛围" in context:
        directives.append("减少瞬态密度，突出空间延展")
    if "hook" in lowered or "主旋律" in context:
        directives.append("让两小节主题保持前景可记忆")
    return directives


def _dedupe(items: list[str]) -> list[str]:
    seen: set[str] = set()
    unique: list[str] = []
    for item in items:
        normalized = item.strip()
        if normalized and normalized not in seen:
            unique.append(normalized)
            seen.add(normalized)
    return unique


def _translate_list(items: list[str], mapping: dict[str, str]) -> list[str]:
    return [mapping.get(item, item) for item in items]


def _zh_key(key: str) -> str:
    if not key:
        return "C大调"
    return key.replace(" major", "大调").replace(" minor", "小调")


def _compact_list(items: list[str], limit: int = 4) -> str:
    selected = [item.rstrip("。；;,.， ") for item in _dedupe(items)[:limit]]
    return "、".join(selected) if selected else "保持当前核心方向"


def _find_issue(issues: list[str], keyword: str) -> str:
    for issue in issues:
        if keyword in issue:
            return issue
    return ""


def _is_optimized_prompt(text: str) -> bool:
    return "生成约" in text and "重点：" in text


def _focus_items(
    latest: str,
    issues: list[str],
    directives: list[str],
    resolved_categories: set[str],
    optimized_prompt_used: bool,
) -> list[str]:
    focus: list[str] = []

    bright_requested = "更明亮" in latest or "明亮" in latest
    tight_requested = "更紧凑" in latest or "紧凑" in latest
    hook_requested = "主旋律" in latest or "hook" in latest.lower() or "抓耳" in latest

    if bright_requested and not optimized_prompt_used and "brightness" not in resolved_categories:
        focus.append("增强主奏清透感。")
    elif "brightness" not in resolved_categories:
        brightness_issue = _find_issue(issues, "明亮度")
        if brightness_issue:
            if "不足" in brightness_issue:
                focus.append("增强主奏高频与清透感。")
            else:
                focus.append("收敛高频亮度，增加温暖中频。")

    if tight_requested and not optimized_prompt_used and "tempo" not in resolved_categories:
        focus.append("缩短前奏，提前进入主体律动。")
    elif "tempo" not in resolved_categories:
        tempo_issue = _find_issue(issues, "节奏")
        if tempo_issue:
            if "偏慢" in tempo_issue:
                focus.append("加强鼓点推进，让目标速度更清晰。")
            else:
                focus.append("降低律动密度，让节奏更稳定。")

    if hook_requested and not optimized_prompt_used and "melody" not in resolved_categories:
        focus.append("突出两小节主旋律记忆点。")
    elif "melody" not in resolved_categories:
        melody_issue = _find_issue(issues, "主旋律")
        if melody_issue:
            focus.append("强化两小节主题记忆点。")

    energy_issue = _find_issue(issues, "能量")
    if energy_issue and "energy" not in resolved_categories:
        focus.append("控制能量层次。")

    onset_issue = _find_issue(issues, "瞬态")
    if onset_issue and "onset" not in resolved_categories:
        focus.append("减少打击瞬态密度。")

    return _dedupe(focus or directives or issues[:4])


def generate_revision(state: MusicAgentState) -> MusicAgentState:
    appreciation = state.get("appreciation_result", {})
    spec = state.get("music_spec", {})
    latest = state.get("latest_user_message", "")
    rag_context = state.get("retrieved_context", "")
    issues = appreciation.get("issues", [])
    resolved_categories = set(appreciation.get("resolved_categories", []))
    optimized_prompt_used = bool(appreciation.get("optimized_prompt_used"))
    instruments = _translate_list(spec.get("instruments", []), INSTRUMENT_ZH)
    structure = _translate_list(spec.get("structure", []), STRUCTURE_ZH)
    directives = _dedupe(_intent_directives(latest) + _rag_directives(rag_context))
    issue_focus = _focus_items(
        latest,
        issues,
        directives,
        resolved_categories,
        optimized_prompt_used,
    )

    style = STYLE_ZH.get(spec.get("style", ""), spec.get("style", "音乐"))
    mood = MOOD_ZH.get(spec.get("mood", ""), spec.get("mood", "聚焦克制"))
    tempo = spec.get("tempo_bpm", 120)
    key = _zh_key(str(spec.get("key", "C major")))
    duration = spec.get("duration_seconds", 12)

    target = (
        f"{style} / {mood} / 每分钟 {tempo} 拍"
    )
    if issues:
        revision_suggestion = (
            f"下一轮围绕 {target} 迭代："
            + "；".join(issue_focus)
        )
    else:
        revision_suggestion = (
            f"保留 {target} 的核心方向，并在中段加入一次更明确的对比。"
        )

    if latest:
        if _is_optimized_prompt(latest):
            revision_suggestion += " 用户最新意图：已采用上一轮优化 Prompt。"
        else:
            revision_suggestion += f" 用户最新意图：{latest}"

    optimization_focus = issue_focus
    optimized_prompt = (
        f"生成约{duration}秒{style}：{key}，{tempo} BPM，情绪{mood}。"
        f"结构：{_compact_list(structure, limit=3)}。"
        f"音色：{_compact_list(instruments, limit=4)}。"
        f"重点：{_compact_list(optimization_focus, limit=3)}。"
    )

    return {
        "revision_suggestion": revision_suggestion,
        "optimized_prompt": optimized_prompt,
    }
