import asyncio
from asyncevents import on_event, emit, wait


@on_event("hello", oneshot=True)  # The handler is removed after it fires once
async def hello(_, event: str):
    print(f"Hello {event!r}!")


@on_event("hi", oneshot=True)
async def hi(_, event: str):
    print(f"Hi {event!r}!")


async def main():
    print("Firing blocking event 'hello'")
    await emit("hello")
    print("Handlers for event 'hello' have exited")
    await emit("hello")  # Nothing happens
    print("Firing non-blocking event 'hi'")
    await emit("hi", block=False)
    await wait("hi")
    print("Handlers for event 'hi' have exited")
    await emit("hi")  # Nothing happens


if __name__ == "__main__":
    asyncio.run(main())
