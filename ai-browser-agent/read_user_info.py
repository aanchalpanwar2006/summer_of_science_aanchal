import asyncio
import json
from pathlib import Path


async def load_user_info(path: str) -> dict:
    def _read():
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    return await asyncio.to_thread(_read)


def format_address(addr: dict) -> str:
    return (
        f"{addr['street']}\n"
        f"          {addr['city']}, {addr['state']} {addr['zip']}\n"
        f"          {addr['country']}"
    )


async def main():
    path = Path(__file__).parent / "user_info.json"
    user = await load_user_info(path)

    addr = user.get("address", {})
    print("=" * 40)
    print("         USER PROFILE")
    print("=" * 40)
    print(f"  Name  : {user['name']}")
    print(f"  Email : {user['email']}")
    print(f"  Phone : {user['phone']}")
    print(f"  Addr  : {format_address(addr)}")
    print("=" * 40)


if __name__ == "__main__":
    asyncio.run(main())
