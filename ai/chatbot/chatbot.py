"""Thin adapter between the LangGraph agent (graph.py) and callers (Streamlit
or the CLI below).

chat_turn() keeps roughly the same job the old version had: take the user's
new message, run the model/tool loop, return (reply_text, widgets). The one
interface change is that callers now pass a `thread_id` string instead of a
`history`/`contents` list -- LangGraph's checkpointer owns the message
history now, keyed by that id.
"""
from langchain_core.messages import HumanMessage

from .graph import graph


def _as_text(content) -> str:
    """Normalize an AIMessage's .content down to a plain string.

    Depending on the model/SDK version, content can come back as a plain
    string OR as a list of content blocks (e.g. [{"type": "text", "text":
    "..."}, {"type": "..." , "extras": {"signature": ...}}]) -- the latter
    happens with some Gemini responses that attach extra metadata like
    thought signatures alongside the actual reply. We only want the text.
    """
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        parts = []
        for block in content:
            if isinstance(block, str):
                parts.append(block)
            elif isinstance(block, dict) and block.get("type") == "text":
                parts.append(block.get("text", ""))
        return "".join(parts)
    return str(content)


def chat_turn(thread_id: str, user_text: str) -> tuple[str, list]:
    """
    Run one turn of the conversation identified by `thread_id`.

    Returns (reply_text, widgets) where widgets is a list of the same
    {"type": ..., "data": ...} descriptors the Streamlit renderers already
    know how to draw.
    """
    widget_sink: list = []
    config = {"configurable": {"thread_id": thread_id, "widget_sink": widget_sink}}

    try:
        result = graph.invoke({"messages": [HumanMessage(content=user_text)]}, config=config)
    except Exception as e:
        return f"(The AI service is busy right now: {e}. Please try again in a moment.)", widget_sink

    reply_text = _as_text(result["messages"][-1].content)
    return reply_text, widget_sink


if __name__ == "__main__":
    import uuid

    print("Insurance assistant ready. Type 'quit' to exit.\n")
    thread_id = str(uuid.uuid4())
    while True:
        msg = input("You: ")
        if msg.lower() in ("quit", "exit"):
            break
        reply, _widgets = chat_turn(thread_id, msg)
        print("Assistant:", reply, "\n")