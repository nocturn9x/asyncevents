# Copyright (C) 2021 nocturn9x
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#    http://www.apache.org/licenses/LICENSE-2.0
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
import asyncio
import inspect
import sys
import time
from collections import defaultdict
from heapq import heappush, heapify, heappop
from logging import Logger, getLogger, INFO, Formatter, StreamHandler
from typing import Dict, List, Tuple, Coroutine, Callable, Any, Awaitable, Optional
from typing import Union  # Separate line because it's gonna be deprecated soon. Can't break Justin's userbot tho :>

from asyncevents.constants import ExceptionHandling, UnknownEventHandling, ExecutionMode
from asyncevents.errors import UnknownEvent


class AsyncEventEmitter:
    """
    A simple priority-based asynchronous event emitter. In contrast to a scheduler, which
    continuously runs in the background orchestrating execution of tasks, an emitter runs
    only when an event is emitted and it only runs the tasks that are meant to catch said
    event, if any.

    :param on_error: Tells the emitter what to do when an exception occurs inside an event
        handler. This value can either be an entry from the asyncevents.ExceptionHandling
        enum or a coroutine function. If the passed object is a coroutine function, it is awaited
        whenever an exception is caught with the AsyncEventEmitter instance, the exception
        object and the event name as arguments (errors from the exception handler itself are
        not caught). Defaults to ExceptionHandling.PROPAGATE, which lets exceptions fall trough
        the execution chain (other enum values are LOG, which prints a log message on the
        logging.ERROR level, and IGNORE which silences the exception entirely)
    :type on_error: Union[ExceptionHandling, Callable[[AsyncEventEmitter, Exception, str], Coroutine[Any, Any, Any]]],
        optional
    :param on_unknown_event: Tells the emitter what to do when an unknown event is triggered. An
        unknown event is an event for which no handler is registered (either because it has never
        been registered or because all of its handlers have been removed). This value can either be
        an entry from the asyncevents.UnknownEventHandling enum or a coroutine function. If the argument
        is a coroutine function, it is awaited with the AsyncEventEmitter instance and the event name as arguments.
        Defaults to UnknownEventHandling.IGNORE, which does nothing (other enum values are LOG, which
        prints a log message on the logging.WARNING level, and ERROR which raises an UnknownEvent exception)
    :type on_unknown_event: Union[UnknownEventHandling, Callable[[AsyncEventEmitter, str], Coroutine[Any, Any, Any]]],
        optional
    :param mode: Tells the emitter how event handlers should be spawned. It should be an entry of the
        the asyncevents.ExecutionMode enum. If it is set to ExecutionMode.PAUSE, the default, the event
        emitter spawns tasks by awaiting each matching handler: this causes it to pause on every handler.
        If ExecutionMode.NOWAIT is used, the emitter uses asyncio.create_task to spawns all the handlers
        at the same time (note though that using this mode kind of breaks the priority queueing: the handlers
        are started according to their priorities, but once they are started they are handled by asyncio's
        event loop which is non-deterministic, so expect some disorder). Using ExecutionMode.NOWAIT allows
        to call the emitter's wait() method, which pauses until all currently running event handlers have
        completed executing (when ExecutionMode.PAUSE is used, wait() is a no-op)
    :type mode: ExecutionMode
    """

    async def _check_event(self, event: str):
        """
        Performs checks about the given event
        and raises/logs appropriately before
        emitting/waiting on it

        :param event: The event name
        :type event: str
        """

        if not self.handlers.get(event):
            if self.on_unknown_event == UnknownEventHandling.IGNORE:
                return
            elif self.on_unknown_event == UnknownEventHandling.ERROR:
                raise UnknownEvent(f"unknown event {event!r}")
            elif self.on_unknown_event == UnknownEventHandling.LOG:
                self.logger.warning(f"Attempted to emit or wait on an unknown event {event!r}")
            else:
                # It's a coroutine! Call it
                await self.on_unknown_event(self, event)

    async def _handle_errors_in_awaitable(self, event: str, obj: Awaitable) -> Any:
        # Thanks to asyncio's *utterly amazing* (HUGE sarcasm there)
        # exception handling, we have to make this wrapper so we can
        # catch errors on a per-handler basis
        try:
            return await obj
        except Exception as e:
            if (event, obj) in self._tasks:
                obj: asyncio.Task  # Silences PyCharm's warnings
                self._tasks.remove((event, obj))
            if inspect.iscoroutinefunction(self.on_error):
                await self.on_error(self, e, event)
            elif self.on_error == ExceptionHandling.PROPAGATE:
                raise
            elif self.on_error == ExceptionHandling.LOG:
                self.logger.error(f"An exception occurred while handling {event!r}: {type(e).__name__} -> {e}")
            # Note how the IGNORE case is excluded: we just do nothing after all

    # Implementations for emit()

    async def _emit_nowait(self, event: str, *args, **kwargs):
        # This implementation of emit() returns immediately
        # and runs the handlers in the background
        await self._check_event(event)
        temp: List[Tuple[int, float, Callable[["AsyncEventEmitter", str, ...], Coroutine[Any, Any, Any]], bool]] = []
        t: Tuple[int, float, Callable[["AsyncEventEmitter", str, ...], Coroutine[Any, Any, Any]], bool]
        while self.handlers[event]:
            # We use heappop because we want the first
            # by priority and the heap queue only has
            # the guarantee we need for heap[0]
            temp.append(heappop(self.handlers[event]))
            t = temp[-1]
            if t[-1]:
                # It won't be re-scheduled
                temp.pop()
            task = asyncio.create_task(t[-2](self, event, *args, **kwargs))
            self._tasks.append((event, asyncio.create_task(self._handle_errors_in_awaitable(event, task))))
        # We push back the elements
        for t in temp:
            heappush(self.handlers[event], t)

    async def _emit_await(self, event: str, *args, **kwargs) -> List[Any]:
        # This implementation of emit() returns only after
        # all handlers have finished executing
        await self._check_event(event)
        result = []
        temp: List[
            Tuple[int, float, Callable[["AsyncEventEmitter", str, ...], Coroutine[Any, Any, Any]], bool]
        ] = self.handlers[event].copy()
        t: Tuple[int, float, Callable[["AsyncEventEmitter", str, ...], Coroutine[Any, Any, Any]], bool]
        while temp:
            # We use heappop because we want the first
            # by priority and the heap queue only has
            # the guarantee we need for heap[0]
            t = heappop(temp)
            if t[-1]:
                self.unregister_handler(event, t[-2])
            result.append(await self._handle_errors_in_awaitable(event, t[-2](self, event, *args, **kwargs)))
        return result

    def __init__(
        self,
        # These type hints come from https://stackoverflow.com/a/59177557/12159081
        # and should correctly hint a coroutine function
        on_error: Union[
            ExceptionHandling, Callable[["AsyncEventEmitter", Exception, str], Coroutine[Any, Any, Any]]
        ] = ExceptionHandling.PROPAGATE,
        on_unknown_event: Union[
            UnknownEventHandling, Callable[["AsyncEventEmitter", str, ...], Coroutine[Any, Any, Any]]
        ] = UnknownEventHandling.IGNORE,
        mode: ExecutionMode = ExecutionMode.PAUSE,
    ):
        """
        Public object constructor
        """

        self.on_error = on_error
        self.on_unknown_event = on_unknown_event
        self.mode = mode
        self.logger: Logger = getLogger("asyncevents")
        self.logger.handlers = []
        self.logger.setLevel(INFO)
        handler: StreamHandler = StreamHandler(sys.stderr)
        handler.setFormatter(Formatter(fmt="[%(levelname)s - %(asctime)s] %(message)s", datefmt="%d/%m/%Y %H:%M:%S %p"))
        self.logger.addHandler(handler)
        # Stores asyncio tasks so that wait() can call
        # asyncio.gather() on them
        self._tasks: List[Tuple[str, asyncio.Task]] = []
        # Stores events and their priorities. Each
        # entry in the dictionary is a (name, handlers)
        # tuple where name is a string and handlers is
        # list of tuples. Each tuple in the list contains
        # a priority (defaults to 0), the insertion time of
        # when the handler was registered (to act as a tie
        # breaker for tasks with identical priorities or
        # when priorities aren't used at all) a coroutine
        # function object and a boolean that signals if the
        # handler is to be deleted after it fires the first
        # time (aka 'oneshot')
        self.handlers: Dict[
            str, List[Tuple[int, float, Callable[["AsyncEventEmitter", str, ...], Coroutine[Any, Any, Any]], bool]]
        ] = defaultdict(list)

    @property
    def on_error(self) -> Union[ExceptionHandling, Callable[["AsyncEventEmitter", str, ...], Coroutine[Any, Any, Any]]]:
        """
        Property getter for on_error
        """

        return self._on_error

    @on_error.setter
    def on_error(
        self, on_error: Union[ExceptionHandling, Callable[["AsyncEventEmitter", str, ...], Coroutine[Any, Any, Any]]]
    ):
        """
        Property setter for on_error

        :param on_error: Tells the emitter what to do when an exception occurs inside an event
        handler. This value can either be an entry from the asyncevents.ExceptionHandling
        enum or a coroutine function. If the passed object is a coroutine function, it is awaited
        whenever an exception is caught with the AsyncEventEmitter instance, the exception
        object and the event name as arguments (errors from the exception handler itself are
        not caught). Defaults to ExceptionHandling.PROPAGATE, which lets exceptions fall trough
        the execution chain (other enum values are LOG, which prints a log message on the
        logging.ERROR level, and IGNORE which silences the exception entirely)
        :type on_error: Union[ExceptionHandling, Callable[[AsyncEventEmitter, Exception, str], Coroutine[Any, Any, Any]]],
        optional
        :raises:
            TypeError: If the provided handler is not valid
        """

        if not inspect.iscoroutinefunction(on_error) and on_error not in ExceptionHandling:
            if inspect.iscoroutine(on_error):
                raise TypeError(
                    "on_error should be a coroutine *function*, not a coroutine! Pass the function"
                    " object without calling it!"
                )
            raise TypeError(
                "expected on_error to be a coroutine function or an entry from the ExceptionHandling"
                f" enum, found {type(on_error).__name__!r} instead"
            )
        self._on_error = on_error

    @property
    def on_unknown_event(
        self,
    ) -> Union[UnknownEventHandling, Callable[["AsyncEventEmitter", str, ...], Coroutine[Any, Any, Any]]]:
        """
        Property getter for on_unknown_event
        """

        return self._on_unknown_event

    @on_unknown_event.setter
    def on_unknown_event(
        self,
        on_unknown_event: Union[
            UnknownEventHandling, Callable[["AsyncEventEmitter", str, ...], Coroutine[Any, Any, Any]]
        ] = UnknownEventHandling.IGNORE,
    ):
        """
        Property setter for on_unknown_event

        :param on_unknown_event: Tells the emitter what to do when an unknown event is triggered. An
        unknown event is an event for which no handler is registered (either because it has never
        been registered or because all of its handlers have been removed). This value can either be
        an entry from the asyncevents.UnknownEventHandling enum or a coroutine function. If the argument
        is a coroutine function, it is awaited with the AsyncEventEmitter instance and the event name as arguments.
        Defaults to UnknownEventHandling.IGNORE, which does nothing (other enum values are LOG, which
        prints a log message on the logging.WARNING level, and ERROR which raises an UnknownEvent exception)
        Note: if the given callable is a coroutine, it is awaited, while it's called normally otherwise
        and its return value is discarded
        :type on_unknown_event: Union[UnknownEventHandling, Callable[[AsyncEventEmitter, str], Coroutine[Any, Any, Any]]],
        optional
        :raises:
            TypeError: If the provided handler is not valid
        """

        if not inspect.iscoroutinefunction(on_unknown_event) and on_unknown_event not in UnknownEventHandling:
            if inspect.iscoroutine(on_unknown_event):
                raise TypeError(
                    "on_unknown_event should be a coroutine *function*, not a coroutine! Pass the function"
                    " object without calling it!"
                )
            raise TypeError(
                "expected on_unknown_event to be a coroutine function or an entry from the"
                f" UnknownEventHandling enum, found {type(on_unknown_event).__name__!r} instead"
            )
        self._on_unknown_event = on_unknown_event

    @property
    def mode(self):
        """
        Property getter for mode
        """
        return self._mode

    @mode.setter
    def mode(self, mode: ExecutionMode):
        """
        Property setter for mode

        :param mode: Tells the emitter how event handlers should be spawned. It should be an entry of the
        the asyncevents.ExecutionMode enum. If it is set to ExecutionMode.PAUSE, the default, the event
        emitter spawns tasks by awaiting each matching handler: this causes it to pause on every handler.
        If ExecutionMode.NOWAIT is used, the emitter uses asyncio.create_task to spawns all the handlers
        at the same time (note though that using this mode kind of breaks the priority queueing: the handlers
        are started according to their priorities, but once they are started they are handled by asyncio's
        event loop which is non-deterministic, so expect some disorder). Using ExecutionMode.NOWAIT allows
        to call the emitter's wait() method, which pauses until all currently running event handlers have
        completed executing (when ExecutionMode.PAUSE is used, wait() is a no-op), but note that return
        values from event handlers are not returned
        :type mode: ExecutionMode
        :raises:
            TypeError: If the given mode is invalid
        """

        if mode not in ExecutionMode:
            raise TypeError(
                f"expected mode to be an entry from the ExecutionMode enum, found {type(mode).__name__!r}" " instead"
            )
        self._mode = mode

    def exists(self, event: str) -> bool:
        """
        Returns if the given event has at least
        one handler registered

        :param event: The event name
        :type event: str
        :return: True if the event has at least one handler,
            False otherwise
        """

        return len(self.handlers.get(event)) > 0

    def register_event(
        self,
        event: str,
        handler: Callable[["AsyncEventEmitter", str, ...], Coroutine[Any, Any, Any]],
        priority: int = 0,
        oneshot: bool = False,
    ):
        """
        Registers an event and its associated handler. If
        the event is already registered, the given handler
        is added to the already existing handler queue. Each
        event will be called with the AsyncEventEmitter instance
        that triggered the event as well as the event name itself

        :param event: The event name
        :type event: str
        :param handler: A coroutine function to be called
            when the event is generated
        :type handler: Callable[["AsyncEventEmitter", str, ...], Coroutine[Any, Any, Any]]
        :param priority: The handler's execution priority,
            defaults to 0 (lower priority means earlier
            execution!)
        :type priority: int, optional
        :param oneshot: If True, the event is unregistered after if fires the first time,
             defaults to False
        :type oneshot: bool, optional
        """

        heappush(self.handlers[event], (priority, time.monotonic(), handler, oneshot))

    def unregister_event(self, event: str):
        """
        Unregisters all handlers for the given
        event in one go. Does nothing if the
        given event is not registered already.
        Note that this does not affect any
        already started event handler for the
        given event

        :param event: The event name
        :type event: str
        """

        self.handlers.pop(event, None)

    def _get(
        self, event: str, handler: Callable[["AsyncEventEmitter", str, ...], Coroutine[Any, Any, Any]]
    ) -> Union[
        None, bool, Tuple[int, float, Callable[["AsyncEventEmitter", str, ...], Coroutine[Any, Any, Any]], bool]
    ]:
        """
        Returns the tuple of (priority, date, corofunc, oneshot) representing the
        given handler. Only the first matching entry is returned. False is returned
        if the given handler is not registered for the given event.

        Note: This method is meant mostly for internal use

        :param event: The event name
        :type event: str
        :param handler: A coroutine function to be called
            when the event is generated
        :type handler: Callable[["AsyncEventEmitter", str, ...], Coroutine[Any, Any, Any]]
        :raises:
            UnknownEvent: If self.on_unknown_error == UnknownEventHandling.ERROR
        :returns: The tuple of (priority, date, coro) representing the
            given handler
        """

        if not self.exists(event):
            return None
        for (priority, tie, corofunc, oneshot) in self.handlers[event]:
            if corofunc == handler:
                return priority, tie, corofunc, oneshot
        return False

    def unregister_handler(
        self,
        event: str,
        handler: Callable[["AsyncEventEmitter", str, ...], Coroutine[Any, Any, Any]],
        remove_all: bool = False,
    ):
        """
        Unregisters a given handler for the given event. If
        remove_all is True (defaults to False), all occurrences
        of the given handler are removed, otherwise only the first
        one is unregistered. Does nothing if the given event is not
        registered already. This method does nothing if the given 
        event exists, but the given handler is not registered for it

        :param event: The event name
        :type event: str
        :param handler: The coroutine function to be unregistered
        :type handler: Callable[["AsyncEventEmitter", str, ...], Coroutine[Any, Any, Any]]
        :param remove_all: If True, all occurrences of the
            given handler are removed, otherwise only the first
            one is unregistered
        :type remove_all: bool, optional
        :raises:
            UnknownEvent: If self.on_unknown_error == UnknownEventHandling.ERROR
        :return:
        """

        if remove_all:
            for (priority, tie, coro, oneshot) in self.handlers[event]:
                if handler == coro:
                    self.handlers[event].remove((priority, tie, coro, oneshot))
        else:
            if t := self._get(event, handler):
                self.handlers[event].remove(t)
        # We maintain the heap queue invariant
        heapify(self.handlers[event])

    async def wait(self, event: Optional[str] = None) -> List[Any]:
        """
        Waits until all the event handlers for the given
        event have finished executing. When the given event
        is None, the default, waits for all handlers of all
        events to terminate. This method is a no-op when the
        emitter is configured with anything other than
        ExecutionMode.NOWAIT or if emit() hasn't been called
        with block=False. Returns a list of all return values
        from the event handlers
        """

        if not event:
            result = [e for e in await asyncio.gather(*[t[1] for t in self._tasks])]
            self._tasks = []
            return result
        else:
            await self._check_event(event)
            result = [e for e in await asyncio.gather(*[t[1] for t in self._tasks if t[0] == event])]
            for t in self._tasks:
                if t[0] == event:
                    self._tasks.remove(t)
            return result

    async def emit(self, event: str, block: bool = True, *args, **kwargs) -> List[Any]:
        """
        Emits an event. Any extra positional and keyword arguments besides
        the event name and the "block" boolean are passed over to the
        event handlers themselves. Returns the values of the event
        handlers in a list when using blocking mode or an empty
        list otherwise

        :param event: The event to trigger. Note that,
            depending on the configuration, unknown events
            may raise errors or log to stderr
        :type event: str
        :param block: Temporarily overrides the emitter's global execution
            mode. If block is True, the default, this call will pause until
            execution of all event handlers has finished, otherwise it returns
            as soon as they're scheduled
        :type block: bool, optional
        :raises:
            UnknownEvent: If self.on_unknown_error == UnknownEventHandling.ERROR
                and the given event is not registered
        """

        mode = self._mode
        if block:
            self._mode = ExecutionMode.PAUSE
            result = await self._emit_await(event, *args, **kwargs)
        else:
            self._mode = ExecutionMode.NOWAIT
            await self._emit_nowait(event, *args, **kwargs)
            result = []
        self._mode = mode
        return result
