"""
Booking Agent node for LangGraph.
"""
from langchain_core.messages import SystemMessage
from langgraph.prebuilt import create_react_agent
from agents.llm_factory import get_llm
from tools.availability_tool import availability_tool
from tools.booking_tool import booking_tool
from tools.cancel_booking_tool import cancel_booking_tool
from tools.register_guest_tool import register_guest_tool

BOOKING_PROMPT = """You are a hotel booking specialist. 
Your job is to help users check room availability, book rooms, and cancel bookings.
If the customer provides an email or name but is not registered, use register_guest_tool to get a customer_id first.
Always confirm booking details with the user after a successful operation.
"""

def get_booking_agent():
    llm = get_llm()
    tools = [availability_tool, booking_tool, cancel_booking_tool, register_guest_tool]
    return create_react_agent(llm, tools, prompt=BOOKING_PROMPT)
