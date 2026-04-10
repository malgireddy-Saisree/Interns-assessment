"""
Escalation Agent node for LangGraph.
"""
from langchain_core.messages import SystemMessage
from langgraph.prebuilt import create_react_agent
from agents.llm_factory import get_llm
from tools.escalation_tool import trigger_escalation

ESCALATION_PROMPT = """You are an Escalation management specialist.
A user has requested to speak to a human or is extremely dissatisfied.
Call the `trigger_escalation` tool with the relevant context provided by the user, then assure them a human agent will be with them shortly.
"""

def get_escalation_agent():
    llm = get_llm()
    tools = [trigger_escalation]
    return create_react_agent(llm, tools, prompt=ESCALATION_PROMPT)
