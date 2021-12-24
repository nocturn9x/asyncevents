# asyncevents - Asynchronous event handling for modern Python

asyncevents is a small library to help developers perform asynchronous event handling in modern Python code.

## Features

- Priority queueing to allow for deterministic event triggering (with a catch, see below)
- Built-in exception handling (optional)
- The public API is fully type hinted for those sweet, sweet editor suggestions
- Public API is fully documented (and some private stuff too): you could write this from scratch in a couple of hours (like I did)
- Very small (~200 CLOC), although it can't fit on a postcard


__Note__: Deterministic event handling can only occur in blocking mode, i.e. when a call to `emit()` blocks until
all event handlers have run. If the non-blocking mode is used, handlers are started according to their priority, 
but there's no telling on how they will be further scheduled to run and that depends entirely on the underlying
asyncio event loop

## Limitations

- Only compatible with asyncio due to the fact that other libraries such as trio and curio have wildly different design
  goals (structured concurrency, separation of environments, etc.), which makes implementing some functionality
  (i.e. the `wait()` method) tricky, if not outright impossible. Also those libraries, especially trio, already have
  decent machinery to perform roughly what asyncevent does
- Does not support using any other loop than the currently running one because of some subtleties of modern asyncio
  wrappers like `asyncio.run()` which creates its own event loop internally (_Thanks, asyncio_)
- Exceptions are kinda finicky in non-blocking mode due to how `asyncio.gather` works: only the first exception
  in a group of handlers is properly raised and log messages might get doubled. Also, exception logging and propagation
  is delayed until you `await wait("some_event")` so be careful
## Why?

This library exists because the current alternatives either suck, lack features or are inspired by other languages'
implementations of events like C# and Node.js: asyncevents aims to be a fully Pythonic library that provides just the
features you need and nothing more (nor nothing less).

## Cool! How do I use it?

Like this

```python3
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
```


## TODOs

- Documentation
- More tests
- Trio/curio backend (maybe)
