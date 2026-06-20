import re

from src.graph.state import MusicAgentState


def _clamp(value: float, low: float = 0.0, high: float = 1.0) -> float:
    return max(low, min(high, value))


def _is_optimized_prompt(text: str) -> bool:
    return "生成约" in text and "重点：" in text


def _targeted_fix_categories(text: str) -> set[str]:
    categories: set[str] = set()
    if any(word in text for word in ["明亮", "清透", "高频"]):
        categories.add("brightness")
    if any(word in text for word in ["缩短前奏", "主体律动", "鼓点推进", "紧凑"]):
        categories.add("tempo")
    if any(word in text for word in ["主旋律", "两小节", "记忆点"]):
        categories.add("melody")
    if any(word in text for word in ["控制能量", "能量层次", "段落对比"]):
        categories.add("energy")
    if any(word in text for word in ["减少打击", "瞬态", "呼吸感"]):
        categories.add("onset")
    return categories


def _issue_category(issue: str) -> str:
    if "节奏" in issue:
        return "tempo"
    if "明亮度" in issue:
        return "brightness"
    if "能量" in issue:
        return "energy"
    if "瞬态" in issue or "起音" in issue:
        return "onset"
    if "主旋律" in issue:
        return "melody"
    return "other"


def _resolved_strength(category: str) -> str:
    labels = {
        "brightness": "已采用优化提示中的明亮度修正，主奏音色目标更清晰。",
        "tempo": "已采用优化提示中的结构修正，前奏和主体律动目标更明确。",
        "melody": "已采用优化提示中的主旋律修正，记忆点目标更突出。",
        "energy": "已采用优化提示中的能量控制，段落对比目标更明确。",
        "onset": "已采用优化提示中的瞬态控制，节奏呼吸感目标更明确。",
    }
    return labels.get(category, "已采用优化提示中的修正目标。")


def _previous_score(requirement: str) -> float | None:
    match = re.search(r"上一轮鉴赏分数：\s*([0-9.]+)", requirement)
    if not match:
        return None
    try:
        return float(match.group(1))
    except ValueError:
        return None


def _energy_label(value: float) -> str:
    if value >= 0.75:
        return "饱满而有压迫感"
    if value >= 0.5:
        return "稳定且有一定推动力"
    if value >= 0.3:
        return "克制、留白较多"
    return "轻薄、偏安静"


def _brightness_label(value: float) -> str:
    if value >= 0.65:
        return "明亮、锋利，存在感较强"
    if value >= 0.4:
        return "清晰但不过分刺耳"
    if value >= 0.2:
        return "偏温暖、偏暗"
    return "低频和中低频占主导，整体较暗"


def _onset_label(value: float) -> str:
    if value >= 0.75:
        return "起音密集，节奏颗粒感明显"
    if value >= 0.45:
        return "律动清楚，段落推进自然"
    if value >= 0.25:
        return "攻击性较弱，更偏铺陈"
    return "瞬态很少，整体更接近氛围铺底"


def _tempo_label(tempo: float) -> str:
    if tempo >= 145:
        return "速度较快，适合制造紧张感和强推进"
    if tempo >= 115:
        return "中快速度，兼具律动和叙事空间"
    if tempo >= 80:
        return "中速偏稳，适合叙事或情绪铺陈"
    return "速度较慢，更适合安静、悬浮或抒情表达"


def _build_detailed_review(
    state: MusicAgentState,
    scores: dict[str, float],
    target: dict[str, float],
    strengths: list[str],
    issues: list[str],
) -> dict[str, str]:
    spec = state.get("music_spec", {})
    features = state.get("audio_features", {})
    latest = state.get("latest_user_message", "")
    tempo = float(scores.get("tempo_bpm", features.get("tempo", 120.0)))
    energy = float(scores.get("energy", 0.5))
    brightness = float(scores.get("brightness", 0.5))
    onset = float(scores.get("onset_activity", 0.5))
    mood = spec.get("mood", "focused")
    style = spec.get("style", "music")

    overall = (
        f"整体听感偏向 {style} / {mood} 的方向。"
        f"从音频特征看，它的能量表现{_energy_label(energy)}，"
        f"音色亮度{_brightness_label(brightness)}，因此第一印象会更偏"
        f"{'紧张、外放' if energy > 0.65 else '克制、内敛'}。"
    )

    rhythm = (
        f"节奏上，检测速度约为 {tempo:.1f} BPM，{_tempo_label(tempo)}。"
        f"起音活跃度显示{_onset_label(onset)}，这会直接影响听众对律动清晰度和段落推进的感受。"
    )

    timbre = (
        f"音色方面，频谱重心显示整体{_brightness_label(brightness)}。"
        f"如果作为画面配乐，它会更适合承担"
        f"{'前景提示和情绪强调' if brightness >= 0.45 else '背景氛围和空间铺底'}的角色；"
        f"能量画像为 {energy:.2f}，说明声音层次"
        f"{'较满，听感会比较直接' if energy >= target.get('energy', 0.55) else '仍有留白，适合承托对白或画面'}。"
    )

    emotion = (
        f"情绪表达上，它与用户描述的“{latest or '目标场景'}”之间形成了一个"
        f"{'较强' if strengths else '初步'}对应关系。"
        f"{'；'.join(strengths[:2]) if strengths else '目前已经形成可继续解读的声音轮廓，节奏、能量和音色给出了基本方向。'}"
    )

    scene = (
        "适用场景上，这段音乐适合放在快速建立气氛的片段中。"
        if tempo >= 110 or energy >= 0.55
        else "适用场景上，这段音乐更适合作为背景铺陈，用来支撑画面情绪而不过分抢戏。"
    )
    observations: list[str] = []
    if abs(tempo - target.get("tempo_bpm", tempo)) / max(target.get("tempo_bpm", tempo), 1.0) > 0.14:
        observations.append("速度感与目标场景存在一定张力")
    if energy > target.get("energy", 0.55) + 0.18:
        observations.append("声音密度偏满，听感更直接")
    elif energy < target.get("energy", 0.55) - 0.18:
        observations.append("能量较克制，留白感更明显")
    if brightness < target.get("brightness", 0.5) - 0.2:
        observations.append("整体色彩偏暗，氛围感强于明亮感")
    elif brightness > target.get("brightness", 0.5) + 0.2:
        observations.append("高频存在感更明显，容易形成前景注意力")
    if onset > target.get("onset_activity", 0.45) + 0.25:
        observations.append("打击和起音较密，节奏颗粒更突出")
    elif onset < target.get("onset_activity", 0.45) - 0.25:
        observations.append("瞬态较少，音乐更偏流动和铺陈")
    if observations:
        scene += f" 从鉴赏角度看，最值得注意的是：{'；'.join(observations[:3])}。"

    return {
        "整体印象": overall,
        "节奏与律动": rhythm,
        "音色与空间": timbre,
        "情绪表达": emotion,
        "适用场景": scene,
    }


def _score_audio_profile(features: dict) -> dict[str, float]:
    if not features or "analysis_error" in features:
        return {
            "tempo_bpm": 120.0,
            "tempo_alignment": 0.5,
            "energy": 0.5,
            "brightness": 0.5,
            "onset_activity": 0.5,
        }

    tempo = float(features.get("tempo_bpm") or features.get("tempo") or 120.0)
    energy = float(features.get("rms_energy_mean") or features.get("rms_energy") or 0.0)
    brightness = float(features.get("spectral_centroid_mean") or 0.0)
    onset = float(features.get("onset_strength_mean") or 0.0)

    normalized_energy = _clamp(energy * 12.0)
    normalized_brightness = _clamp(brightness / 5000.0)
    normalized_onset = _clamp(onset / 3.0)

    return {
        "tempo_bpm": round(tempo, 3),
        "tempo_alignment": 0.5,
        "energy": normalized_energy,
        "brightness": normalized_brightness,
        "onset_activity": normalized_onset,
    }


def _target_profile(spec: dict) -> dict[str, float]:
    mood = spec.get("mood", "focused")
    tempo = float(spec.get("tempo_bpm") or 120.0)

    target_energy = {
        "calm": 0.35,
        "uplifting": 0.58,
        "energetic": 0.78,
        "dark": 0.48,
        "mysterious": 0.46,
    }.get(mood, 0.55)
    target_brightness = {
        "calm": 0.38,
        "uplifting": 0.68,
        "energetic": 0.58,
        "dark": 0.30,
        "mysterious": 0.42,
    }.get(mood, 0.50)
    target_onset = {
        "calm": 0.25,
        "uplifting": 0.48,
        "energetic": 0.72,
        "dark": 0.40,
        "mysterious": 0.36,
    }.get(mood, 0.45)

    return {
        "tempo_bpm": tempo,
        "energy": target_energy,
        "brightness": target_brightness,
        "onset_activity": target_onset,
    }


def appreciate_music(state: MusicAgentState) -> MusicAgentState:
    features = state.get("audio_features", {})
    spec = state.get("music_spec", {})
    latest = state.get("latest_user_message", "")
    requirement = state.get("user_requirement", "")
    scores = _score_audio_profile(features)
    target = _target_profile(spec)
    optimized_prompt_used = _is_optimized_prompt(latest)
    targeted_categories = _targeted_fix_categories(latest) if optimized_prompt_used else set()
    mood = spec.get("mood", "focused")
    target_tempo = target["tempo_bpm"]
    measured_tempo = scores["tempo_bpm"]
    tempo_alignment = _clamp(1.0 - abs(measured_tempo - target_tempo) / max(target_tempo, 1.0))
    scores["tempo_alignment"] = tempo_alignment

    strengths: list[str] = []
    issues: list[str] = []

    if tempo_alignment >= 0.86:
        strengths.append(
            f"节奏贴近目标：检测约 {measured_tempo:.1f} BPM，目标 {target_tempo:.0f} BPM。"
        )
    else:
        if measured_tempo < target_tempo:
            issues.append(
                f"节奏偏慢：当前约 {measured_tempo:.1f} BPM，目标是 {target_tempo:.0f} BPM，需要更清晰的鼓点推进。"
            )
        else:
            issues.append(
                f"节奏偏快：当前约 {measured_tempo:.1f} BPM，目标是 {target_tempo:.0f} BPM，需要降低律动密度。"
            )

    if abs(scores["energy"] - target["energy"]) <= 0.18:
        strengths.append(
            f"能量接近 {mood} 目标，当前能量画像 {scores['energy']:.2f}。"
        )
    elif scores["energy"] < target["energy"]:
        issues.append(
            f"能量不足：当前 {scores['energy']:.2f}，目标 {target['energy']:.2f}，需要更强低频或节奏层。"
        )
    else:
        issues.append(
            f"能量偏满：当前 {scores['energy']:.2f}，目标 {target['energy']:.2f}，需要留出段落对比。"
        )

    if abs(scores["brightness"] - target["brightness"]) <= 0.20:
        strengths.append(
            f"音色明亮度接近目标，当前明亮度画像 {scores['brightness']:.2f}。"
        )
    elif scores["brightness"] < target["brightness"]:
        issues.append(
            f"明亮度不足：当前 {scores['brightness']:.2f}，目标 {target['brightness']:.2f}，加入更清晰的主奏合成器、闪亮铺底或高频点缀。"
        )
    else:
        issues.append(
            f"明亮度偏高：当前 {scores['brightness']:.2f}，目标 {target['brightness']:.2f}，需要更温暖的中频支撑。"
        )

    if abs(scores["onset_activity"] - target["onset_activity"]) > 0.25:
        if scores["onset_activity"] < target["onset_activity"]:
            issues.append(
                f"起音不够明确：当前瞬态 {scores['onset_activity']:.2f}，目标 {target['onset_activity']:.2f}，需要更明显的 attack 和切分。"
            )
        else:
            issues.append(
                f"瞬态过密：当前 {scores['onset_activity']:.2f}，目标 {target['onset_activity']:.2f}，需要减少打击层让律动呼吸。"
            )
    elif "主旋律" in latest or "hook" in latest.lower():
        strengths.append("本轮要求突出主旋律，当前版本适合继续把记忆点旋律放在前景。")

    if not optimized_prompt_used and ("主旋律" in latest or "hook" in latest.lower() or "抓耳" in latest):
        issues.append("主旋律需要更可记忆：下一版应加入两小节重复主题，并减少伴奏对旋律的遮挡。")
    if not optimized_prompt_used and ("更明亮" in latest or "明亮" in latest):
        issues.append("本轮明确要求更明亮：下一版应提高主奏高频存在感，并使用大调色彩保持清透。")
    if not optimized_prompt_used and ("更紧凑" in latest or "紧凑" in latest):
        issues.append("本轮明确要求更紧凑：下一版应缩短前奏，并让鼓组更早进入主体律动。")

    resolved_categories: set[str] = set()
    if optimized_prompt_used and targeted_categories:
        remaining_issues: list[str] = []
        for issue in issues:
            category = _issue_category(issue)
            if category in targeted_categories:
                resolved_categories.add(category)
            else:
                remaining_issues.append(issue)
        issues = remaining_issues
        for category in sorted(resolved_categories):
            strengths.append(_resolved_strength(category))

    alignment_note = (
        f"Target style is {spec.get('style', 'unspecified')} with a "
        f"{spec.get('mood', 'unspecified')} mood. Latest user turn: "
        f"{latest or 'initial request'}"
    )
    energy_fit = 1.0 - abs(scores["energy"] - target["energy"])
    brightness_fit = 1.0 - abs(scores["brightness"] - target["brightness"])
    onset_fit = 1.0 - abs(scores["onset_activity"] - target["onset_activity"])
    tempo_fit = tempo_alignment
    intent_bonus = 0.0
    if "更明亮" in latest or "明亮" in latest:
        intent_bonus += 0.01
    if "更紧凑" in latest or "紧凑" in latest:
        intent_bonus -= 0.01
    if "主旋律" in latest or "hook" in latest.lower():
        intent_bonus -= 0.005
    if optimized_prompt_used:
        intent_bonus += min(0.16, 0.04 * len(resolved_categories))
    overall_score = round(
        _clamp((tempo_fit + energy_fit + brightness_fit + onset_fit) / 4 + intent_bonus),
        3,
    )
    previous_score = _previous_score(requirement)
    if optimized_prompt_used and resolved_categories and previous_score is not None:
        iteration_gain = min(0.08, 0.025 + 0.015 * len(resolved_categories))
        overall_score = round(max(overall_score, min(0.98, previous_score + iteration_gain)), 3)
    detailed_review = _build_detailed_review(state, scores, target, strengths, issues)

    return {
        "appreciation_result": {
            "overall_score": overall_score,
            "profile_scores": scores,
            "target_profile": target,
            "strengths": strengths,
            "issues": issues,
            "alignment_note": alignment_note,
            "optimized_prompt_used": optimized_prompt_used,
            "resolved_categories": sorted(resolved_categories),
            "detailed_review": detailed_review,
        }
    }
