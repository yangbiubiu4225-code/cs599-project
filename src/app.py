from __future__ import annotations

from pathlib import Path
import sys
from uuid import uuid4

import streamlit as st

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.graph.music_graph import run_appreciation_workflow, run_generation_workflow
from src.graph.state import MusicAgentState


EXAMPLE_PROMPTS = [
    "生成一段适合科幻短片开场的 cinematic electronic 音乐，氛围神秘但有推进感。",
    "把上一版改得更明亮一些，节奏更紧凑，主旋律更容易记住。",
    "请从情绪表达、节奏稳定性和声音质感三个角度评价这段音乐。",
]

WORKFLOW_LABELS = {
    "generation": [
        "需求理解",
        "Music Spec",
        "Prompt 生成",
        "音乐生成",
        "音频分析",
        "鉴赏评价",
        "修改建议",
        "历史保存",
    ],
    "appreciation": [
        "需求理解",
        "Music Spec",
        "音频分析",
        "鉴赏评价",
        "历史保存",
    ],
}


def _save_uploaded_audio(uploaded_file) -> str:
    output_dir = Path("data/uploaded")
    output_dir.mkdir(parents=True, exist_ok=True)
    suffix = Path(uploaded_file.name).suffix or ".wav"
    audio_path = output_dir / f"{uuid4()}{suffix}"
    audio_path.write_bytes(uploaded_file.getbuffer())
    return str(audio_path)


def _audio_mime(audio_path: str) -> str:
    suffix = Path(audio_path).suffix.lower()
    if suffix == ".mp3":
        return "audio/mpeg"
    if suffix == ".ogg":
        return "audio/ogg"
    if suffix == ".flac":
        return "audio/flac"
    if suffix == ".m4a":
        return "audio/mp4"
    return "audio/wav"


def _play_audio(audio_path: str | None) -> None:
    if not audio_path:
        st.info("暂无音频。")
        return

    path = Path(audio_path)
    if not path.exists():
        st.warning(f"音频文件不存在：{audio_path}")
        return

    st.audio(path.read_bytes(), format=_audio_mime(audio_path))
    st.caption(str(path))


def _init_session() -> None:
    if "messages" not in st.session_state:
        st.session_state.messages = [
            {
                "role": "assistant",
                "content": (
                    "你好，我是 MusicAgent Studio。你可以像聊天一样描述音乐需求，"
                    "生成模式下我会迭代音乐草稿；鉴赏模式下我会直接给出音乐赏析。"
                ),
            }
        ]
    if "last_result" not in st.session_state:
        st.session_state.last_result = None
    if "uploaded_audio_path" not in st.session_state:
        st.session_state.uploaded_audio_path = None


def _reset_conversation() -> None:
    st.session_state.messages = [
        {
            "role": "assistant",
            "content": "新的创作会话已开始。告诉我你想要什么场景、风格、情绪或参考方向。",
        }
    ]
    st.session_state.last_result = None
    st.session_state.uploaded_audio_path = None


def _compose_requirement(user_message: str, last_result: MusicAgentState | None) -> str:
    if not last_result:
        return user_message.strip()

    previous_spec = last_result.get("music_spec", {})
    previous_score = last_result.get("appreciation_result", {}).get("overall_score", "暂无")
    previous_issues = last_result.get("appreciation_result", {}).get("issues", [])
    issue_summary = "；".join(previous_issues[:3]) if previous_issues else "暂无明显问题"

    return f"""
上一轮音乐方向：
风格={previous_spec.get("style", "未知")}；
情绪={previous_spec.get("mood", "未知")}；
速度={previous_spec.get("tempo_bpm", "未知")} BPM；
调性={previous_spec.get("key", "未知")}

上一轮鉴赏分数：
{previous_score}

上一轮待优化点：
{issue_summary}

请以本轮用户追加要求为最高优先级，覆盖上一轮 Prompt 优化内容：
{user_message.strip()}
""".strip()


def _run_agent_turn(
    user_message: str,
    mode: str,
    generator_backend: str,
) -> MusicAgentState | None:
    last_result = st.session_state.last_result
    requirement = _compose_requirement(user_message, last_result)

    if mode == "生成模式":
        return run_generation_workflow(
            requirement,
            generator_backend=generator_backend,
            latest_user_message=user_message,
        )

    audio_path = st.session_state.uploaded_audio_path
    if not audio_path:
        st.session_state.messages.append(
            {
                "role": "assistant",
                "content": "请先在左侧上传一段音频，我才能进入鉴赏模式分析它。",
            }
        )
        return None

    return run_appreciation_workflow(
        requirement,
        audio_path,
        latest_user_message=user_message,
    )


def _format_agent_reply(state: MusicAgentState) -> str:
    spec = state.get("music_spec", {})
    appreciation = state.get("appreciation_result", {})
    score = appreciation.get("overall_score", "暂无")
    issues = appreciation.get("issues", [])
    strengths = appreciation.get("strengths", [])
    revision = state.get("revision_suggestion", "暂无修改建议。")

    if state.get("run_mode") == "appreciation":
        return _format_appreciation_reply(state)

    issue_text = "；".join(issues) if issues else "暂未发现明显问题"
    strength_text = "；".join(strengths) if strengths else "当前版本已形成可分析结果"

    return f"""
我已经完成这一轮处理。

**当前方向**：{spec.get("style", "未识别风格")} / {spec.get("mood", "未识别情绪")} / {spec.get("tempo_bpm", "未知")} BPM

**鉴赏分数**：{score}

**主要优点**：{strength_text}

**需要优化**：{issue_text}

**下一轮建议**：{revision}
""".strip()


def _format_appreciation_reply(state: MusicAgentState) -> str:
    spec = state.get("music_spec", {})
    appreciation = state.get("appreciation_result", {})
    features = state.get("audio_features", {})
    scores = appreciation.get("profile_scores", {})
    detailed_review = appreciation.get("detailed_review", {})
    score = appreciation.get("overall_score", "暂无")

    duration = features.get("duration", "未知")
    tempo = features.get("tempo", "未知")
    energy = scores.get("energy", "未知")
    brightness = scores.get("brightness", "未知")
    review_text = "\n\n".join(
        f"**{title}**：{content}" for title, content in detailed_review.items()
    )
    if not review_text:
        review_text = "这段音乐已经形成可分析的节奏、能量和音色轮廓。"

    return f"""
我已经完成这段音乐的赏析。

**参考方向**：{spec.get("style", "未识别风格")} / {spec.get("mood", "未识别情绪")}

**鉴赏分数**：{score}

**基础听感**：音频约 {duration} 秒，检测节奏约 {tempo} BPM；整体能量画像为 {energy}，明亮度画像为 {brightness}。

{review_text}
""".strip()


def _render_chat() -> None:
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])


def _render_workflow_trace(state: MusicAgentState | None) -> None:
    st.subheader("Agent 工作流")
    if not state:
        st.info("开始对话后，这里会显示每轮 Agent 节点。")
        return

    labels = WORKFLOW_LABELS.get(state.get("run_mode", "generation"), [])
    for index, label in enumerate(labels, start=1):
        st.write(f"{index}. {label} 已完成")


def _render_memory(state: MusicAgentState | None) -> None:
    st.subheader("会话记忆")
    turns = sum(1 for item in st.session_state.messages if item["role"] == "user")
    st.metric("对话轮次", turns)

    if not state:
        st.caption("暂无历史记录。")
        return

    st.write(f"History ID: `{state.get('history_id', '暂无')}`")
    st.write(f"Run Mode: `{state.get('run_mode', 'unknown')}`")
    backend = state.get("generation_result", {}).get(
        "used_backend",
        state.get("generator_backend", "N/A"),
    )
    st.write(f"Backend: `{backend}`")


def _render_result_panel(state: MusicAgentState | None) -> None:
    if not state:
        st.info("还没有生成结果。发一条消息后，Agent 会在这里沉淀当前状态。")
        return

    run_mode = state.get("run_mode", "generation")
    generation_result = state.get("generation_result", {})
    if generation_result.get("fallback_used"):
        st.warning("MusicGen 后端不可用，已自动回退到本地 Mock。")
        with st.expander("查看回退原因"):
            st.json(generation_result.get("error", {}))

    overview_1, overview_2, overview_3 = st.columns(3)
    with overview_1:
        st.metric("模式", run_mode)
    with overview_2:
        score = state.get("appreciation_result", {}).get("overall_score", "暂无")
        st.metric("鉴赏分数", score)
    with overview_3:
        if run_mode == "appreciation":
            st.metric("音频来源", "上传音频")
        else:
            backend = generation_result.get("used_backend", "N/A")
            st.metric("生成后端", backend)

    if run_mode == "appreciation":
        tabs = st.tabs(["音频", "Music Spec", "音频特征", "赏析"])

        with tabs[0]:
            _play_audio(state.get("audio_path"))

        with tabs[1]:
            st.json(state.get("music_spec", {}))

        with tabs[2]:
            st.json(state.get("audio_features", {}))

        with tabs[3]:
            _render_appreciation_panel(state)
        return

    tabs = st.tabs(["音频", "Music Spec", "Prompt", "音频特征", "鉴赏", "修改建议"])

    with tabs[0]:
        _play_audio(state.get("audio_path"))

    with tabs[1]:
        st.json(state.get("music_spec", {}))

    with tabs[2]:
        st.code(state.get("generation_prompt") or "暂无 Prompt", language="text")
        with st.expander("优化后的 Prompt"):
            st.write(state.get("optimized_prompt") or "暂无")

    with tabs[3]:
        st.json(state.get("audio_features", {}))

    with tabs[4]:
        _render_generation_appreciation_panel(state)

    with tabs[5]:
        st.write(state.get("revision_suggestion") or "暂无修改建议。")


def _render_appreciation_panel(state: MusicAgentState) -> None:
    appreciation = state.get("appreciation_result", {})
    features = state.get("audio_features", {})
    scores = appreciation.get("profile_scores", {})
    detailed_review = appreciation.get("detailed_review", {})

    st.write("这是一段面向听感理解的赏析结果，重点放在节奏、能量、音色和情绪表达。")
    st.markdown("**听感概览**")
    st.write(
        f"- 时长约 {features.get('duration', '未知')} 秒，检测节奏约 "
        f"{features.get('tempo', '未知')} BPM。"
    )
    st.write(
        f"- 能量画像：{scores.get('energy', '未知')}；"
        f"明亮度画像：{scores.get('brightness', '未知')}；"
        f"起音活跃度：{scores.get('onset_activity', '未知')}。"
    )

    st.markdown("**详细赏析**")
    if detailed_review:
        for title, content in detailed_review.items():
            st.markdown(f"**{title}**")
            st.write(content)
    else:
        st.write("这段音乐已经形成可分析的节奏、能量和音色轮廓。")
    st.json(scores)


def _render_generation_appreciation_panel(state: MusicAgentState) -> None:
    appreciation = state.get("appreciation_result", {})
    strengths = appreciation.get("strengths", [])
    issues = appreciation.get("issues", [])
    st.write(appreciation.get("alignment_note", "暂无鉴赏说明。"))
    left, right = st.columns(2)
    with left:
        st.markdown("**优点**")
        for item in strengths or ["暂无"]:
            st.write(f"- {item}")
    with right:
        st.markdown("**问题**")
        for item in issues or ["暂无"]:
            st.write(f"- {item}")
    st.json(appreciation.get("profile_scores", {}))


def _inject_styles() -> None:
    st.markdown(
        """
        <style>
        .block-container {
            padding-top: 1.5rem;
            max-width: 1400px;
        }
        [data-testid="stSidebar"] {
            min-width: 300px;
        }
        div[data-testid="stChatMessage"] {
            border-radius: 8px;
            padding: 0.2rem 0;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )


def main() -> None:
    st.set_page_config(page_title="MusicAgent Studio", page_icon="M", layout="wide")
    _inject_styles()
    _init_session()

    st.title("MusicAgent Studio")
    st.caption("一个以多轮对话驱动的 AI 音乐生成与鉴赏 Agent")

    with st.sidebar:
        st.header("Agent 控制台")
        mode = st.radio("运行模式", ["生成模式", "鉴赏模式"])
        generator_backend = "mock"
        if mode == "生成模式":
            backend_label = st.selectbox(
                "音乐生成后端",
                ["本地 Mock", "MusicGen"],
                help="MusicGen 首次运行会下载模型；失败时会自动回退到 Mock。",
            )
            generator_backend = "musicgen" if backend_label == "MusicGen" else "mock"

        if mode == "鉴赏模式":
            uploaded_file = st.file_uploader(
                "上传待鉴赏音频",
                type=["wav", "mp3", "flac", "ogg", "m4a"],
            )
            if uploaded_file is not None:
                st.session_state.uploaded_audio_path = _save_uploaded_audio(uploaded_file)
                st.success("音频已载入，本轮对话会基于它进行鉴赏。")

        st.divider()
        st.markdown("**快速开始**")
        for index, prompt in enumerate(EXAMPLE_PROMPTS, start=1):
            if st.button(prompt, key=f"example_{index}", use_container_width=True):
                st.session_state.pending_prompt = prompt

        if st.button("清空对话", use_container_width=True):
            _reset_conversation()
            st.rerun()

    left, right = st.columns([0.95, 1.05], gap="large")

    with left:
        st.subheader("多轮对话")
        _render_chat()

        prompt = st.chat_input(
            "和 MusicAgent 对话：描述音乐、要求修改、追问鉴赏理由..."
        )
        prompt = st.session_state.pop("pending_prompt", prompt)

        if prompt:
            st.session_state.messages.append({"role": "user", "content": prompt})
            with st.chat_message("user"):
                st.markdown(prompt)

            with st.chat_message("assistant"):
                with st.spinner("Agent 正在理解需求、调用工具并更新记忆..."):
                    result = _run_agent_turn(prompt, mode, generator_backend)
                    if result:
                        st.session_state.last_result = result
                        reply = _format_agent_reply(result)
                        st.session_state.messages.append(
                            {"role": "assistant", "content": reply}
                        )
                        st.markdown(reply)

    with right:
        st.subheader("Agent 工作台")
        _render_memory(st.session_state.last_result)
        st.divider()
        _render_workflow_trace(st.session_state.last_result)
        st.divider()
        _render_result_panel(st.session_state.last_result)


if __name__ == "__main__":
    main()
