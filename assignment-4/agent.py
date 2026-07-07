from langchain_openai import ChatOpenAI
from langgraph.checkpoint.memory import MemorySaver
from langgraph.prebuilt import create_react_agent

from browser_tools import click_element, get_user_profile, navigate_to, type_text

SESSION_CONFIG = {"configurable": {"thread_id": "session-1"}}


def build_agent():
    llm = ChatOpenAI(model="gpt-4o-mini", temperature=0)
    tools = [navigate_to, click_element, type_text, get_user_profile]
    memory = MemorySaver()
    return create_react_agent(llm, tools, checkpointer=memory)
