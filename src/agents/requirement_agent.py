from src.graph.state import MusicAgentState


def understand_requirement(state: MusicAgentState) -> MusicAgentState:
    requirement = state.get("user_requirement", "").strip()
    if not requirement:
        requirement = "Create a polished instrumental music draft with a clear motif."

    return {"user_requirement": requirement}
