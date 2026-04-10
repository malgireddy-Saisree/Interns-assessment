"""
FAQ Agent node for LangGraph.
"""
from langchain_core.messages import SystemMessage
from langgraph.prebuilt import create_react_agent
from agents.llm_factory import get_llm
from tools.faq_search_tool import faq_search_tool

FAQ_PROMPT = """You are a hotel information and FAQ specialist.
Answer user questions regarding hotel amenities, room types, policies, and general info by searching the system.
Be polite, clear, and comprehensive. Do not make up information that isn't returned by your tools.
"""

def get_faq_agent():
    llm = get_llm()
    tools = [faq_search_tool]
    return create_react_agent(llm, tools, prompt=FAQ_PROMPT)
