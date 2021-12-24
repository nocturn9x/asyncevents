import time
import asyncio
from asyncevents import on_event, emit, wait


@on_event("hello")
async def hello(_, event: str):
    print(f"Hello {event!r}!")


@on_event("hi")
async def hi(_, event: str):
    print(f"Hi {event!r}! I'm going to sleep for 5 seconds")
    await asyncio.sleep(5)  # Simulates some work


async def main():
    print("Firing blocking event 'hello'")
    await emit("hello")  # This call blocks until hello() terminates
    print("Handlers for event 'hello' have exited")
    # Notice how, until here, the output is in order: this is on purpose!
    # When using blocking mode, asyncevents even guarantees that handlers
    # with different priorities will be executed in order
    print("Firing blocking event 'hello'")
    await emit("hi", block=False)  # This one spawns hi() and returns immediately
    print("Non-blocking event 'hello' fired")
    await emit("event3")  # Does nothing: No handlers registered for event3!
    # We wait now for the the handler of the "hi" event to complete
    t = time.time()
    print("Waiting on event 'hi'")
    await wait("hi")  # Waits until all the handlers triggered by the "hi" event exit
    print(f"Waited for {time.time() - t:.2f} seconds")  # Should print roughly 5 seconds


if __name__ == "__main__":
    asyncio.run(main())
