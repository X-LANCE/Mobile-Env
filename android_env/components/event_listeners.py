import abc
import re
import itertools

class Event(abc.ABC):
    #  abstract class `Event` {{{ # 
    def __init__(self, transformation=None, cast=None):
        #  method `__init__` {{{ # 
        """
        transformation - str representing a python expression that can be
          evaluated by `eval` function or None for a default identity mapping.
          "x" should be used to indicate the input variable. `x` could be a
          scalar or a list.
        cast - callable accepting something returning something else or None
        """

        self._transformation_str = transformation
        self._cast = cast or (lambda x: x)

        self._flag = False
        self._value = None
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
        value - the same type as `self._value`
        """

        self._value = value
        self._flag = True
        #  }}} method `set` # 
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

        return self._transform(self._value) if self.is_set() else None
        #  }}} method `get` # 
    #  }}} abstract class `Event` # 

class Or(Event):
    #  class `Or` {{{ # 
    def __init__(self, events, transformation=None, cast=None):
        #  method `__init__` {{{ # 
        """
        events - iterable of Event
        transformation - str or None
        cast - callable accepting something returning something else or None
        """

        super(Or, self).__init__(transformation, cast)

        self._events = list(events)
        #  }}} method `__init__` # 

    def is_set(self):
        #  method `is_set` {{{ # 
        """
        return bool
        """

        return any(map(lambda x: x.is_set(), self._events))
        #  }}} method `is_set` # 

    def get(self):
        #  method `get` {{{ # 
        """
        return the same type as `self._transform` returns or None
        """

        for evt in self._events:
            if evt.is_set():
                return self._transform(evt.get())
        return None
        #  }}} method `get` # 
    #  }}} class `Or` # 

class And(Event):
    #  class `And` {{{ # 
    def __init__(self, events, transformation=None, cast=None):
        #  method `__init__` {{{ # 
        """
        events - iterable of Event
        transformation - str of None
        cast - callable accepting something returning something else or None
        """

        super(And, self).__init__(transformation, cast)

        self._events = list(events)
        #  }}} method `__init__` # 

    def is_set(self):
        #  method `is_set` {{{ # 
        """
        return bool
        """

        return all(map(lambda x: x.is_set(), self._events))
        #  }}} method `is_set` # 

    def get(self):
        #  method `get` {{{ # 
        """
        return the same type as `self._transform` returns or None
        """

        return self._transform(
                list(
                    map(lambda x: x.get(),
                        self._events))) if self.is_set() else None
        #  }}} method `get` # 
    #  }}} class `And` # 

class RegionEvent(Event, abc.ABC):
    #  abstract class `RegionEvent` {{{ # 
    def __init__(self, region, needs_detection=False,
            transformation=None, cast=None):
        #  method `__init__` {{{ # 
        """
        region - iterable of four floats as [x0, y0, x1, y1]
        needs_detection - bool
        transformation - str of None
        cast - callable accepting something returning something else or None
        """

        super(RegionEvent, self).__init__(transformation, cast)
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
            transformation=None, cast=None):
        #  method `__init__` {{{ # 
        """
        expect - str
        region - iterable of four floats as [x0, y0, x1, y1]
        needs_detection - bool
        transformation - str or None
        cast - callable accepting str returning something except str or None
        """

        super(TextEvent, self).__init__(region, needs_detection, transformation, cast)

        self._expect = re.compile(expect)
        #  }}} method `__init__` # 

    def set(self, text):
        #  method `set` {{{ # 
        """
        text - str or None
        """

        match_ = self.expect.match(text)
        if match_ is not None:
            self.value = match_.groups()
            self._flag = True
        #  }}} method `set` # 
    #  }}} class `TextEvent` # 

class IconRecogEvent(RegionEvent):
    #  class `IconRecogEvent` {{{ # 
    def __init__(self, icon_class,
            region, needs_detection=False,
            transformation=None):
        #  method `__init__` {{{ # 
        """
        icon_class - str
        region - iterable of four floats as [x0, y0, x1, y1]
        needs_detection - bool
        transformation - str of None
        """

        super(IconRecogEvent, self).__init__(region, needs_detection, transformation, None)

        self._icon_class = icon_class
        #  }}} method `__init__` # 

    def set(self, icon_class):
        #  method `set` {{{ # 
        """
        icon_class - str
        """

        if icon_class==self._icon_class:
            self._value = True
            self._flag = True
        #  }}} method `set` # 
    #  }}} class `IconRecogEvent` # 

class IconMatchEvent(RegionEvent):
    #  class `IconMatchEvent` {{{ # 
    def __init__(self, path,
            region, needs_detection=False,
            transformation=None):
        #  method `__init__` {{{ # 
        """
        path - str
        region - iterable of four floats as [x0, y0, x1, y1]
        needs_detection - bool
        transformation - str or None
        """

        super(IconMatchEvent, self).__init__(region, needs_detection, transformation, None)

        self._path = path
        #  }}} method `__init__` # 

    @property
    def path(self):
        return self._path

    def set(self, set_flag):
        #  method `set` {{{ # 
        """
        set_flag - bool
        """

        if set_flag:
            self._value = True
            self._flag = True
        #  }}} method `set` # 
    #  }}} class `IconMatchEvent` # 

# TODO: `ViewHierarchyEvent` and `LogEvent`

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
    #  }}} class `ViewHierarchyEvent` # 
