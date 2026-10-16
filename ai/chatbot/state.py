from typing import Annotated, TypedDict
from langgraph.graph.message import add_messages


class AgentState(TypedDict):
    """Graph state: just the running conversation.

    Widgets are deliberately NOT part of this state. If they were, and were
    accumulated with a reducer (e.g. operator.add), they'd keep piling up
    turn after turn since the checkpointer persists state across the whole
    thread. Instead, widgets are collected per-turn via a plain list passed
    through RunnableConfig -- see tools.py (_record_widget) and chatbot.py
    (widget_sink) for the two ends of that.
    """
    messages: Annotated[list, add_messages]