import asyncio
from asyncevents import on_event, emit, get_current_emitter, UnknownEventHandling
from asyncevents.errors import UnknownEvent


@on_event("test")
@on_event("test2")
async def oh_no(_, event: str):
    print(f"The event {event!r} definitely exists!")


async def handle_unknown_event(_, event: str):
    print(f"The event {event!r} definitely does not exist!")


async def main():
    await emit("test")
    await emit("test2")
    await emit("test3")  # Does nothing by default
    get_current_emitter().on_unknown_event = UnknownEventHandling.LOG
    await emit("test3")  # Logs an error message
    get_current_emitter().on_unknown_event = UnknownEventHandling.ERROR  # Raises an exception
    try:
        await emit("test3")
    except UnknownEvent:
        print("Bang!")
    get_current_emitter().on_unknown_event = handle_unknown_event  # Calls the function with the event as argument
    await emit("test3")


if __name__ == "__main__":
    asyncio.run(main())
