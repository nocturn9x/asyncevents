import asyncio
from asyncevents import on_event, emit


@on_event("hello", oneshot=True)  # The handler is removed after it fires once
async def hello(_, event: str):
    print(f"Hello {event!r}!")


async def main():
    print("Firing blocking event 'hello'")
    await emit("hello")
    print("Handlers for event 'hello' have exited")
    await emit("hello")  # Nothing happens


if __name__ == "__main__":
    asyncio.run(main())
