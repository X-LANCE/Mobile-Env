import abc
import re
import itertools

from typing import Generic, TypeVar, Callable, Optional, Any
from typing import Tuple, List, Pattern
from typing import Iterable

# The general data flow for the event flag classes:
# value -> verification -> cast -> transform -> wrap -> update
#                        \\_________________/          /
#                         \    _transform             /
#                          \_________________________/

# TODO: add type annotations

I = TypeVar("Input")
V = TypeVar("Verified")
C = TypeVar("Cast")
T = TypeVar("Transformed")
W = TypeVar("Wrapped")

class Event(abc.ABC, Generic[I, V, C, T, W]):
    #  abstract class `Event` {{{ # 
    def __init__(self,
            transformation: Optional[str] = None,
            cast: Optional[Callable[[V], C]] = None,
            wrap: Optional[Callable[[T], W]] = None,
            update: Optional[Callable[[W, W], W]] = None):
        #  method `__init__` {{{ # 
        """
        transformation - str representing a python expression that can be
          evaluated by `eval` function or None for a default identity mapping.
          "x" should be used to indicate the input variable. `x` could be a
          scalar or a list.
        cast - callable accepting the verified type returning the cast type or
          None
        wrap - callable accepting the transformed type returning the wrapped
          type or None
        update - callable accepting
          + the wrapped type
          + the wrapped type
          and returning the wrapped type
        """

        self._transformation_str: Optional[str] = transformation
        self._cast: Callable[[V], C] = cast or (lambda x: x)
        self._wrap: Callable[[T], W] = wrap or (lambda x: x)
        update = update or (lambda x, y: y)
        self._update: Callable[[Optional[W], W], W] = lambda x, y: update(x, y) if x is not None else y

        self._flag: bool = False
        self._value: Optional[W] = None

        self._ever_set: bool = False
        self._prerequisites: List[Event] = []
        #  }}} method `__init__` # 

    def _transform(self, x: Union[V, List[V]]) -> T:
        #  method `_transformation` {{{ # 
        """
        x - the same type as `self._value` or list of instances of type of
          `self._value`

        return something
        """

        x = list(map(self._cast, x)) if hasattr(x, "__iter__") else self._cast(x)
        return eval(self._transformation_str) if self._transformation_str else x
        #  }}} method `_transformation` # 

    def set(self, value: I):
        #  method `set` {{{ # 
        """
        value - the input type
        """

        if any(map(lambda evt: not evt.is_ever_set(), self._prerequisites)):
            return
        is_validate, value = self._verify(value)
        if is_validate:
            value = self._transform(value)
            value = self._wrap(value)
            self._value = self._update(self._value, value)
            self._flag = True
            self._ever_set = True
        #  }}} method `set` # 
    @abc.abstractmethod
    def _verify(self, value: I) -> Tuple[bool, Optional[Union[V, List[V]]]]:
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
    def clear(self):
        #  method `clear` {{{ # 
        self._flag = False
        self._value = None
        #  }}} method `clear` # 
    def is_set(self) -> bool:
        return self._flag
    def get(self) -> Optional[W]:
        #  method `get` {{{ # 
        """
        return the wrapped type if `this.is_set()` else None
        """

        return self._value if self.is_set() else None
        #  }}} method `get` # 

    def is_ever_set(self) -> bool:
        return self._ever_set
    def reset(self):
        self._flag = False
        self._value = None
        self._ever_set = False
    def add_prerequisites(self, *prerequisites: Iterable[Event]):
        #  method `add_prerequisites` {{{ # 
        """
        prerequisites - iterable of Event
        """

        self._prerequisites += prerequisites
        #  }}} method `add_prerequisites` # 
    #  }}} abstract class `Event` # 

class EmptyEvent(Event[Any, None, None, None, None]):
    #  class `EmptyEvent` {{{ # 
    def __init__(self):
        super(EmptyEvent, self).__init__()
    def set(self, value: Any):
        pass
    def _verify(self, value: Any) -> Tuple[bool, None]:
        return False, None
    def is_set(self) -> Tuple[bool]:
        return False
    def get(self) -> None:
        return None
    #  }}} class `EmptyEvent` # 

class Or(Event[Any, V, C, T, W]):
    #  class `Or` {{{ # 
    def __init__(self,
            events: Iterable[Event[Any, Any, Any, Any, V]],
            transformation: Optional[str] = None,
            cast: Optional[Callable[[V], C]] = None,
            wrap: Optional[Callable[[T], W]] = None,
            update: Optional[Callable[[W, W], W]] = None):
        #  method `__init__` {{{ # 
        """
        events - iterable of Event
        transformation - str or None
        cast - callable accepting the verified type returning the cast type or
          None
        wrap - callable accepting the transformed type returning the wrapped
          type or None
        update - callable accepting
          + the wrapped type
          + the wrapped type
          and returning the wrapped type
        """

        update = update or (lambda x, y: x)
        super(Or, self).__init__(transformation, cast, wrap, update)

        self._events: List[Event[Any, Any, Any, Any, V]] = list(events)
        #  }}} method `__init__` # 

    def set(self, value: Any):
        pass

    def is_set(self) -> bool:
        #  method `is_set` {{{ # 
        """
        return bool
        """

        if any(map(lambda evt: not evt.is_ever_set(), self._prerequisites)):
            return False
        if any(map(lambda x: x.is_set(), self._events)):
            self._ever_set = True
            return True
        return False
        #  }}} method `is_set` # 

    def clear(self):
        #  method `clear` {{{ # 
        for evt in self._events:
            evt.clear()
        #  }}} method `clear` # 

    def get(self) -> Optional[W]:
        #  method `get` {{{ # 
        """
        return the wrapped type returns or None
        """

        if any(map(lambda evt: not evt.is_ever_set(), self._prerequisites)):
            return None
        value = None
        is_set = False
        for evt in self._events:
            if evt.is_set():
                is_set = True
                self._ever_set = True
                value = self._update(value, self._wrap(self._transform(evt.get())))
        return value if is_set else None
        #  }}} method `get` # 

    def is_ever_set(self) -> bool:
        if not self._ever_set:
            return self.is_set()
        return True
    #  }}} class `Or` # 

class And(Event[Any, V, C, T, W]):
    #  class `And` {{{ # 
    def __init__(self,
            events: Iterable[Event[Any, Any, Any, Any, V]],
            transformation: Optional[str] = None,
            cast: Optional[Callable[[V], C]] = None,
            wrap: Optional[Callable[[T], W]] = None):
        #  method `__init__` {{{ # 
        """
        events - iterable of Event
        transformation - str of None
        cast - callable accepting the verified type returning the cast type or
          None
        wrap - callable accepting the transformed type returning the wrapped
          type or None
        """

        super(And, self).__init__(transformation, cast, wrap, None)

        self._events: List[Event[Any, Any, Any, Any, V]] = list(events)
        #  }}} method `__init__` # 

    def set(self, value: Any):
        pass

    def is_set(self) -> bool:
        #  method `is_set` {{{ # 
        """
        return bool
        """

        if any(map(lambda evt: not evt.is_ever_set(), self._prerequisites)):
            return False
        if len(self._events)==0:
            return False
        if any(map(lambda x: not x.is_set(), self._events)):
            return False
        self._ever_set = True
        return True
        #  }}} method `is_set` # 

    def clear(self):
        #  method `clear` {{{ # 
        if self.is_set():
            for evt in self._events:
                evt.clear()
        #  }}} method `clear` # 
    def force_clear(self):
        #  method `force_clear` {{{ # 
        for evt in self._events:
            evt.clear()
        #  }}} method `force_clear` # 

    def get(self) -> Optional[W]:
        #  method `get` {{{ # 
        """
        return the wrapped type returns or None
        """

        if any(map(lambda evt: not evt.is_ever_set(), self._prerequisites)):
            return None
        return self._wrap(
                self._transform(
                    list(
                        map(lambda x: x.get(),
                            self._events)))) if self.is_set() else None
        #  }}} method `get` # 

    def is_ever_set(self) -> bool:
        if not self._ever_set:
            return self.is_set()
        return True
    #  }}} class `And` # 

class RegionEvent(Event[I, V, C, T, W], abc.ABC):
    #  abstract class `RegionEvent` {{{ # 
    def __init__(self, region: Iterable[float], needs_detection: bool = False,
            transformation: Optional[str] = None,
            cast: Optional[Callable[[V], C]] = None,
            wrap: Optional[Callable[[T], W]] = None,
            update: Optional[Callable[[W, W], W]] = None):
        #  method `__init__` {{{ # 
        """
        region - iterable of four floats as [x0, y0, x1, y1]
        needs_detection - bool
        transformation - str of None
        cast - callable accepting the verified type returning the cast type or
          None
        wrap - callable accepting the transformed type returning the wrapped
          type or None
        update - callable accepting
          + the wrapped type
          + the wrapped type
          and returning the wrapped type
        """

        super(RegionEvent, self).__init__(transformation, cast, wrap, update)
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

class TextEvent(RegionEvent[Optional[str], str, C, T, W]):
    #  class `TextEvent` {{{ # 
    def __init__(self, expect: str,
            region: Iterable[float], needs_detection: bool = False,
            transformation: Optional[str] = None,
            cast: Optional[Callable[[str], C]] = None,
            wrap: Optional[Callable[[T], W]] = None,
            update: Optional[Callable[[W, W], W]] = None):
        #  method `__init__` {{{ # 
        """
        expect - str
        region - iterable of four floats as [x0, y0, x1, y1]
        needs_detection - bool
        transformation - str or None
        cast - callable accepting the verified type returning the cast type or
          None
        wrap - callable accepting the transformed type returning the wrapped
          type or None
        update - callable accepting
          + the wrapped type
          + the wrapped type
          and returning the wrapped type
        """

        super(TextEvent, self).__init__(region, needs_detection, transformation, cast, wrap, update)

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
        match_ = self._expect.match(text)
        if match_ is not None:
            return True, match_.groups()
        return False, None
        #  }}} method `_verify` # 
    #  }}} class `TextEvent` # 

class IconRecogEvent(RegionEvent[str, bool, bool, T, W]):
    #  class `IconRecogEvent` {{{ # 
    def __init__(self, icon_class: str,
            region: Iterable[float], needs_detection: bool = False,
            transformation: Optional[str] = None,
            wrap: Optional[Callable[[T], W]] = None,
            update: Optional[Callable[[W, W], W]] = None):
        #  method `__init__` {{{ # 
        """
        icon_class - str
        region - iterable of four floats as [x0, y0, x1, y1]
        needs_detection - bool
        transformation - str of None
        wrap - callable accepting the transformed type returning the wrapped
          type or None
        update - callable accepting
          + the wrapped type
          + the wrapped type
          and returning the wrapped type
        """

        super(IconRecogEvent, self).__init__(region, needs_detection, transformation, None, wrap, update)

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

class IconMatchEvent(RegionEvent[bool, bool, bool, T, W]):
    #  class `IconMatchEvent` {{{ # 
    def __init__(self, path,
            region: Iterable[float], needs_detection: bool = False,
            transformation: Optional[str] = None,
            wrap: Optional[Callable[[T], W]] = None,
            update: Optional[Callable[[W, W], W]] = None):
        #  method `__init__` {{{ # 
        """
        path - str
        region - iterable of four floats as [x0, y0, x1, y1]
        needs_detection - bool
        transformation - str or None
        wrap - callable accepting the transformed type returning the wrapped
          type or None
        update - callable accepting
          + the wrapped type
          + the wrapped type
          and returning the wrapped type
        """

        super(IconMatchEvent, self).__init__(region, needs_detection, transformation, None, wrap, update)

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

class ViewHierarchyEvent(Event[List, Any, C, T, W]):
    #  class `ViewHierarchyEvent` {{{ # 
    P = TypeVar("Property")

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

            raise NotImplementedError
            #  }}} abstract method `match` # 
        #  }}} class `Property` # 

    class PureProperty(Property[Any]):
        #  class `PureProperty` {{{ # 
        def __init__(self, name: str):
            super(PureProperty, self).__init__(name)

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

            super(ScalarProperty, self).__init__(name)
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

            super(StringProperty, self).__init__(name)
            self._pattern: Pattern[str] = re.compile(pattern)
            #  }}} method `__init__` # 

        def match(self, value: str) -> bool:
            #  method `match` {{{ # 
            """
            value - str

            return bool
            """

            return self._pattern.match(value) is not None
            #  }}} method `match` # 
        #  }}} class `StringProperty` # 

    def __init__(self, vh_path: Iterable[str], vh_properties: Iterable[Property],
            transformation: Optional[str] = None,
            cast: Optional[Callable[[V], C]] = None,
            wrap: Optional[Callable[[T], W]] = None,
            update: Optional[Callable[[W, W], W]] = None):
        #  method `__init__` {{{ # 
        """
        vh_path - iterable of str
        vh_property - iterable of Property
        transformation - str or None
        cast - callable accepting the verified type returning the cast type or
          None
        wrap - callable accepting the transformed type returning the wrapped
          type or None
        update - callable accepting
          + the wrapped type
          + the wrapped type
          and returning the wrapped type
        """

        super(ViewHierarchyEvent, self).__init__(transformation, cast, wrap, update)

        self._vh_path: List[str] = list(vh_path)
        self._vh_properties: List[Property] = list(vh_properties)
        self._property_names: List[str] = list(map(lambda prpt: prpt.name, vh_properties))
        #  }}} method `__init__` # 

    @property
    def path(self) -> List[str]:
        return self._vh_path
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
            return True, values
        return False, None
        #  }}} method `_verify` # 
    #  }}} class `ViewHierarchyEvent` # 

class LogEvent(Event[str, str, C, T, W]):
    #  class `LogEvent` {{{ # 
    def __init__(self, filters: Iterable[str], pattern: str,
            transformation: Optional[str] = None,
            cast: Optional[Callable[[V], C]] = None,
            wrap: Optional[Callable[[T], W]] = None,
            update: Optional[Callable[[W, W], W]] = None):
        #  method `__init__` {{{ # 
        """
        filters - iterable of str
        pattern - str
        cast - callable accepting the verified type returning the cast type or
          None
        wrap - callable accepting the transformed type returning the wrapped
          type or None
        update - callable accepting
          + the wrapped type
          + the wrapped type
          and returning the wrapped type
        """

        super(LogEvent, self).__init__(transformation, cast, wrap, update)

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

        match_ = self._pattern.match(line)
        if match_ is not None:
            return True, match_.groups()
        return False, None
        #  }}} method `_verify` # 
    #  }}} class `LogEvent` # 
