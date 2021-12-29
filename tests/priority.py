import asyncio
from asyncevents import on_event, emit, wait


@on_event("event")  # Priority defaults to 0, hence highest
async def first(_, event: str):
    print(f"Ran first for {event!r}!")


@on_event("event", priority=1)  # Higher number = lower priority
async def second(_, event: str):
    print(f"Ran second for {event!r}!")


@on_event("event", priority=1)  # You can add as many handlers as you want at a given priority level
async def also_second(_, event: str):
    print(f"Ran second too for {event!r}!")


@on_event("event", priority=2)  # Higher number = lower priority
async def third(_, event: str):
    print(f"Ran third for {event!r}!")


async def main():
    print("Firing blocking event 'event'")
    await emit("event")
    print("Handlers for event 'event' have exited")
    print("Firing non-blocking event 'event'")
    await emit("event", block=False)
    print("Non-blocking event 'event' fired, waiting on it")
    await wait("event")


if __name__ == "__main__":
    asyncio.run(main())
