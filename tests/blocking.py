import asyncio
from asyncevents import on_event, emit


@on_event("hello")
async def hello(_, event: str):
    print(f"Hello {event!r}!")


async def main():
    print("Firing blocking event 'hello'")
    await emit("hello")
    print("Handlers for event 'hello' have exited")


if __name__ == "__main__":
    asyncio.run(main())
