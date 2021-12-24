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
from enum import Enum, auto, EnumMeta


class ContainsEnumMeta(EnumMeta):
    """
    Simple metaclass that implements
    the item in self operation
    """

    def __contains__(cls, item):
        try:
            cls(item)
        except ValueError:
            return False
        else:
            return True


class ExceptionHandling(Enum, metaclass=ContainsEnumMeta):
    """
    Flags that control how exceptions
    are handled in asyncevents. Note that,
    following Python's conventions, only
    subclasses of Exception are caught.
    Any subclass of BaseException is ignored
    as exceptions deriving directly from it,
    aside from Exception itself, are not meant
    to be caught
    """

    IGNORE: "ExceptionHandling" = auto()  # The exception is caught and ignored
    LOG: "ExceptionHandling" = auto()  # The exception is caught and logged
    PROPAGATE: "ExceptionHandling" = auto()  # The exception is not caught at all


class UnknownEventHandling(Enum, metaclass=ContainsEnumMeta):
    """
    Flags that control how the event emitter
    handles events for which no task has been
    registered. Note that this only applies to the
    emit and the wait methods, and not to
    register_handler/unregister_handler
    """

    IGNORE: "UnknownEventHandling" = auto()  # Do nothing
    LOG: "UnknownEventHandling" = auto()  # Log it as a warning
    ERROR: "UnknownEventHandling" = auto()  # raise an UnknownEvent error


class ExecutionMode(Enum, metaclass=ContainsEnumMeta):
    """
    Flags that control how the event emitter
    spawns tasks
    """

    PAUSE: "ExecutionMode" = auto()  # Spawn tasks via "await"
    NOWAIT: "ExecutionMode" = auto()  # Use asyncio.create_task
