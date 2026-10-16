"""Builds the LangGraph agent that replaces the old manual while-loop in
chatbot.py.

Structure:
    START -> agent -> (tool call?) -> tools -> agent -> ... -> END

This is the same shape as the original loop: call the model, if it asked for
a tool run it and feed the result back, repeat until the model just returns
text. LangGraph's prebuilt ToolNode/tools_condition do the routing that used
to be hand-written.
"""
import os
from dotenv import load_dotenv

load_dotenv()

from langchain_core.messages import SystemMessage
from langchain_google_genai import ChatGoogleGenerativeAI
from langgraph.checkpoint.memory import MemorySaver
from langgraph.graph import END, START, StateGraph
from langgraph.prebuilt import ToolNode, tools_condition

from .state import AgentState
from .tools import ALL_TOOLS

MODEL = "gemini-3.1-flash-lite"

SYSTEM_PROMPT = (
    "You are a warm, friendly vehicle insurance assistant. You help customers 1. apply for a "
    "policy and 2. file and track claims. Collect information conversationally, one or two "
    "questions at a time, never as a cold form. When you receive a list of policies, present them "
    "clearly with their features and premiums and let the customer choose. Always tell the customer "
    "their application id, policy number, or claim number when you get one. Never invent ids or "
    "numbers - only use ones returned by the tools. Be concise and human."
)

# max_retries covers the same "Gemini is briefly flaky" case the old code
# handled with a manual 3-attempt/backoff loop.
# google_api_key is passed explicitly so we can keep using GEMINI_API_KEY as
# the env var name (ChatGoogleGenerativeAI otherwise defaults to GOOGLE_API_KEY).
llm = ChatGoogleGenerativeAI(
    model=MODEL, max_retries=3, google_api_key=os.environ["GEMINI_API_KEY"]
)
llm_with_tools = llm.bind_tools(ALL_TOOLS)


def agent_node(state: AgentState) -> dict:
    """Call the model with the system prompt + conversation so far."""
    messages = [SystemMessage(content=SYSTEM_PROMPT), *state["messages"]]
    response = llm_with_tools.invoke(messages)
    return {"messages": [response]}


builder = StateGraph(AgentState)
builder.add_node("agent", agent_node)
builder.add_node("tools", ToolNode(ALL_TOOLS))

builder.add_edge(START, "agent")
# tools_condition looks at the agent's last message: if it has tool_calls,
# route to "tools"; otherwise route to END. This replaces the old
# `if not function_call: return` check.
builder.add_conditional_edges("agent", tools_condition, {"tools": "tools", END: END})
builder.add_edge("tools", "agent")

# MemorySaver + thread_id replaces the old pattern of passing a `contents`
# list around by hand -- the checkpointer now owns conversation history.
graph = builder.compile(checkpointer=MemorySaver())