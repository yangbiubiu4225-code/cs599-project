# 项目名称
MusicAgent Studio

## 项目简介

MusicAgent Studio 是一个面向 AI 音乐创作场景的生成与鉴赏迭代智能体。系统支持“AI 音乐生成”和“AI 音乐鉴赏”两个运行模式，能够将用户的自然语言音乐需求转化为结构化 Music Spec，并通过音频分析、音乐鉴赏 Agent 和修改建议 Agent 形成可迭代的创作反馈闭环。

生成模式执行完整的“需求理解—Music Spec 生成—Prompt 生成—音乐生成—音频分析—鉴赏评价—修改建议—历史保存”流程。鉴赏模式跳过音乐生成和修改建议阶段，直接对用户上传的音频进行特征分析，并结合目标场景生成更详细的音乐赏析。

## 方向

方向一：Agentic AI 原生开发

## 技术栈

- AI IDE: Trae CN 
- LLM: OpenAI API
- Agent Framework: LangGraph
- UI: Streamlit
- Audio Analysis: librosa
- Music Generation: 本地 Mock / MusicGen(Transformers，可选)
- Storage: JSON / SQLite
- Container: Docker

## 目录结构
```text
src/
├── app.py                         # Streamlit 前端入口，负责页面展示、用户输入、音频播放和结果展示
├── config.py                      # 全局配置文件，负责读取环境变量、API Key、模型参数和项目路径配置
├── __init__.py
│
├── graph/                         # Agent 工作流编排模块
│   ├── __init__.py
│   ├── music_graph.py             # 基于 LangGraph 构建生成模式与鉴赏模式两个工作流
│   └── state.py                   # 定义 MusicAgentState，保存需求、Music Spec、Prompt、音频路径、分析结果等状态信息
│
├── agents/                        # Agent 节点实现目录
│   ├── __init__.py
│   ├── requirement_agent.py       # 需求理解 Agent，将用户自然语言需求解析为音乐创作意图
│   ├── spec_agent.py              # Music Spec 生成 Agent，将创作意图转化为结构化音乐规格
│   ├── prompt_agent.py            # Prompt 生成 Agent，将 Music Spec 转化为音乐生成模型可用的 Prompt
│   ├── appreciation_agent.py      # 音乐鉴赏 Agent，根据用户需求和音频特征评价生成结果
│   └── revision_agent.py          # 修改建议 Agent，根据鉴赏结果生成下一轮优化建议
│
├── tools/                         # Agent 可调用的工具模块
│   ├── __init__.py
│   ├── music_generator.py         # 音乐生成工具，支持本地 Mock 与可选 MusicGen 后端
│   ├── audio_analyzer.py          # 音频分析工具，使用 librosa 提取时长、节奏、能量、频谱等音频特征
│   ├── memory_store.py            # 记忆存储工具，保存用户偏好、历史生成记录和评价结果
│   └── report_writer.py           # 报告生成工具，将生成过程、音频特征、鉴赏结果和修改建议整理为报告
│
├── prompts/                       # Prompt 模板目录
│   ├── music_spec_prompt.txt      # Music Spec 生成提示词模板
│   ├── generation_prompt.txt      # 音乐生成 Prompt 转换提示词模板
│   ├── appreciation_prompt.txt    # 音乐鉴赏评价提示词模板
│   └── revision_prompt.txt        # 修改建议生成提示词模板
│
└── eval/                          # 测试与评估模块
    ├── test_cases.json            # 测试样例，包含不同音乐场景下的用户需求
    └── evaluate.py                # 评估脚本，用于评估 Spec 完整性、Prompt 质量和鉴赏结果有效性
```

## 核心功能

- 自然语言音乐需求理解
- Music Spec 自动生成
- 音乐生成 Prompt 生成
- 音乐生成工具调用
- 音频特征分析
- 音乐鉴赏评分与详细赏析
- 修改建议生成
- 历史记录保存

## 运行模式

### AI 音乐生成模式

```text
需求理解 -> Music Spec 生成 -> Prompt 生成 -> 音乐生成 -> 音频分析 -> 鉴赏评价 -> 修改建议 -> 历史保存
```

音乐生成后端支持：

- `mock`：默认本地合成 `.wav`，适合Demo展示，稳定且无需额外模型下载。
- `musicgen`：通过 Hugging Face Transformers 调用 MusicGen。本地未安装、模型下载失败或加载失败时，可自动回退到 `mock`。

### AI 音乐鉴赏模式

```text
需求理解 -> Music Spec 生成 -> 音频分析 -> 鉴赏评价 -> 历史保存
```

该模式跳过音乐生成与修改建议节点，直接分析用户上传音频，并从整体印象、节奏与律动、音色与空间、情绪表达、适用场景等角度给出赏析。两个模式共享音频分析工具、音乐鉴赏 Agent 和记忆存储工具。

## 安装与运行
1.创建conda环境
```bash
conda create -n musicagent python=3.10 -y
conda activate musicagent
```
2.安装基础依赖
```bash
pip install -r requirements.txt
```
3.配置环境变量
```bash
cp .env.example .env
```
4.启动项目
```bash
streamlit run src/app.py
```
默认使用 Mock 音乐生成，不需要额外模型M；usicGen 第一次运行会下载模型权重，配置会优先选择 `facebook/musicgen-small`。演示时建议把`MUSICGEN_DURATION` 设置为 5 到 8 秒。模型缓存默认放在 `data/model_cache/`
5.可选用musicgen（注意，musicgen为外部开源项目）
如果要使用 MusicGen 本地生成音乐
```bash
pip install -r requirements-musicgen.txt
```
同时需对.env进行修改
```env
MUSIC_GENERATOR_BACKEND=musicgen
MUSICGEN_MODEL=facebook/musicgen-small
MUSICGEN_DURATION=8
MUSICGEN_FALLBACK_TO_MOCK=true
```

## 项目状态

- [x] Proposal
- [x] MVP
- [ ] Final
