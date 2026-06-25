import json
from intent_parser import parse_intent

TEST_COMMANDS = [
    "apply to this job at careers.openai.com",           # fill_form
    "close all tabs",                                     # click
    "email this summary to my boss at boss@company.com",  # email
    "summarize this article",                             # summarize
    "navigate to GitHub",                                 # navigate
    "fill in the contact form with my details",           # fill_form
    "search for Python developer jobs on LinkedIn",       # navigate
    "send a follow-up email to the recruiter",            # email
    "click the submit button",                            # click
    "do something useful",                                # clarify (ambiguous)
]


def print_result(index: int, command: str, result: dict) -> None:
    action = result.get("action", "unknown")
    url = result.get("target_url") or "—"
    steps = result.get("steps", [])
    data = result.get("data", {})
    question = result.get("question", "")

    print(f"\n[{index}] Command : {command}")
    print(f"    Action  : {action}")

    if action == "clarify":
        print(f"    Question: {question}")
    else:
        print(f"    URL     : {url}")
        if data:
            print(f"    Data    : {json.dumps(data, indent=14)[1:-1].strip()}")
        print(f"    Steps   :")
        for i, step in enumerate(steps, 1):
            print(f"             {i}. {step}")


def main() -> None:
    print("=" * 60)
    print("  Assignment 3 — Intent Parser Test Suite")
    print("=" * 60)

    passed = 0
    failed = 0

    for i, command in enumerate(TEST_COMMANDS, 1):
        try:
            result = parse_intent(command)
            print_result(i, command, result)
            passed += 1
        except Exception as exc:
            print(f"\n[{i}] Command : {command}")
            print(f"    ERROR   : {exc}")
            failed += 1

    print("\n" + "=" * 60)
    print(f"  Results: {passed} passed, {failed} failed out of {len(TEST_COMMANDS)} commands")
    print("=" * 60)


if __name__ == "__main__":
    main()
