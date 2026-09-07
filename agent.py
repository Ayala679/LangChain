"""
agent.py
---------
Command-line entry point.
All graph and approval logic lives in services/.
"""

import sys
from services.chat_service import start_run, resume_run, new_thread_id


def run_cli(topic: str):
    thread_id = new_thread_id()
    print(f"\nSearching for sources on: \"{topic}\"\n" + "-" * 60)

    result = start_run(topic, thread_id)

    while result["interrupted"]:
        print("\n SOURCES FOUND:\n")
        print(result["sources"])
        print("\n" + "-" * 60)

        print("\nOptions:")
        print("  [1] Approve selected sources")
        print("  [2] Reject and re-search with feedback")
        action = input("\nChoose (1/2): ").strip()

        if action == "2":
            feedback = input("Enter your feedback: ").strip() or "Please find better sources."
            result = resume_run({"action": "reject", "feedback": feedback}, thread_id)
        else:
            selection = input(
                "\nEnter source numbers to keep (e.g. 1,3,5) or press Enter for all: "
            ).strip() or "all"
            result = resume_run({"action": "approve", "selection": selection}, thread_id)

    print("\n" + "-" * 60)
    print(result["final_answer"])


if __name__ == "__main__":
    topic = sys.argv[1] if len(sys.argv) > 1 else "Artificial Intelligence in healthcare"
    run_cli(topic)
