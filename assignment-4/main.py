import asyncio

from dotenv import load_dotenv

from agent import SESSION_CONFIG, build_agent
from browser_tools import close_browser, init_browser

DEMO_TASK = "go to https://google.com and search for AI news"


async def run_loop(agent) -> None:
    print("\nBrowser Agent ready. Type 'quit' to exit.")
    print(f"  Demo task: {DEMO_TASK}\n")

    while True:
        try:
            cmd = input("You: ").strip()
        except (EOFError, KeyboardInterrupt):
            break

        if not cmd:
            continue
        if cmd.lower() in ("quit", "exit", "q"):
            break

        result = await agent.ainvoke(
            {"messages": [("user", cmd)]},
            config=SESSION_CONFIG,
        )
        reply = result["messages"][-1].content
        print(f"\nAgent: {reply}\n")


async def main() -> None:
    load_dotenv()

    print("Starting browser...")
    await init_browser()

    agent = build_agent()

    try:
        await run_loop(agent)
    finally:
        print("\nClosing browser...")
        await close_browser()
        print("Done.")


if __name__ == "__main__":
    asyncio.run(main())
