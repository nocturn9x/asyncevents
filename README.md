# asyncevents - Asynchronous event handling for modern Python

asyncevents is a small library to help developers perform asynchronous event handling in modern Python code.

## Features

- Priority queueing to allow for deterministic event triggering (with a catch, see below)
- Built-in exception handling (optional)
- The public API is fully type hinted for those sweet, sweet editor suggestions
- Public API is fully documented (and some private stuff too): you could write this from scratch in a couple of hours (like I did)
- Very small (~200 CLOC), although it can't fit on a postcard
- Oneshot events (i.e. fired only once)


## Must Read
- Deterministic event handling can only occur in blocking mode, i.e. when a call to `emit()` blocks until
  all event handlers have run. If the non-blocking mode is used, handlers are started according to their priority, 
  but there's no telling on how they will be further scheduled to run and that depends entirely on the underlying
  asyncio event loop
- When using `oneshot=True`, the handler is unscheduled _before_ it is first run: this ensures a consistent behavior
  between blocking and non-blocking mode.
- An exception in one event handler does not cause the others to be cancelled when using non-blocking mode. In blocking
  mode, if an error occurs in one handler, and it propagates, then the handlers after it are not started
- Exceptions in custom exception handlers are not caught
- When using non-blocking mode, exceptions are kind of a mess due to how asyncio works: They are only delivered once
  you `wait()` for an event (same for log messages). This allows spawning many events and only having to worry about 
  exceptions in a single point in your code, but it also means you have less control over how the handlers run: if an
  error occurs in one handler, it will be raised once you call `wait()` but any other error in other handlers will
  be silently dropped

## Limitations

- Only compatible with asyncio due to the fact that other libraries such as trio and curio have wildly different design
  goals (structured concurrency, separation of environments, etc.), which makes implementing some functionality
  (i.e. the `wait()` method) tricky, if not outright impossible. Also those libraries, especially trio, already have
  decent machinery to perform roughly what asyncevent does
- Does not support using any other loop than the currently running one because of some subtleties of modern asyncio
  wrappers like `asyncio.run()` which creates its own event loop internally (_Thanks, asyncio_)

## Why?

This library exists because the current alternatives either suck, lack features or are inspired by other languages'
implementations of events like C# and Node.js: asyncevents aims to be a fully Pythonic library that provides you the
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
    # When using blocking _mode, asyncevents even guarantees that handlers
    # with different priorities will be executed in order
    print("Firing non-blocking event 'hi'")
    await emit("hi", block=False)  # This one spawns hi() and returns immediately
    print("Non-blocking event 'hi' fired")
    await emit("event3")  # Does nothing: No handlers registered for event3!
    # We wait now for the the handler of the "hi" event to complete
    t = time.time()
    print("Waiting on event 'hi'")
    await wait("hi")  # Waits until all the handlers triggered by the "hi" event exit
    print(f"Waited for {time.time() - t:.2f} seconds")  # Should print roughly 5 seconds


if __name__ == "__main__":
    asyncio.run(main())
```

__Note__: This example showed that the event names match the functions' names: this is just for explanatory purposes!
It's not compulsory for your event and their respective handlers' names to match. You can also register as many
functions you want for the same or multiple events and asyncevents will call them all when one of them is fired.
For more usage examples (until the documentation is done), check out the tests directory or read the source code:
it's pretty straightforward, I promise.

## TODOs

- Documentation
- More tests
- Trio/curio backend (maybe)
