import asyncio
from asyncevents import on_event, emit


@on_event("hello")
async def hello(_, event: str):
    print(f"Hello {event!r}!")
    return 42


@on_event("hello")
async def owo(_, event: str):
    print(f"owo {event!r}!")
    return 1


@on_event("hello")
async def hi(_, event: str):
    print(f"Hello {event!r}!")


async def main():
    print("Firing blocking event 'hello'")
    assert await emit("hello") == [42, 1, None]
    print("Handlers for event 'hello' have exited")


if __name__ == "__main__":
    asyncio.run(main())
