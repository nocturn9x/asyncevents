import asyncio
from asyncevents import on_event, emit


@on_event("hello")
async def hello(_, event: str, n: int):
    print(f"Hello {event!r}! The number is {n}!")


async def main():
    print("Firing blocking event 'hello'")
    await emit("hello", True, 5)
    print("Handlers for event 'hello' have exited")


if __name__ == "__main__":
    asyncio.run(main())
