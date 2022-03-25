from android_env.components import thread_function

# mainly taken from `DumpsysThread`
class ScreenAnalyzerThread(thread_function.ThreadFunction):
    #  class `ScreenAnalyzerThread` {{{ # 
    def __init__(self,
            text_detector, text_recognizer,
            icon_detector, icon_recognizer, icon_matcher,
            check_frequency, max_failed_current_activity,
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

        check_frequency - int
        max_failed_current_activity - int

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

        self._main_loop_counter = 0
        self._check_frequency = check_frequency
        self._max_failed_activity_extraction = max_failed_current_activity
        self._num_failed_activity_extraction = 0
        #  }}} method `__init__` # 
    #  }}} class `ScreenAnalyzerThread` # 
