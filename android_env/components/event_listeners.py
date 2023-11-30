# Copyright 2023 SJTU X-Lance Lab
# 
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
# 
#     http://www.apache.org/licenses/LICENSE-2.0
# 
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""
Created by Danyang Zhang @X-Lance.
"""

import abc
import re
import itertools
import functools
import enum

import lxml.cssselect as cssselect
from sentence_transformers import SentenceTransformer
from sentence_transformers.util import dot_score
from rapidfuzz import fuzz
from difflib import SequenceMatcher
import torch

from typing import Generic, TypeVar, Callable, Optional, Any, Union
from typing import Tuple, List, Pattern, Dict, Match
from typing import Iterable, ClassVar

from absl import logging

# The whole data flow for the event flag classes:
# value -> verification -> transform -> wrap -> update
#        \______________/ \__________________________/
#         in EventSource          in EventSlot

I = TypeVar("Input")
V = TypeVar("Verified")
C = TypeVar("Cast")
T = TypeVar("Transformed")
W = TypeVar("Wrapped")

class Event(abc.ABC, Generic[W]):
    #  abstract class `Event` {{{ # 
    #def __init__(self,
            #transformation: Optional[str] = None,
            #cast: Optional[Callable[[V], C]] = None,
            #wrap: Optional[Callable[[T], W]] = None,
            #update: Optional[Callable[[W, W], W]] = None):
        ##  method `__init__` {{{ # 
        #"""
        #transformation - str representing a python expression that can be
          #evaluated by `eval` function or None for a default identity mapping.
          #"x" should be used to indicate the input variable. `x` could be a
          #scalar or a list.
        #cast - callable accepting the verified type returning the cast type or
          #None
        #wrap - callable accepting the transformed type returning the wrapped
          #type or None
        #update - callable accepting
          #+ the wrapped type
          #+ the wrapped type
          #and returning the wrapped type
        #"""
#
        #self._transformation_str: Optional[str] = transformation
        #self._cast: Callable[[V], C] = cast or (lambda x: x)
        #self._wrap: Callable[[T], W] = wrap or (lambda x: x)
        #update = update or (lambda x, y: y)
        #self._update: Callable[[Optional[W], W], W] = lambda x, y: update(x, y) if x is not None else y
#
        #self._flag_cache: bool = False
        #self._value_cache: Optional[W] = None
#
        #self._ever_set: bool = False
        #self._prerequisites: List[Event] = []
        ##  }}} method `__init__` # 

    #@abc.abstractmethod
    #def set(self, value: I):
        #"""
        #value - the input type
        #"""
#
        #raise NotImplementedError()
    @abc.abstractmethod
    def is_set(self) -> bool:
        """
        return bool
        """

        raise NotImplementedError()
    @abc.abstractmethod
    def get(self) -> List[W]:
        """
        return list of the wrapped type
        """

        raise NotImplementedError()
    @abc.abstractmethod
    def is_ever_set(self) -> bool:
        """
        return bool
        """

        raise NotImplementedError()
    @abc.abstractmethod
    def reset(self):
        raise NotImplementedError()
#
    #@abc.abstractmethod
    #def _clear(self):
        #raise NotImplementedError()
#
    #def get_cache(self) -> Tuple[bool, Optional[W]]:
        ##  method `get_cache` {{{ # 
        #return self._flag_cache, self._value_cache
        ##  }}} method `get_cache` # 
    #def clear_cache(self):
        ##  method `clear_cache` {{{ # 
        #self._flag_cache = False
        #self._value_cache = False
        #self._clear_cache()
        ##  }}} method `clear_cache` # 
    #@abc.abstractmethod
    #def _clear_cache(self):
        #raise NotImplementedError()
    #  }}} abstract class `Event` # 

class Repeatability(enum.IntEnum):
    NONE = 0
    LAST = 1
    UNLIMITED = 2

class EventSource(Event[V], abc.ABC, Generic[I, V]):
    #  abstract class `EventSource` {{{ # 
    def __init__(self,
            #transformation: Optional[str] = None,
            #cast: Optional[Callable[[V], C]] = None,
            #wrap: Optional[Callable[[T], W]] = None,
            #update: Optional[Callable[[W, W], W]] = None,
            repeatability: Repeatability = Repeatability.NONE):
        #  method `__init__` {{{ # 
        """
        #transformation - str representing a python expression that can be
          #evaluated by `eval` function or None for a default identity mapping.
          #"x" should be used to indicate the input variable. `x` could be a
          #scalar or a list.
        #cast - callable accepting the verified type returning the cast type or
          #None
        #wrap - callable accepting the transformed type returning the wrapped
          #type or None
        #update - callable accepting
          #+ the wrapped type
          #+ the wrapped type
          #and returning the wrapped type
        repeatability - Repeatability
        """

        super(EventSource, self).__init__()

        self._repeatability: Repeatability = repeatability
        self._last_input: I = None # the last input, both activating and not activating
        self._input_history: List[I] = [] # history list of the activating inputs

        self._flag: bool = False
        self._value: List[V] = []

        self._flag_cache: bool = False
        self._value_cache: List[V] = []

        self._ever_set: bool = False
        #  }}} method `__init__` # 

    def set(self, value: I):
        #  method `set` {{{ # 
        """
        value - the input type
        """

        #if any(map(lambda evt: not evt.is_ever_set(), self._prerequisites)):
            #return

        if self._repeatability==Repeatability.NONE and value in self._input_history or\
                self._repeatability==Repeatability.LAST and value == self._last_input:
            return
        self._last_input = value

        is_validate, value_ = self._verify(value)
        if is_validate:
            self._input_history.append(value)

            #value_ = self._transform(value_)
            #value_ = self._wrap(value_)
            #self._value = self._update(self._value, value_)
            self._value.append(value_)

            self._flag = True
            self._ever_set = True
        #  }}} method `set` # 
    @abc.abstractmethod
    def _verify(self, value: I) -> Tuple[bool, Optional[V]]:
        #  abstract method `_verify` {{{ # 
        """
        This is a hook function for the extenders to implement.

        value - the input type

        return
        - bool
        - the verified type
        """

        raise NotImplementedError()
        #  }}} abstract method `_verify` # 

    def snapshot(self):
        #  method `snapshot` {{{ # 
        self._flag_cache = self._flag
        self._value_cache = self._value
        self._flag = False
        self._value = []
        #  }}} method `snapshot` # 
    def is_set(self) -> bool:
        return self._flag_cache
    def get(self) -> List[W]:
        #  method `get` {{{ # 
        """
        return lsit the wrapped type
        """

        return self._value_cache if self.is_set() else []
        #  }}} method `get` # 
    def clear(self):
        #  method `clear` {{{ # 
        self._flag_cache = False
        self._value_cache = []
        #  }}} method `clear` # 

    def is_ever_set(self) -> bool:
        return self._ever_set
    def reset(self):
        self._ever_set = False
        self._input_history = []
        self._last_input = None
    #  }}} abstract class `EventSource` # 

class EventSlot(Event[W], abc.ABC, Generic[V, T, W]):
    #  abstract class `EventSlot` {{{ # 
    def __init__( self
                , sources: Iterable[Event[V]]
                , transformation: Optional[List[str]] = None
                , wrap: Optional[Callable[[T], W]] = None
                , update: Optional[Callable[[W, W], W]] = None
                , repeatability: Repeatability = Repeatability.UNLIMITED
                ):
        #  method `__init__` {{{ # 
        """
        Args:
            sources: iterable of Event
            transformation: list of str or None
            wrap: callable accepting the transformed type returning the wrapped
              type or None
            update: callable accepting
              + the wrapped type
              + the wrapped type
              and returning the wrapped type
            repeatability (Repeatability): repeatability
        """

        super(EventSlot, self).__init__()

        self._sources: List[Event[V]] = list(sources)

        #self._cast: Callable[[V], C] = cast or (lambda x: x)
        self._transformation_str: List[str] = transformation or []
        if len(self._transformation_str)==0:
            self._transformation_str.append("y = x")
        self._wrap: Callable[[T], W] = wrap or (lambda x: x)
        update = update or (lambda x, y: y)
        #self._update: Callable[[Optional[W], W], W] = lambda x, y: update(x, y) if x is not None else y
        self._update: Callable[[W, W], W] = update

        self._repeatability: Repeatability = repeatability
        self._last_set: bool = False
        self._set: bool = False
        self._new_step: bool = True

        self._ever_set: bool = False
        self._prerequisites: List[Event] = []
        #  }}} method `__init__` # 
    def replace_sources(self, index: int, source: Event):
        #  method `append_sources` {{{ # 
        self._sources[index] = source
        #  }}} method `append_sources` # 

    def _transform(self, x: Union[V, List[V]]) -> T:
        #  method `_transformation` {{{ # 
        """
        x - the same type as `self._value` or list of instances of type of
          `self._value`

        return something
        """

        #try:
            #x = list(map(self._cast, x0)) if hasattr(x0, "__iter__") else self._cast(x0)
        #except:
            #x = x0
        #return eval(self._transformation_str) if self._transformation_str else x
        local_env = {"x": x}
        for cmmd in self._transformation_str:
            #logging.info("\x1b[1;33m{:}\x1b[0m".format(cmmd))
            exec(cmmd, globals(), local_env)
        return local_env["y"]
        #  }}} method `_transformation` # 

    def add_prerequisites(self, *prerequisites: Iterable[Event]):
        #  method `add_prerequisites` {{{ # 
        """
        prerequisites - iterable of Event
        """

        self._prerequisites += prerequisites
        #  }}} method `add_prerequisites` # 
    def _satisfies_prerequisites(self) -> bool:
        return all(map(lambda evt: evt.is_ever_set(), self._prerequisites))

    def set_new_step(self):
        self._new_step = True
        for evt in self._sources:
            if hasattr(evt, "set_new_step"):
                evt.set_new_step()

    def is_set(self):
        #  method `is_set` {{{ # 
        if self._new_step:
            if not self._satisfies_prerequisites():
                self._set = False
            elif self._is_set():
                if self._repeatability==Repeatability.UNLIMITED:
                    set_: bool = True
                elif self._repeatability==Repeatability.LAST:
                    set_: bool = not self._last_set
                else:
                    set_: bool = not self._ever_set
                self._ever_set = True
                self._last_set = True
                self._set = set_
            else:
                self._set = False
        self._new_step = False
        return self._set
        #  }}} method `is_set` # 
    @abc.abstractclassmethod
    def _is_set(self) -> bool:
        #  method `_is_set` {{{ # 
        raise NotImplementedError()
        #  }}} method `_is_set` # 

    def get(self) -> List[W]:
        #  method `get` {{{ # 
        """
        return list of the wrapped type
        """

        if not self.is_set():
            return []
        return self._get()
        #  }}} method `get` # 
    @abc.abstractclassmethod
    def _get(self) -> List[W]:
        raise NotImplementedError()

    def is_ever_set(self) -> bool:
        if not self._ever_set:
            return self.is_set()
        return True
    def reset(self):
        #  method `reset` {{{ # 
        self._ever_set = False
        self._last_set = False
        self._set = False
        for evt in self._sources:
            evt.reset()
        #  }}} method `reset` # 
    #  }}} abstract class `EventSlot` # 

class EmptyEvent(EventSlot[None, None, None]):
    #  class `EmptyEvent` {{{ # 
    def __init__(self):
        super(EmptyEvent, self).__init__([])
    def _is_set(self) -> bool:
        return False
    def _get(self) -> List[None]:
        return []
    #  }}} class `EmptyEvent` # 

class DefaultEvent(EventSlot[V, T, W]):
    #  class `DefaultEvent` {{{ # 
    def __init__( self
                , sources: List[Event[V]]
                , transformation: Optional[List[str]] = None
                , wrap: Optional[Callable[[T], W]] = None
                , update: Optional[Callable[[W, W], W]] = None
                , repeatability: Repeatability = Repeatability.UNLIMITED
                ):
        #  method `__init__` {{{ # 
        """
        Args:
            sources: iterable of Event
            transformation: list of str or None
            wrap: callable accepting the transformed type returning the wrapped
              type or None
            update: callable accepting
              + the wrapped type
              + the wrapped type
              and returning the wrapped type
            repeatability (Repeatability): repeatability
        """

        super(DefaultEvent, self).__init__(sources, transformation, wrap, update, repeatability)
        #  }}} method `__init__` # 

    def _is_set(self) -> bool:
        #  method `_is_set` {{{ # 
        """
        return bool
        """

        return len(self._sources)>0 and self._sources[0].is_set()
        #  }}} method `_is_set` # 

    def _get(self) -> List[W]:
        source_values = self._sources[0].get()
        return [functools.reduce(self._update,
                    map(self._wrap,
                        map(self._transform,
                            source_values)))]
    #  }}} class `DefaultEvent` # 

class Or(EventSlot[V, T, W]):
    #  class `Or` {{{ # 
    def __init__( self
                , events: Iterable[Event[V]]
                , transformation: Optional[List[str]] = None
                , wrap: Optional[Callable[[T], W]] = None
                , update: Optional[Callable[[W, W], W]] = None
                , repeatability: Repeatability = Repeatability.UNLIMITED
                ):
        #  method `__init__` {{{ # 
        """
        Args:
            sources: iterable of Event
            transformation: list of str or None
            wrap: callable accepting the transformed type returning the wrapped
              type or None
            update: callable accepting
              + the wrapped type
              + the wrapped type
              and returning the wrapped type
            repeatability (Repeatability): repeatability
        """

        #update = update or (lambda x, y: x)
        super(Or, self).__init__(events, transformation, wrap, update, repeatability)

        #self._events: List[Event[Any, Any, Any, Any, V]] = list(events)
        #  }}} method `__init__` # 

    def _is_set(self) -> bool:
        #  method `_is_set` {{{ # 
        """
        return bool
        """

        return any(map(lambda x: x.is_set(), self._sources))
        #  }}} method `_is_set` # 

    def _get(self) -> List[W]:
        #  method `_get` {{{ # 
        """
        return list of the wrapped type
        """

        return [functools.reduce(self._update,
                    map(self._wrap,
                        map(self._transform,
                            itertools.chain.from_iterable(
                                map(lambda evt: evt.get(),
                                    self._sources)))))]
        #value = None
        #is_set = False
        #for evt in self._events:
            #if evt.is_set():
                #is_set = True
                #self._ever_set = True
                #value = self._update(value, self._wrap(self._transform(evt.get())))
        #return value if is_set else None
        #  }}} method `_get` # 
    #  }}} class `Or` # 

class And(EventSlot[V, T, W]):
    #  class `And` {{{ # 
    def __init__( self
                , events: Iterable[Event[V]]
                , transformation: Optional[List[str]] = None
                , wrap: Optional[Callable[[T], W]] = None
                , repeatability: Repeatability = Repeatability.UNLIMITED
                ):
        #  method `__init__` {{{ # 
        """
        Args:
            sources: iterable of Event
            transformation: list of str or None
            wrap: callable accepting the transformed type returning the wrapped
              type or None
            update: callable accepting
              + the wrapped type
              + the wrapped type
              and returning the wrapped type
            repeatability (Repeatability): repeatability
        """

        super(And, self).__init__(events, transformation, wrap, repeatability)

        #self._events: List[Event[Any, Any, Any, Any, V]] = list(events)
        #  }}} method `__init__` # 

    def _is_set(self) -> bool:
        #  method `_is_set` {{{ # 
        """
        return bool
        """

        if len(self._sources)==0:
            return False
        return all(map(lambda x: x.is_set(), self._sources))
        #  }}} method `_is_set` # 

    def _get(self) -> List[W]:
        #  method `_get` {{{ # 
        """
        return list of the wrapped type
        """

        return [self._wrap(
                    self._transform(
                        list(
                            map(lambda x: x.get(),
                                self._sources))))]
        #  }}} method `_get` # 
    #  }}} class `And` # 

class RegionEvent(EventSource[I, V], abc.ABC):
    #  abstract class `RegionEvent` {{{ # 
    def __init__(self, region: Iterable[float], needs_detection: bool = False,
            #transformation: Optional[str] = None,
            #cast: Optional[Callable[[V], C]] = None,
            #wrap: Optional[Callable[[T], W]] = None,
            #update: Optional[Callable[[W, W], W]] = None,
            repeatability: Repeatability = Repeatability.NONE):
        #  method `__init__` {{{ # 
        """
        region - iterable of four floats as [x0, y0, x1, y1]
        needs_detection - bool
        #transformation - str of None
        #cast - callable accepting the verified type returning the cast type or
          #None
        #wrap - callable accepting the transformed type returning the wrapped
          #type or None
        #update - callable accepting
          #+ the wrapped type
          #+ the wrapped type
          #and returning the wrapped type
        repeatability - Repeatability
        """

        #super(RegionEvent, self).__init__(transformation, cast, wrap, update, repeatability)
        super(RegionEvent, self).__init__(repeatability)
        self._region: List[float] = list(itertools.islice(region, 4))
        self._needs_detection: bool = needs_detection
        #  }}} method `__init__` # 

    @property
    def region(self) -> List[float]:
        return self._region
    @property
    def needs_detection(self) -> bool:
        return self._needs_detection
    #  }}} abstract class `RegionEvent` # 

class TextEvent(RegionEvent[Optional[str], List[str]]):
    #  class `TextEvent` {{{ # 
    def __init__(self, expect: str,
            region: Iterable[float], needs_detection: bool = False,
            #transformation: Optional[str] = None,
            #cast: Optional[Callable[[str], C]] = None,
            #wrap: Optional[Callable[[T], W]] = None,
            #update: Optional[Callable[[W, W], W]] = None,
            repeatability: Repeatability = Repeatability.NONE):
        #  method `__init__` {{{ # 
        """
        expect - str
        region - iterable of four floats as [x0, y0, x1, y1]
        needs_detection - bool
        #transformation - str or None
        #cast - callable accepting the verified type returning the cast type or
          #None
        #wrap - callable accepting the transformed type returning the wrapped
          #type or None
        #update - callable accepting
          #+ the wrapped type
          #+ the wrapped type
          #and returning the wrapped type
        repeatability - Repeatability
        """

        #super(TextEvent, self).__init__(region, needs_detection, transformation, cast, wrap, update, repeatability)
        super(TextEvent, self).__init__(region, needs_detection, repeatability)

        self._expect: Pattern[str] = re.compile(expect)
        #  }}} method `__init__` # 

    def _verify(self, text: Optional[str]) -> Tuple[bool, Optional[List[str]]]:
        #  method `_verify` {{{ # 
        """
        text - str or None

        return bool, list of str or None
        """

        if text is None:
            return False, None
        match_ = self._expect.search(text)
        if match_ is not None:
            logging.debug("\x1b[5;31mText Matched: %s for %s\x1b[0m", text, self._expect.pattern)
            return True, match_.groups()
        return False, None
        #  }}} method `_verify` # 
    #  }}} class `TextEvent` # 

class IconRecogEvent(RegionEvent[str, bool]):
    #  class `IconRecogEvent` {{{ # 
    def __init__(self, icon_class: str,
            region: Iterable[float], needs_detection: bool = False,
            #transformation: Optional[str] = None,
            #wrap: Optional[Callable[[T], W]] = None,
            #update: Optional[Callable[[W, W], W]] = None,
            repeatability: Repeatability = Repeatability.NONE):
        #  method `__init__` {{{ # 
        """
        icon_class - str
        region - iterable of four floats as [x0, y0, x1, y1]
        needs_detection - bool
        #transformation - str of None
        #wrap - callable accepting the transformed type returning the wrapped
          #type or None
        #update - callable accepting
          #+ the wrapped type
          #+ the wrapped type
          #and returning the wrapped type
        repeatability - Repeatability
        """

        #super(IconRecogEvent, self).__init__(region, needs_detection, transformation, None, wrap, update, repeatability)
        super(IconRecogEvent, self).__init__(region, needs_detection, repeatability)

        self._icon_class: str = icon_class
        #  }}} method `__init__` # 

    def _verify(self, icon_class: str) -> Tuple[bool, bool]:
        #  method `_verify` {{{ # 
        """
        icon_class - str

        return bool, bool
        """

        flag = icon_class==self._icon_class
        return flag, flag
        #  }}} method `_verify` # 
    #  }}} class `IconRecogEvent` # 

class IconMatchEvent(RegionEvent[bool, bool]):
    #  class `IconMatchEvent` {{{ # 
    def __init__(self, path,
            region: Iterable[float], needs_detection: bool = False,
            #transformation: Optional[str] = None,
            #wrap: Optional[Callable[[T], W]] = None,
            #update: Optional[Callable[[W, W], W]] = None,
            repeatability: Repeatability = Repeatability.NONE):
        #  method `__init__` {{{ # 
        """
        path - str
        region - iterable of four floats as [x0, y0, x1, y1]
        needs_detection - bool
        #transformation - str or None
        #wrap - callable accepting the transformed type returning the wrapped
          #type or None
        #update - callable accepting
          #+ the wrapped type
          #+ the wrapped type
          #and returning the wrapped type
        repeatability - Repeatability
        """

        #super(IconMatchEvent, self).__init__(region, needs_detection, transformation, None, wrap, update, repeatability)
        super(IconMatchEvent, self).__init__(region, needs_detection, repeatability)

        self._path: str = path
        #  }}} method `__init__` # 

    @property
    def path(self) -> str:
        return self._path

    def _verify(self, set_flag: bool) -> Tuple[bool, bool]:
        #  method `_verify` {{{ # 
        """
        set_flag - bool

        return bool, bool
        """

        return set_flag, set_flag
        #  }}} method `_verify` # 
    #  }}} class `IconMatchEvent` # 

P = TypeVar("Property")

class ViewHierarchyEvent(EventSource[List, List[Any]]):
    #  class `ViewHierarchyEvent` {{{ # 
    class Property(abc.ABC, Generic[P]):
        #  class `Property` {{{ # 
        def __init__(self, name: str):
            #  method `__init__` {{{ # 
            """
            name - str
            """

            self._name: str = name
            #  }}} method `__init__` # 

        @property
        def name(self) -> str:
            return self._name

        @abc.abstractmethod
        def match(self, value: P) -> bool:
            #  abstract method `match` {{{ # 
            """
            value - something

            return bool
            """

            raise NotImplementedError()
            #  }}} abstract method `match` # 
        #  }}} class `Property` # 

    class PureProperty(Property[Any]):
        #  class `PureProperty` {{{ # 
        def __init__(self, name: str):
            super(ViewHierarchyEvent.PureProperty, self).__init__(name)

        def match(self, value: Any) -> bool:
            return True
        #  }}} class `PureProperty` # 

    class ScalarProperty(Property[P]):
        #  class `ScalarProperty` {{{ # 
        def __init__(self, name: str,
                comparator: Callable[[P, P], bool], value: P):
            #  method `__init__` {{{ # 
            """
            name - str
            comparator - callable accepting
              + the same type with `value`
              + the same type with `value`
              and returning bool
            value - something
            """

            super(ViewHierarchyEvent.ScalarProperty, self).__init__(name)
            self._comparator: Callable[[P, P], bool] = comparator
            self._value: P = value
            #  }}} method `__init__` # 

        def match(self, value: P) -> bool:
            #  method `match` {{{ # 
            """
            value - something

            return bool
            """

            return self._comparator(self._value, value)
            #  }}} method `match` # 
        #  }}} class `ScalarProperty` # 

    class StringProperty(Property[str]):
        #  class `StringProperty` {{{ # 
        def __init__(self, name: str, pattern: str):
            #  method `__init__` {{{ # 
            """
            name - str
            pattern - str
            """

            super(ViewHierarchyEvent.StringProperty, self).__init__(name)
            self._pattern: Pattern[str] = re.compile(pattern)
            #  }}} method `__init__` # 

        def match(self, value: str) -> bool:
            #  method `match` {{{ # 
            """
            value - str

            return bool
            """

            return self._pattern.search(value) is not None
            #  }}} method `match` # 
        #  }}} class `StringProperty` # 

    _css_quick_pattern: ClassVar[Pattern[str]] = re.compile(r'(?P<type>[#.$@])(?P<oprt>[$^*]?)(?P<val>"[^"]+"|\d+)')
    _css_quick_type: ClassVar[Dict[str, str]] = { "#": "resource-id"
                                                , ".": "class"
                                                , "$": "package"
                                                , "@": "index"
                                                }

    @staticmethod
    def _css_quick_replace(me_selector: Match[str]) -> str:
        #  function _css_quick_replace {{{ # 
        value: str = me_selector.group("val")
        if value.isdigit():
            value = "\"" + value + "\""
        return '[{:}{:}={:}]'.format( ViewHierarchyEvent._css_quick_type[me_selector.group("type")]
                                      , me_selector.group("oprt")
                                      , value
                                      )
        #  }}} function _css_quick_replace # 
    @staticmethod
    def transform_selector(me_selector: str) -> str:
        #  function transform_selector {{{ # 
        """
        Transforms Mobile-Env-customized CSS selector into standard CSS selector.
        The syntax is defined as follows:

        * #"com.wikihow.wikihowapp:id/search_src_text" -> [resource-id="com.wikihow.wikihowapp:id/search_src_text"]
        * #$"search_src_text" -> [resource-id$=search_src_text]
        * ."android.widget.EditText" -> [class="android.widget.EditText"]
        * .$"EditText" -> [class$=EditText]
        * $"com.wikihow.wikihowapp" -> [package="com.wikihow.wikihowapp"]
        * @2 -> [index="2"], somewhat the same as :nth-child(3) (index attribute starts from 0)

        Args:
            me_selector (str): Mobile-Env-customized CSS selector

        Returns:
            str: transformed standard CSS selector
        """

        return ViewHierarchyEvent._css_quick_pattern\
                .sub( ViewHierarchyEvent._css_quick_replace
                    , me_selector
                    )
        #  }}} function transform_selector # 

    def __init__( self, vh_path: Iterable[str], vh_properties: Iterable[Property]
                #, transformation: Optional[str] = None
                #, cast: Optional[Callable[[V], C]] = None
                #, wrap: Optional[Callable[[T], W]] = None
                #, update: Optional[Callable[[W, W], W]] = None
                , repeatability: Repeatability = Repeatability.NONE
                ):
        #  method `__init__` {{{ # 
        """
        Args:
            vh_path (Iterable[str]): a group of Mobile-Env-customized css
              selectors
            vh_property (Iterable[Property]): iterable of Property
            repeatability (Repeatability): defines the
              repeatability of the event source
        """

        super(ViewHierarchyEvent, self).__init__(repeatability)

        #self._vh_path: List[str] = list(vh_path)
        self._selector_str: str = ViewHierarchyEvent.transform_selector(", ".join(vh_path))
        self._selector: cssselect.CSSSelector = cssselect.CSSSelector(self._selector_str)
        self._vh_properties: List[ViewHierarchyEvent.Property] = list(vh_properties)
        self._property_names: List[str] = list(map(lambda prpt: prpt.name, vh_properties))
        #  }}} method `__init__` # 

    #@property
    #def path(self) -> List[str]:
        #return self._vh_path
    @property
    def selector(self) -> cssselect.CSSSelector:
        return self._selector
    @property
    def property_names(self) -> List[str]:
        return self._property_names

    def _verify(self, values: List[Any]) -> Tuple[bool, Optional[List[Any]]]:
        #  method `_verify` {{{ # 
        """
        values - list with the same length as `self._vh_properties`

        return
        - bool
        - the same type as `values` or None
        """

        if all(map(lambda p: p[0].match(p[1]),
                itertools.zip_longest(self._vh_properties, values))):
            logging.debug( "\x1b[5;31mVH Event\x1b[0m: %s for %s.%s"
                         , str(values)
                         , self._selector_str
                         , str(self._property_names)
                         )
            return True, values
        return False, None
        #  }}} method `_verify` # 
    #  }}} class `ViewHierarchyEvent` # 

class LogEvent(EventSource[str, List[str]]):
    #  class `LogEvent` {{{ # 
    def __init__(self, filters: Iterable[str], pattern: str,
            #transformation: Optional[str] = None,
            #cast: Optional[Callable[[V], C]] = None,
            #wrap: Optional[Callable[[T], W]] = None,
            #update: Optional[Callable[[W, W], W]] = None,
            repeatability: Repeatability = Repeatability.NONE):
        #  method `__init__` {{{ # 
        """
        filters - iterable of str
        pattern - str
        #cast - callable accepting the verified type returning the cast type or
          #None
        #wrap - callable accepting the transformed type returning the wrapped
          #type or None
        #update - callable accepting
          #+ the wrapped type
          #+ the wrapped type
          #and returning the wrapped type
        repeatability - Repeatability
        """

        super(LogEvent, self).__init__(repeatability)

        self._filters: List[str] = list(filters)
        self._pattern: Pattern[str] = re.compile(pattern)
        #  }}} method `__init__` # 

    @property
    def filters(self) -> List[str]:
        return self._filters
    @property
    def pattern(self) -> Pattern[str]:
        return self._pattern

    def _verify(self, line: str) -> Tuple[bool, Optional[List[str]]]:
        #  method `_verify` {{{ # 
        """
        line - str

        return bool, list of str or None
        """

        match_ = self._pattern.search(line)
        if match_ is not None:
            logging.debug( "\x1b[5;31mLog Event\x1b[0m: %s for %s"
                         , line
                         , self._pattern.pattern
                         )
            return True, match_.groups()
        return False, None
        #  }}} method `_verify` # 
    #  }}} class `LogEvent` # 

class ResponseEvent(EventSource[str, Union[List[str], float]]):
    #  class ResponseEvent {{{ # 
    class ResponseCheckMode(enum.IntEnum):
        REGEX = 0
        DIFFLIB = 1
        FUZZ = 2
        SBERT = 3

    def __init__( self
                , pattern: str
                , mode: ResponseCheckMode
                , sbert: Optional[SentenceTransformer] = None
                , repeatability: Repeatability = Repeatability.NONE
                ):
        #  method __init__ {{{ # 
        """
        Args:
            pattern (str): the reference for ResponseEvent
            mode (ResponseCheckMode): the match mode. relies on the following
              modules:
              * re
              * difflib
              * rapidfuzz
              * sentence-transformers
            sbert (Optional[SentenceTransformer]): sentence transformer used
              in SBERT mode
            repeatability (Repeatability): repeatability mode
        """

        super(ResponseEvent, self).__init__(repeatability)

        self._pattern: str = pattern
        self._sbert: Optional[SentenceTransformer] = sbert

        self._mode: ResponseEvent.ResponseCheckMode = mode
        if mode==ResponseEvent.ResponseCheckMode.REGEX:
            matcher: Pattern[str] = re.compile(self._pattern, flags=re.MULTILINE)
            self._match: Callable[[str], Match[str]] = matcher.search
        elif mode==ResponseEvent.ResponseCheckMode.DIFFLIB:
            matcher: SequenceMatcher = SequenceMatcher( b=self._pattern
                                                            , autojunk=False
                                                            )
            def match_(a: str) -> float:
                matcher.set_seq1(a)
                return matcher.ratio()
            self._match: Callable[[str], float] = match_
        elif mode==ResponseEvent.ResponseCheckMode.FUZZ:
            self._match: Callable[[str], float] = functools.partial( fuzz.ratio
                                                                   , self._pattern
                                                                   )
        elif mode==ResponseEvent.ResponseCheckMode.SBERT:
            # (1, D)
            encoding: torch.Tensor = self._sbert.encode( [self._pattern]
                                                       , show_progress_bar=False
                                                       , convert_to_tensor=True
                                                       , normalize_embeddings=True
                                                       )
            def match_(a: str) -> float:
                # (1, D)
                a_encoding: torch.Tensor = self._sbert.encode( [a]
                                                             , show_progress_bar=False
                                                             , convert_to_tensor=True
                                                             , normalize_embeddings=True
                                                             )
                return dot_score(encoding, a_encoding).squeeze().cpu().item()
            self._match: Callable[[str], float] = match_
        #  }}} method __init__ # 

    def _verify(self, response: str) -> Tuple[bool, Optional[Union[List[str], float]]]:
        #  method _verify {{{ # 
        if self._mode==ResponseEvent.ResponseCheckMode.REGEX:
            match_: Match[str] = self._match(response)
            if match_ is not None:
                logging.info( "\x1b[5;31mResponse Event: %s for REGEX %s\x1b[0m"
                            , response, self._pattern
                            )
                return True, match_.groups()
            return False, None
        score: float = self._match(response)
        logging.info( "\x1b[5;31mResponse Score: %.4f @ %s for %s %s\x1b[0m"
                    , score, response
                    , self._mode.name, self._pattern
                    )
        return True, score
        #  }}} method _verify # 
    #  }}} class ResponseEvent # 
