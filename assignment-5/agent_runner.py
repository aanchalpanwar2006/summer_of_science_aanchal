import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "assignment-4"))

from agent import build_agent  # noqa: E402  (assignment-4/agent.py)


async def run_agent(
    task_id: str,
    command: str,
    tasks: dict,
    queues: dict,
) -> None:
    tasks[task_id]["status"] = "running"
    queue: asyncio.Queue = queues[task_id]

    try:
        agent = build_agent()
        config = {"configurable": {"thread_id": task_id}}
        final_result = ""

        async for event in agent.astream_events(
            {"messages": [("user", command)]},
            config=config,
            version="v2",
        ):
            kind = event["event"]

            if kind == "on_tool_start":
                tool_name = event.get("name", "unknown")
                tool_input = event.get("data", {}).get("input", "")
                step = f"Calling tool: {tool_name}({tool_input})"
                tasks[task_id]["steps"].append(step)
                await queue.put(step)

            elif kind == "on_tool_end":
                output = event.get("data", {}).get("output", "")
                step = f"Tool result: {output}"
                tasks[task_id]["steps"].append(step)
                await queue.put(step)

            elif kind == "on_chain_end":
                # Capture the final agent reply from the root chain
                output = event.get("data", {}).get("output", {})
                if isinstance(output, dict):
                    messages = output.get("messages", [])
                    if messages:
                        last = messages[-1]
                        content = getattr(last, "content", None) or str(last)
                        if content:
                            final_result = content

        tasks[task_id]["status"] = "done"
        tasks[task_id]["result"] = final_result

    except Exception as exc:
        tasks[task_id]["status"] = "error"
        tasks[task_id]["result"] = str(exc)

    finally:
        await queue.put(None)  # sentinel — tells WebSocket to close
