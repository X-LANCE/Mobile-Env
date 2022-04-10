import abc
import re
import itertools

# The general data flow for the event flag classes:
# value -> cast -> transform -> update
#        \\_________________/        /
#         \    _transform           /
#          \_______________________/

class Event(abc.ABC):
    #  abstract class `Event` {{{ # 
    def __init__(self, transformation=None, cast=None, update=None):
        #  method `__init__` {{{ # 
        """
        transformation - str representing a python expression that can be
          evaluated by `eval` function or None for a default identity mapping.
          "x" should be used to indicate the input variable. `x` could be a
          scalar or a list.
        cast - callable accepting something returning something else or None
        update - callable accepting
          + something as `self._value`
          + something as the new value
          and returning something
        """

        self._transformation_str = transformation
        self._cast = cast or (lambda x: x)
        update = update or (lambda x, y: y)
        self._update = lambda x, y: update(x, y) if x is not None else y

        self._flag = False
        self._value = None

        self._ever_set = False
        self._prerequisites = []
        #  }}} method `__init__` # 

    def _transform(self, x):
        #  method `_transformation` {{{ # 
        """
        x - the same type as `self._value` or list of instances of type of
          `self._value`

        return something
        """

        x = list(map(self._cast, x)) if hasattr(x, "__iter__") else self._cast(x)
        return eval(self._transformation_str) if self._transformation_str else x
        #  }}} method `_transformation` # 

    def set(self, value):
        #  method `set` {{{ # 
        """
        value - something
        """

        if any(map(lambda evt: not evt.is_ever_set(), self._prerequisites)):
            return
        is_validate, value = self._verify(value)
        if is_validate:
            value = self._transform(value)
            self._value = self._update(self._value, value)
            self._flag = True
            self._ever_set = True
        #  }}} method `set` # 
    def _verify(self, value):
        #  method `_verify` {{{ # 
        """
        This is a hook function for the extenders to implement.

        value - something

        return
        - bool
        - something else
        """

        raise NotImplementedError()
        #  }}} method `_verify` # 
    def clear(self):
        #  method `clear` {{{ # 
        self._flag = False
        self._value = None
        #  }}} method `clear` # 
    def is_set(self):
        return self._flag
    def get(self):
        #  method `get` {{{ # 
        """
        return the same type as `self._transform` returns if `this.is_set()` else None
        """

        return self._value if self.is_set() else None
        #  }}} method `get` # 

    def is_ever_set(self):
        return self._ever_set
    def reset(self):
        self._flag = False
        self._value = None
        self._ever_set = False
    def add_prerequisites(self, *prerequisites):
        #  method `add_prerequisites` {{{ # 
        """
        prerequisites - iterable of Event
        """

        self._prerequisites += prerequisites
        #  }}} method `add_prerequisites` # 
    #  }}} abstract class `Event` # 

class EmptyEvent(Event):
    #  class `EmptyEvent` {{{ # 
    def __init__(self):
        super(EmptyEvent, self).__init__()
    def set(self, value):
        pass
    def _verify(self, value):
        return False, None
    def is_set(self):
        return False
    def get(self):
        return None
    #  }}} class `EmptyEvent` # 

class Or(Event):
    #  class `Or` {{{ # 
    def __init__(self, events, transformation=None, cast=None, update=None):
        #  method `__init__` {{{ # 
        """
        events - iterable of Event
        transformation - str or None
        cast - callable accepting something returning something else or None
        update - callable accepting
          + something as `self._value`
          + something as the new value
          and returning something
        """

        update = update or (lambda x, y: x)
        super(Or, self).__init__(transformation, cast, update)

        self._events = list(events)
        #  }}} method `__init__` # 

    def is_set(self):
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

    def get(self):
        #  method `get` {{{ # 
        """
        return the same type as `self._transform` returns or None
        """

        if any(map(lambda evt: not evt.is_ever_set(), self._prerequisites)):
            return None
        value = None
        is_set = False
        for evt in self._events:
            if evt.is_set():
                is_set = True
                self._ever_set = True
                value = self._update(value, self._transform(evt.get()))
        return value if is_set else None
        #  }}} method `get` # 

    def is_ever_set(self):
        if not self._ever_set:
            return self.is_set()
        return True
    #  }}} class `Or` # 

class And(Event):
    #  class `And` {{{ # 
    def __init__(self, events, transformation=None, cast=None, update=None):
        #  method `__init__` {{{ # 
        """
        events - iterable of Event
        transformation - str of None
        cast - callable accepting something returning something else or None
        update - callable accepting
          + something as `self._value`
          + something as the new value
          and returning something, has no effect for `And` event.
        """

        super(And, self).__init__(transformation, cast, update)

        self._events = list(events)
        #  }}} method `__init__` # 

    def is_set(self):
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

    def get(self):
        #  method `get` {{{ # 
        """
        return the same type as `self._transform` returns or None
        """

        if any(map(lambda evt: not evt.is_ever_set(), self._prerequisites)):
            return None
        return self._transform(
                list(
                    map(lambda x: x.get(),
                        self._events))) if self.is_set() else None
        #  }}} method `get` # 

    def is_ever_set(self):
        if not self._ever_set:
            return self.is_set()
        return True
    #  }}} class `And` # 

class RegionEvent(Event, abc.ABC):
    #  abstract class `RegionEvent` {{{ # 
    def __init__(self, region, needs_detection=False,
            transformation=None, cast=None, update=None):
        #  method `__init__` {{{ # 
        """
        region - iterable of four floats as [x0, y0, x1, y1]
        needs_detection - bool
        transformation - str of None
        cast - callable accepting something returning something else or None
        update - callable accepting
          + something as `self._value`
          + something as the new value
          and returning something
        """

        super(RegionEvent, self).__init__(transformation, cast, update)
        self._region = list(itertools.islice(region, 4))
        self._needs_detection = needs_detection
        #  }}} method `__init__` # 

    @property
    def region(self):
        return self._region
    @property
    def needs_detection(self):
        return self._needs_detection
    #  }}} abstract class `RegionEvent` # 

class TextEvent(RegionEvent):
    #  class `TextEvent` {{{ # 
    def __init__(self, expect,
            region, needs_detection=False,
            transformation=None, cast=None, update=None):
        #  method `__init__` {{{ # 
        """
        expect - str
        region - iterable of four floats as [x0, y0, x1, y1]
        needs_detection - bool
        transformation - str or None
        cast - callable accepting str returning something except str or None
        update - callable accepting
          + str as `self._value`
          + str as the new value
          and returning str
        """

        super(TextEvent, self).__init__(region, needs_detection, transformation, cast, update)

        self._expect = re.compile(expect)
        #  }}} method `__init__` # 

    def _verify(self, text):
        #  method `_verify` {{{ # 
        """
        text - str or None

        return bool, list of str or None
        """

        match_ = self._expect.match(text)
        if match_ is not None:
            return True, match_.groups()
        return False, None
        #  }}} method `_verify` # 
    #  }}} class `TextEvent` # 

class IconRecogEvent(RegionEvent):
    #  class `IconRecogEvent` {{{ # 
    def __init__(self, icon_class,
            region, needs_detection=False,
            transformation=None, update=None):
        #  method `__init__` {{{ # 
        """
        icon_class - str
        region - iterable of four floats as [x0, y0, x1, y1]
        needs_detection - bool
        transformation - str of None
        update - callable accepting
          + something as `self._value`
          + something as the new value
          and returning something
        """

        super(IconRecogEvent, self).__init__(region, needs_detection, transformation, None, update)

        self._icon_class = icon_class
        #  }}} method `__init__` # 

    def _verify(self, icon_class):
        #  method `_verify` {{{ # 
        """
        icon_class - str

        return bool, bool
        """

        flag = icon_class==self._icon_class
        return flag, flag
        #  }}} method `_verify` # 
    #  }}} class `IconRecogEvent` # 

class IconMatchEvent(RegionEvent):
    #  class `IconMatchEvent` {{{ # 
    def __init__(self, path,
            region, needs_detection=False,
            transformation=None, update=None):
        #  method `__init__` {{{ # 
        """
        path - str
        region - iterable of four floats as [x0, y0, x1, y1]
        needs_detection - bool
        transformation - str or None
        update - callable accepting
          + something as `self._value`
          + something as the new value
          and returning something
        """

        super(IconMatchEvent, self).__init__(region, needs_detection, transformation, None, update)

        self._path = path
        #  }}} method `__init__` # 

    @property
    def path(self):
        return self._path

    def _verify(self, set_flag):
        #  method `_verify` {{{ # 
        """
        set_flag - bool

        return bool, bool
        """

        return set_flag, set_flag
        #  }}} method `_verify` # 
    #  }}} class `IconMatchEvent` # 

class ViewHierarchyEvent(Event):
    #  class `ViewHierarchyEvent` {{{ # 
    class Property(abc.ABC):
        #  class `Property` {{{ # 
        def __init__(self, name):
            #  method `__init__` {{{ # 
            """
            name - str
            """

            self._name = name
            #  }}} method `__init__` # 

        @property
        def name(self):
            return self._name

        @abc.abstractmethod
        def match(self, value):
            #  abstract method `match` {{{ # 
            """
            value - something

            return bool
            """

            raise NotImplementedError
            #  }}} abstract method `match` # 
        #  }}} class `Property` # 

    class PureProperty(Property):
        #  class `PureProperty` {{{ # 
        def __init__(self, name):
            super(PureProperty, self).__init__(name)

        def match(self, value):
            return True
        #  }}} class `PureProperty` # 

    class ScalarProperty(Property):
        #  class `ScalarProperty` {{{ # 
        def __init__(self, name, comparator, value):
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
            self._comparator = comparator
            self._value = value
            #  }}} method `__init__` # 

        def match(self, value):
            #  method `match` {{{ # 
            """
            value - something

            return bool
            """

            return self._comparator(self._value, value)
            #  }}} method `match` # 
        #  }}} class `ScalarProperty` # 

    class StringProperty(Property):
        #  class `StringProperty` {{{ # 
        def __init__(self, name, pattern):
            #  method `__init__` {{{ # 
            """
            name - str
            pattern - str
            """

            super(StringProperty, self).__init__(name)
            self._pattern = re.compile(pattern)
            #  }}} method `__init__` # 

        def match(self, value):
            #  method `match` {{{ # 
            """
            value - str

            return bool
            """

            return self._pattern.match(value) is not None
            #  }}} method `match` # 
        #  }}} class `StringProperty` # 

    def __init__(self, vh_path, vh_properties,
            transformation=None, cast=None, update=None):
        #  method `__init__` {{{ # 
        """
        vh_path - iterable of str
        vh_property - iterable of Property
        transformation - str or None
        cast - callable accepting something returning something else or None
        update - callable accepting
          + something as `self._value`
          + something as the new value
          and returning something
        """

        super(ViewHierarchyEvent, self).__init__(transformation, cast, update)

        self._vh_path = list(vh_path)
        self._vh_properties = list(vh_properties)
        self._property_names = list(map(lambda prpt: prpt.name, vh_properties))
        #  }}} method `__init__` # 

    # ZDY_COMMENT: I'd like to leave the view hierarchy match job to the
    # dumpsys thread

    @property
    def path(self):
        return self._vh_path
    @property
    def property_names(self):
        return self._property_names

    def _verify(self, values):
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

class LogEvent(Event):
    #  class `LogEvent` {{{ # 
    def __init__(self, filters, pattern,
            transformation=None, cast=None, update=None):
        #  method `__init__` {{{ # 
        """
        filters - iterable of str
        pattern - str
        transformation - str of None
        cast - callable accepting str returning something except str or None
        """

        super(LogEvent, self).__init__(transformation, cast, update)

        self._filters = list(filters)
        self._pattern = re.compile(pattern)
        #  }}} method `__init__` # 

    @property
    def filters(self):
        return self._filters
    @property
    def pattern(self):
        return self._pattern

    def _verify(self, line):
        #  method `_verify` {{{ # 
        """
        line - str

        return bool, list of str
        """

        match_ = self._pattern.match(line)
        if match_ is not None:
            return True, match_.groups()
        return False, None
        #  }}} method `_verify` # 
    #  }}} class `LogEvent` # 
