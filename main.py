"""
StayEase Concierge — CLI Entry Point
Run:  python main.py
"""
import os
import sys
import uuid

# Fix Windows console encoding for Unicode
if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

# Ensure project root is on the path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from agents.planner import run_planner


def main():
    conversation_id = str(uuid.uuid4())

    print("=" * 60)
    print("  StayEase Concierge - AI Hotel Assistant")
    print("=" * 60)
    print("  Hotels: H001 City Grand (Hyderabad) | H002 Beach Resort (Vizag)")
    print("  Type 'quit' or 'exit' to end the conversation.")
    print("=" * 60)
    print()

    while True:
        try:
            user_input = input("You: ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\n\nGoodbye! Thank you for choosing StayEase.")
            break

        if not user_input:
            continue
        if user_input.lower() in ("quit", "exit", "bye"):
            print("\nConcierge: Goodbye! Thank you for choosing StayEase. Have a wonderful day!\n")
            break

        print()
        try:
            response = run_planner(user_input, conversation_id)
            print(f"Concierge: {response}")
        except Exception as e:
            print(f"Error: {e}")
        print()


if __name__ == "__main__":
    main()
