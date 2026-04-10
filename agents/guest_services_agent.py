"""
Guest Services Agent node for LangGraph.
"""
from langchain_core.messages import SystemMessage
from langgraph.prebuilt import create_react_agent
from agents.llm_factory import get_llm
from tools.guest_services_tool import guest_services_tool
from tools.guest_history_tool import guest_history_tool

SERVICES_PROMPT = """You are an in-stay guest services specialist.
You help current or past guests order services, file complaints, or look up their booking history.
You can look up their profile and recent bookings using the guest_history_tool.
You can also add services to their active booking or file complaints using guest_services_tool.
"""

def get_guest_services_agent():
    llm = get_llm()
    tools = [guest_services_tool, guest_history_tool]
    return create_react_agent(llm, tools, prompt=SERVICES_PROMPT)
