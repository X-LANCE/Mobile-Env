import abc

class Event(abc.ABC):
    #  abstract class `Event` {{{ # 
    def __init__(self, transformation=None):
        #  method `__init__` {{{ # 
        """
        transformation - str representing a python expression that can be
          evaluated by `eval` function or None for a default identity mapping.
          "x" should be used to indicate the input variable. `x` could be a
          scalar or a list.
        """

        self._transformation_str = transformation

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
    def __init__(self, events, transformation=None):
        #  method `__init__` {{{ # 
        """
        events - iterable of Event
        transformation - str or None
        """

        super(Or, self).__init__(transformation)

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
    #  class `Event` {{{ # 
    def __init__(self, events, transformation=None):
        #  method `__init__` {{{ # 
        """
        events - iterable of Event
        transformation - str of None
        """

        super(And, self).__init__(transformation)

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
    #  }}} class `Event` # 
