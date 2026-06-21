# MusicAgent Studio 架构图

本文档记录 MusicAgent Studio 当前版本的核心架构图，便于课程报告、README 或 GitHub 页面引用。图中内容以当前 `src` 目录实现为准。

## 1. 系统总体架构

```mermaid
flowchart TB
    User["用户<br/>自然语言需求 / 上传音频"] --> UI["Streamlit 前端<br/>src/app.py"]

    UI --> Mode{"运行模式"}
    Mode -->|AI 音乐生成| GenGraph["生成工作流<br/>LangGraph StateGraph"]
    Mode -->|AI 音乐鉴赏| AppGraph["鉴赏工作流<br/>LangGraph StateGraph"]

    subgraph GraphLayer["工作流层：src/graph"]
        GenGraph
        AppGraph
        State["MusicAgentState<br/>src/graph/state.py"]
    end

    subgraph AgentLayer["Agent 层：src/agents"]
        RequirementAgent["Requirement Agent<br/>需求理解"]
        SpecAgent["Spec Agent<br/>Music Spec 生成"]
        PromptAgent["Prompt Agent<br/>生成 Prompt"]
        AppreciationAgent["Appreciation Agent<br/>音乐鉴赏"]
        RevisionAgent["Revision Agent<br/>修改建议"]
    end

    subgraph ToolLayer["工具层：src/tools"]
        RAG["RAG Retriever<br/>本地知识检索"]
        Generator["Music Generator<br/>Mock / MusicGen"]
        Analyzer["Audio Analyzer<br/>librosa 特征提取"]
        Memory["Memory Store<br/>历史记录保存"]
    end

    subgraph DataLayer["数据与知识层"]
        Knowledge["src/knowledge<br/>音乐风格 / 场景 / 评分知识"]
        Generated["data/generated<br/>生成音频"]
        Uploaded["data/uploaded<br/>上传音频"]
        History["data/history<br/>JSON 历史记录"]
        Env[".env<br/>API Key 与后端配置"]
    end

    GenGraph --> State
    AppGraph --> State
    State --> RequirementAgent
    State --> RAG
    RAG --> Knowledge
    State --> SpecAgent
    State --> PromptAgent
    State --> Generator
    Generator --> Generated
    Uploaded --> Analyzer
    Generated --> Analyzer
    State --> Analyzer
    State --> AppreciationAgent
    State --> RevisionAgent
    State --> Memory
    Memory --> History
    Env --> Generator
```

## 2. 双模式工作流

```mermaid
flowchart LR
    Start["用户输入"] --> Mode{"选择模式"}

    Mode -->|生成模式| G1["understand_requirement"]
    G1 --> G2["retrieve_music_context"]
    G2 --> G3["generate_music_spec"]
    G3 --> G4["generate_prompt"]
    G4 --> G5["generate_music"]
    G5 --> G6["analyze_audio"]
    G6 --> G7["appreciate_music"]
    G7 --> G8["generate_revision"]
    G8 --> G9["save_history"]
    G9 --> EndG["返回完整 MusicAgentState"]

    Mode -->|鉴赏模式| A1["understand_requirement"]
    A1 --> A2["retrieve_music_context"]
    A2 --> A3["generate_music_spec"]
    A3 --> A4["analyze_audio"]
    A4 --> A5["appreciate_music"]
    A5 --> A6["save_history"]
    A6 --> EndA["返回赏析结果"]

    Upload["用户上传音频"] --> A4
```

## 3. RAG 增强链路

```mermaid
sequenceDiagram
    participant User as 用户
    participant UI as Streamlit 对话界面
    participant Graph as LangGraph 工作流
    participant Req as Requirement Agent
    participant RAG as RAG Retriever
    participant KB as 本地 Markdown 知识库
    participant Spec as Spec Agent
    participant App as Appreciation Agent

    User->>UI: 输入音乐需求或鉴赏目标
    UI->>Graph: 构造 MusicAgentState
    Graph->>Req: understand_requirement
    Req-->>Graph: 结构化用户意图
    Graph->>RAG: retrieve_music_context
    RAG->>KB: 检索风格、场景、Prompt 示例、评分规则
    KB-->>RAG: 返回相关片段与来源
    RAG-->>Graph: 写入 retrieved_context / rag_sources / rag_summary
    Graph->>Spec: generate_music_spec
    Spec-->>Graph: 结合 RAG 生成 Music Spec
    Graph->>App: appreciate_music
    App-->>Graph: 结合音频特征与 RAG 生成鉴赏结果
```

## 4. MusicAgentState 数据流

```mermaid
flowchart TB
    Input["user_requirement<br/>latest_user_message<br/>run_mode"] --> State["MusicAgentState"]

    State --> Intent["需求理解结果<br/>music_spec 初始语义"]
    State --> RAGFields["RAG 字段<br/>rag_query<br/>rag_summary<br/>retrieved_context<br/>rag_sources<br/>rag_matches"]
    State --> Spec["music_spec<br/>style / mood / tempo / instruments / structure"]
    State --> Prompt["generation_prompt<br/>optimized_prompt"]
    State --> Audio["audio_path<br/>generation_result"]
    State --> Features["audio_features<br/>duration / tempo / rms / centroid / zcr / onset"]
    State --> Review["appreciation_result<br/>score / strengths / analysis"]
    State --> Revision["revision_suggestion"]
    State --> History["history_id"]
```

## 5. 运行与扩展说明

- 默认生成后端为本地 Mock，便于课堂 Demo 稳定运行。
- 可选 MusicGen 后端通过 `.env` 配置开启，生成失败时可回退到 Mock。
- 生成模式与鉴赏模式共享 RAG、音频分析、音乐鉴赏和历史保存模块。
- 后续可扩展向量数据库、云端音乐生成 API、长期记忆和更细粒度的 LLM 评价指标。
