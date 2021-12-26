import asyncio
from asyncevents import on_event, emit


@on_event("test")
async def hello(_, event: str):
    print(f"Hello {event!r}!")


@on_event("test")
async def hi(_, event: str):
    print(f"Hi {event!r}!")


async def main():
    print("Firing blocking event 'test'")
    await emit("test")
    print("Handlers for event 'test' have exited")


if __name__ == "__main__":
    asyncio.run(main())
