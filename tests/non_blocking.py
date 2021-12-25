import time
import asyncio
from asyncevents import on_event, emit, wait


@on_event("hi")
async def hi(_, event: str):
    print(f"Hi {event!r}! I'm going to sleep for 5 seconds")
    await asyncio.sleep(5)  # Simulates some work


async def main():
    print("Emitting event 'hi'")
    await emit("hi", block=False)
    print("Event 'hi' fired")
    t = time.time()
    print("Waiting on event 'hi'")
    await wait("hi")
    print(f"Waited for {time.time() - t:.2f} seconds")


if __name__ == "__main__":
    asyncio.run(main())
