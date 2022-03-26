from android_env.components import thread_function
import enum

from android_env.proto import emulator_controller_pb2
from android_env.proto import emulator_controller_pb2_grpc

# mainly taken from `DumpsysThread`
class ScreenAnalyzerThread(thread_function.ThreadFunction):
    #  class `ScreenAnalyzerThread` {{{ # 
    class Signal(enum.IntEnum):
        #  enum `Signal` {{{ # 
        CHECK_SCREEN = 0
        DID_NOT_CHECK = 1
        OK = 2
        #  }}} enum `Signal` # 

    def __init__(self,
            text_detector, text_recognizer,
            icon_detector, icon_recognizer, icon_matcher,
            emulator_stub, image_format,
            #check_frequency,
            #max_failed_current_activity,
            block_input, block_output, name="screen_analyzer"):
        #  method `__init__` {{{ # 
        """
        text_detector - callable accepting tensor with shape (3, width, height)
          as screenshot and returning list of str as detected texts
        text_recognizer - callable accepting tensor with shape (3, width, height)
          and returning str

        icon_detector - callable accepting tensor with shape (3, width, height)
          and returning
          + tensor of float32 with shape (nb_icons, 4)
          + list of str with length nb_icons as recognized icon classes
        icon_recognizer - callable accepting tensor with shape (3, width, height)
          and returning str as recognized icon class
        icon_matcher - callable accepting
          + tensor with shape (nb_candidates, 3, width, height)
          + tensor with shape (3, width, height)
          and returning list of bool

        emulator_stub - emulator_controller_pb2_grpc.EmulatorControllerStub
        image_format - emulator_controller_pb2.ImageFormat

        #check_frequency - int
        #max_failed_current_activity - int

        block_input - bool
        block_output - bool
        name - str
        """

        super(ScreenAnalyzerThread, self).__init__(block_input, block_output, name)

        self._text_detector = text_detector
        self._test_recognizer = text_recognizer
        self._icon_detector = icon_detector
        self._icon_recognizer = icon_recognizer
        self._icon_matcher = icon_matcher

        self._emulator_stub = emulator_stub
        self._image_format = image_format

        self._text_event_listeners = []
        self._icon_event_listeners = []
        self._icon_match_event_listeners = []

        #self._main_loop_counter = 0
        #self._check_frequency = check_frequency
        #self._max_failed_activity_extraction = max_failed_current_activity
        #self._num_failed_activity_extraction = 0
        #  }}} method `__init__` # 

    #  Methods to Add Event Listeners {{{ # 
    def add_text_event_listeners(self, *event_listeners):
        """
        event_listeners - list of event_listeners.TextEvent
        """

        self._text_event_listeners += event_listeners

    def add_icon_event_listeners(self, *event_listeners):
        """
        event_listeners - list of event_listeners.IconRecogEvent
        """

        self._icon_event_listeners += event_listeners

    def add_icon_match_event_listeners(self, *event_listeners):
        """
        event_listeners - list of event_listeners.IconMatchEvent
        """

        self._icon_match_event_listeners += event_listeners
    #  }}} Methods to Add Event Listeners # 

    def get_screenshot(self):
        """
        return tensor of uint8 with shape (3, width, height)
        """

        image_proto = self._emulator_stub.getScreenshot(self._image_format)

    #  Methods to Match Registered Events {{{ # 
    def match_text_events(self):
        #  method `match_text_events` {{{ # 
        pass
        #  }}} method `match_text_events` # 
    #  }}} Methods to Match Registered Events # 

    def main(self):
        #  method `main` {{{ # 
        command = self._read_value()

        if command!=ScreenAnalyzerThread.Signal.CHECK_SCREEN:
            self._write_value(ScreenAnalyzerThread.Signal.DID_NOT_CHECK)
            return
        #self._main_loop_counter += 1
        #if self._check_frequency<=0 or\
                #self._main_loop_counter < self._check_frequency:
            #self._write_value(ScreenAnalyzerThread.Signal.DID_NOT_CHECK)
            #return
        #self._main_loop_counter = 0

        screen = self.get_screenshot()

        self.match_text_events()
        self.match_icon_events()
        self.match_icon_match_events()
        #  }}} method `main` # 
    #  }}} class `ScreenAnalyzerThread` # 
