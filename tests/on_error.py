import asyncio
from asyncevents import on_event, emit, get_current_emitter, ExceptionHandling


@on_event("error")
async def oh_no(_, event: str):
    print(f"Goodbye after {event!r}!")
    raise ValueError("D:")


async def handle_error(_, exc: Exception, event: str):
    print(f"Exception {type(exc).__name__!r} from {event!r} handled!")


async def main():
    try:
        await emit("error")  # The error propagates
    except ValueError:
        print("Bang!")
    # Now let's try a different error handling strategy
    get_current_emitter().on_error = ExceptionHandling.LOG  # Logs the exception
    await emit("error")  # This won't raise. Yay!
    print("We're safe!")
    # And a different one again
    get_current_emitter().on_error = ExceptionHandling.IGNORE  # Silences the exception
    await emit("error")  # This won't raise nor log anything to the console. Yay x2!
    print("We're safe again!")
    # Let's try using a coroutine function as an exception handler
    get_current_emitter().on_error = handle_error
    await emit("error")  # This will call handle_error with the exception object and the event name
    print("We're safe once again!")


if __name__ == "__main__":
    asyncio.run(main())
