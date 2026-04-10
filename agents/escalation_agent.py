"""
Escalation Agent node for LangGraph.
"""
import json
from langchain_core.messages import SystemMessage
from langgraph.prebuilt import create_react_agent
from agents.llm_factory import get_llm
from tools.notification_tool import notification_tool
from db.sqlite_client import create_escalation
from langchain_core.tools import tool

# We wrap the escalation logic as a standard Langchain tool for this agent
@tool
def trigger_escalation(customer_id: str, reason: str, conversation_summary: str = "", booking_id: str = "") -> str:
    """Trigger an escalation, file it in the DB, and notify front-desk.
    Args:
        customer_id: The customer ID if known.
        reason: Why the user wants to talk to a human.
        conversation_summary: Summary of what happened.
        booking_id: Relevant booking ID.
    Returns escalation confirmation.
    """
    result = create_escalation(
        customer_id=customer_id,
        reason=reason,
        conversation_summary=conversation_summary,
        booking_id=booking_id if booking_id else None,
    )

    # Notify front-desk
    notification_tool.invoke({
        "recipient": "frontdesk@stayease.com",
        "subject": f"Escalation {result['escalation_id']} — {reason}",
        "message": (
            f"Customer {customer_id} has requested human assistance.\n"
            f"Reason: {reason}\n"
            f"Booking: {booking_id or 'N/A'}\n"
            f"Summary: {conversation_summary or 'N/A'}"
        ),
    })
    return json.dumps(result, indent=2)

ESCALATION_PROMPT = """You are an Escalation management specialist.
A user has requested to speak to a human or is extremely dissatisfied.
Call the `trigger_escalation` tool with the relevant context provided by the user, then assure them a human agent will be with them shortly.
"""

def get_escalation_agent():
    llm = get_llm()
    tools = [trigger_escalation]
    return create_react_agent(llm, tools, prompt=ESCALATION_PROMPT)
