"""
The orchestrator / planner agent.
Uses Azure OpenAI GPT-4o directly with function-calling.
Zero dependency on LangChain.
"""
import json
from openai import AzureOpenAI

from config.settings import (
    AZURE_OPENAI_API_KEY,
    AZURE_OPENAI_ENDPOINT,
    AZURE_OPENAI_DEPLOYMENT,
    AZURE_OPENAI_API_VERSION,
)
from tools import ALL_TOOLS
from memory.conversation_memory import get_memory

# ── Azure OpenAI client (module-level singleton) ──────────────

_client = AzureOpenAI(
    api_key=AZURE_OPENAI_API_KEY,
    azure_endpoint=AZURE_OPENAI_ENDPOINT,
    api_version=AZURE_OPENAI_API_VERSION,
)

# ── System prompt ─────────────────────────────────────────────

SYSTEM_PROMPT = """\
You are **StayEase Concierge**, an AI assistant for the StayEase hotel chain.
You help guests with bookings, cancellations, FAQs, services, complaints, and escalations.

## Hotels
- H001 — StayEase City Grand (Hyderabad). Rooms: standard ₹3,500 | deluxe ₹5,500 | suite ₹9,500.
- H002 — StayEase Beach Resort (Vizag). Rooms: standard ₹4,500 | deluxe ₹7,500 | suite ₹15,000.

## Rules
1. always greet the guest warmly.
2. For BOOKINGS: collect customer_id (or identify from context), hotel, room_type, check_in, check_out, guests. Then check availability → confirm booking → update DB.
3. If a guest wants to book or access services and is NOT registered, use `register_guest_tool` to ask for their name and email, and register them to get a new `customer_id`.
4. For CANCELLATIONS: ask for booking_id, then cancel and communicate the refund.
5. For FAQs: use the faq_search_tool and give a grounded answer.
6. For SERVICES / COMPLAINTS: use guest_services_tool with action='add_service' or 'file_complaint'.
7. For ESCALATION: if the guest explicitly asks to speak to a human, or after 3 failed resolution attempts, escalate.
8. ALWAYS use tools to read/write data — never make up booking IDs, prices, or availability.
9. When a booking or cancellation succeeds, clearly confirm the details (ID, dates, cost/refund).
10. Be concise, polite, and professional. Use ₹ for currency.
11. **PRIVACY & SECURITY**: You are a pure customer support agent. NEVER reveal private information. Do NOT list out other customers' names, emails, phone numbers, or customer IDs. Only provide information related to the current user's explicitly provided identity. If someone asks for a list of guests or another guest's booking details, politely refuse to provide it.

"""

# ── Build tool definitions + lookup map ───────────────────────

_TOOL_DEFS = [t.to_openai_tool() for t in ALL_TOOLS]
_TOOL_MAP = {t.name: t for t in ALL_TOOLS}


# ── Public entry point ────────────────────────────────────────

def run_planner(user_message: str, conversation_id: str) -> str:
    """
    Main entry point called by the CLI.
    1. Load conversation history
    2. Send to GPT-4o with tools
    3. Loop: if GPT wants to call tools, execute them and feed results back
    4. Save memory and return final text
    """
    memory = get_memory(conversation_id)

    # Build messages list
    messages = [{"role": "system", "content": SYSTEM_PROMPT}]

    # Add conversation history
    for msg in memory.chat_memory.messages:
        role = "user" if msg.type == "human" else "assistant"
        messages.append({"role": role, "content": msg.content})

    # Add current user message
    messages.append({"role": "user", "content": user_message})

    # Tool-calling loop (max 10 iterations)
    for _ in range(10):
        response = _client.chat.completions.create(
            model=AZURE_OPENAI_DEPLOYMENT,
            messages=messages,
            tools=_TOOL_DEFS,
            tool_choice="auto",
            temperature=0.3,
        )

        choice = response.choices[0]

        # If model wants to call tools
        if choice.message.tool_calls:
            # Append assistant message with tool calls
            messages.append(choice.message)

            # Execute each tool call
            for tool_call in choice.message.tool_calls:
                fn_name = tool_call.function.name
                fn_args = json.loads(tool_call.function.arguments)

                print(f"  [TOOL] Calling {fn_name}({json.dumps(fn_args, default=str)})")

                tool_fn = _TOOL_MAP.get(fn_name)
                if tool_fn:
                    try:
                        result = tool_fn.invoke(fn_args)
                    except Exception as e:
                        result = json.dumps({"error": str(e)})
                else:
                    result = json.dumps({"error": f"Unknown tool: {fn_name}"})

                print(f"  [DONE] {fn_name} -> {str(result)[:200]}")

                # Feed tool result back
                messages.append({
                    "role": "tool",
                    "tool_call_id": tool_call.id,
                    "content": str(result),
                })
        else:
            # No more tool calls — we have the final response
            output = choice.message.content or "I'm sorry, I couldn't process that."

            # Save conversation turn
            memory.chat_memory.add_user_message(user_message)
            memory.chat_memory.add_ai_message(output)

            return output

    return "I've reached the maximum number of steps. Please try rephrasing your request."
