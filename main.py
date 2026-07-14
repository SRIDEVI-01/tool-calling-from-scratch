from agent import run_conversation


def print_trace(steps: dict):
    print(f"User: {steps['user_message']}")
    print("Model first response:\n", steps["model_first_response"])

    if steps["parse_error"]:
        print(f"\nCould not parse tool call: {steps['parse_error']}")
        return

    if steps["tool_call"]:
        tc = steps["tool_call"]
        print(f"\nDetected tool call: {tc['name']}({tc.get('arguments', {})})")
        print(f"Tool result: {steps['tool_result']}")
    else:
        print("\nNo tool call detected.")

    print("\nFinal answer:\n", steps["final_answer"])


if __name__ == "__main__":
    demo_queries = [
        "What's the weather in Mumbai?",
        "What time is it right now?",
        "What's 12 times 7 plus 3?",
        "Send an email to john@example.com about tomorrow's meeting",
        "Can you book me a flight to Tokyo?",
    ]

    for query in demo_queries:
        print("=" * 60)
        steps = run_conversation(query)
        print_trace(steps)
        print()
