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
import functools
import threading
from asyncevents import events, errors
from typing import Any, Callable, Coroutine, Optional, List
from asyncevents.constants import ExceptionHandling, ExecutionMode, UnknownEventHandling

# Thread-local namespace for storing the currently
# used AsyncEventEmitter instance automatically
local_storage: threading.local = threading.local()
AsyncEventEmitter = events.AsyncEventEmitter


def get_current_emitter() -> AsyncEventEmitter:
    """
    Returns the currently active
    emitter in the current thread
    and creates a new one if one
    doesn't exist
    """

    if not hasattr(local_storage, "emitter"):
        local_storage.emitter = AsyncEventEmitter()
    return local_storage.emitter


def set_current_emitter(emitter: AsyncEventEmitter):
    """
    Sets the active emitter in the current thread.
    Discards the existing one, if it exists

    :param emitter: The new emitter to set
        for the current thread
    :type emitter: :class: AsyncEventEmitter
    """

    if not isinstance(emitter, AsyncEventEmitter) and not issubclass(type(emitter), AsyncEventEmitter):
        raise TypeError(
            "expected emitter to be an instance of AsyncEventEmitter or a subclass thereof,"
            f" found {type(emitter).__name__!r} instead"
        )
    local_storage.emitter = emitter


async def wait(event: Optional[str] = None) -> List[Any]:
    """
    Shorthand for get_current_emitter().wait()
    """

    return await get_current_emitter().wait(event)


async def emit(event: str, block: bool = True, *args, **kwargs) -> List[Any]:
    """
    Shorthand for get_current_emitter().emit(event, block)
    """

    return await get_current_emitter().emit(event, block, *args, **kwargs)


async def exists(event: str):
    """
    Shorthand for get_current_emitter().exists(event)
    """

    return get_current_emitter().exists(event)


def on_event(event: str, priority: int = 0, emitter: AsyncEventEmitter = get_current_emitter(), oneshot: bool = False):
    """
    Decorator shorthand of emitter.register_event(event, f, priority, oneshot)
    """

    def decorator(corofunc: Callable[[AsyncEventEmitter, str], Coroutine[Any, Any, Any]]):
        emitter.register_event(event, corofunc, priority, oneshot)

        @functools.wraps(corofunc)
        async def wrapper(*args, **kwargs):
            return await corofunc(*args, **kwargs)

        return wrapper

    return decorator


__all__ = [
    "events",
    "errors",
    "AsyncEventEmitter",
    "ExceptionHandling",
    "ExecutionMode",
    "UnknownEventHandling",
    "on_event",
    "emit",
    "wait",
    "exists",
    "get_current_emitter",
    "set_current_emitter",
]
