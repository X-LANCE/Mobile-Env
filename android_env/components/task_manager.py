# coding=utf-8
# vim: set tabstop=2 shiftwidth=2:
# Copyright 2021 DeepMind Technologies Limited.
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

"""TaskManager handles all events and information related to the task."""

import ast
import copy
import datetime
import json
import queue
import re
import threading
from typing import Any, Dict, List, Set
import functools
import operator

from absl import logging
from android_env.components import adb_controller as adb_control

from android_env.components import app_screen_checker
from android_env.components import dumpsys_thread
from android_env.components import errors

from android_env.components import log_stream as log_stream_lib
from android_env.components import logcat_thread

# zdy
from android_env.components.tools import naive_functions
from android_env.proto import emulator_controller_pb2
from android_env.proto import emulator_controller_pb2_grpc
from android_env.components import screen_analyzer_thread

from android_env.components import setup_step_interpreter
from android_env.proto import task_pb2
from android_env.components import event_listeners # zdy
import numpy as np

class TaskManager():
  """Handles all events and information related to the task."""

  def __init__(
      self,
      task: task_pb2.Task,
      max_bad_states: int = 3,
      dumpsys_check_frequency: int = 150,
      max_failed_current_activity: int = 10,
  ):
    #  method `__init__` {{{ # 
    """Controls task-relevant events and information.

    Args:
      task: A task proto defining the RL task.
      max_bad_states: How many bad states in a row are allowed before a restart
        of the simulator is triggered.
      dumpsys_check_frequency: Frequency, in steps, at which to check
        current_activity and view hierarchy
      max_failed_current_activity: The maximum number of tries for extracting
        the current activity before forcing the episode to restart.
    """
    self._task = task
    self._max_bad_states = max_bad_states
    self._dumpsys_check_frequency = dumpsys_check_frequency
    self._max_failed_current_activity = max_failed_current_activity

    self._lock = threading.Lock()
    self._extras_max_buffer_size = 100
    self._adb_controller = None
    self._emulator_stub = None
    self._image_format = None
    self._setup_step_interpreter = None

    self._vocabulary: List[str] = self._task.vocabulary

    # Logging settings
    self._log_dict = {
        'reset_count_step_timeout': 0,
        'reset_count_player_exited': 0,
        'reset_count_episode_end': 0,
        'reset_count_max_duration_reached': 0,
        'restart_count_max_bad_states': 0,
    }

    # zdy
    #  Event Infrastructures {{{ # 
    self._events_with_id: Dict[int, event_listeners.Event] = {}
    self._events_in_need: Dict[int, List[event_listeners.Event]] = {}

    self._text_events: List[event_listeners.TextEvent] = []
    self._icon_events: List[event_listeners.IconRecogEvent] = []
    self._icon_match_events: List[event_listeners.IconMatchEvent] = []
    self._view_hierarchy_events: List[event_listeners.ViewHierarchyEvent] = []
    self._log_events: List[event_listeners.LogEvent] = []
    self._log_filters: Set[str] = set()

    self._score_event: event_listeners.Event =\
      self.parse_event_listeners(task.event_slots.score_listener, cast=float)\
        if task.HasField("event_slots") and task.event_slots.HasField("score_listener")\
        else event_listeners.EmptyEvent()
    self._reward_event: event_listeners.Event =\
      self.parse_event_listeners(task.event_slots.reward_listener, cast=float,
          update=operator.add)\
        if task.HasField("event_slots") and task.event_slots.HasField("reward_listener")\
        else event_listeners.EmptyEvent()
    self._episode_end_event: event_listeners.Event =\
      self.parse_event_listeners(task.event_slots.episode_end_listener)\
        if task.HasField("event_slots") and task.event_slots.HasField("episode_end_listener")\
        else event_listeners.EmptyEvent()

    def _update_dict(buffer_size_limit: int,
        dict1: Dict[str, Any],
        dict2: Dict[str, Any]) -> Dict[str, Any]:
      for k in dict2:
        if k in dict1:
          dict1[k] += dict2[k]
        else:
          dict1[k] = dict2[k]
        if len(dict1[k])>buffer_size_limit:
          dict1[k] = dict1[k][-buffer_size_limit:]
      return dict1
    self._extra_event: event_listeners.Event =\
      self.parse_event_listeners(task.event_slots.extra_listener,
          update=functools.partial(_update_dict, self._extras_max_buffer_size))\
        if task.HasField("event_slots") and task.event_slots.HasField("extra_listener")\
        else event_listeners.EmptyEvent()

    def _parse_json(extra: str) -> Dict[str, Any]:
      try:
        extra = dict(json.loads(extra))
      except ValueError:
        logging.error('JSON string could not be parsed: %s', extra1)
        extra = {}
      return extra
    self._json_extra_event: event_listeners.Event =\
      self.parse_event_listeners(task.event_slots.json_extra_listener,
          wrap=_parse_json,
          update=functools.partial(_update_dict, self._extras_max_buffer_size))\
        if task.HasField("event_slots") and task.event_slots.HasField("json_extra_listener")\
        else event_listeners.EmptyEvent()

    def _update_list(buffer_size_limit: int, instruction1: List[str], instruction2: List[str]) -> List[str]:
      instruction1 += instruction2
      return instruction1
    self._instruction_event: event_listeners.Event =\
      self.parse_event_listeners(task.event_slots.instruction_listener,
          cast=str, wrap=(lambda instrct: instrct if isinstance(instrct, list) else [instrct]),
          update=functools.partial(_update_list, self._extras_max_buffer_size))\
        if task.HasField("event_slots") and task.event_slots.HasField("instruction_listener")\
        else event_listeners.EmptyEvent()

    del self._events_with_id
    del self._events_in_need
    #  }}} Event Infrastructures # 

    # Initialize internal state
    self._task_start_time = None
    self._episode_steps = 0
    self._bad_state_counter = 0
    self._is_bad_episode = False

    self._latest_values = {
        #'reward': 0.0,
        'score': 0.0,
        "player_exited": False,
        #'extra': {},
        #'episode_end': False,
    }

    logging.info('Task config: %s', self._task)
    #  }}} method `__init__` # 

  # zdy
  # TODO: test the correctness
  def parse_event_listeners(self, event_definition: task_pb2.Event,
      cast: Optional[Callable[[V], C]] = None,
      wrap: Optional[Callable[[T], W]] = None,
      update: Optional[Callable[[W, W], W]] = None) -> event_listeners.Event:
    #  method `parse_event_listeners` {{{ # 
    """
    event_definition - task_pb2.Event
    cast - callable accepting the verified type returning the cast type or
      None
    wrap - callable accepting the transformed type returning the wrapped
      type or None
    update - callable accepting
      + the wrapped type
      + the wrapped type
      and returning the wrapped type

    return event_listeners.Event
    """

    def _rect_to_list(rect: task_pb2.Event.Rect) -> List[float]:
      #  function `_rect_to_list` {{{ # 
      """
      rect - task_pb2.Event.Rect

      return list of four floats
      """

      return [rect.x0, rect.y0, rect.x1, rect.y1]
      #  }}} function `_rect_to_list` # 

    transformation = event_definition.transformation if len(event_definition.transformation)>0\
        else "x"

    #  Text Events {{{ # 
    if event_definition.HasField("text_recognize"):
      event = event_listeners.TextEvent(event_definition.text_recognize.expect,
          _rect_to_list(event_definition.text_recognize.rect), needs_detection=False,
          transformation=transformation, cast=cast, wrap=wrap, update=update)
      self._text_events.append(event)
    elif event_definition.HasField("text_detect"):
      event = event_listeners.TextEvent(event_definition.text_detect.expect,
          _rect_to_list(event_definition.text_detect.rect), needs_detection=True,
          transformation=transformation, cast=cast, wrap=wrap, update=update)
      self._text_events.append(event)
    #  }}} Text Events # 
    #  Icon Events {{{ # 
    elif event_definition.HasField("icon_recognize"):
      event = event_listeners.IconRecogEvent(getattr(event_definition.icon_recognize, "class"),
          _rect_to_list(event_definition.icon_recognize.rect), needs_detection=False,
          transformation=transformation, wrap=wrap, update=update)
      self._icon_events.append(event)
    elif event_definition.HasField("icon_detect"):
      event = event_listeners.IconRecogEvent(getattr(event_definition.icon_detect, "class"),
          _rect_to_list(event_definition.icon_detect.rect), needs_detection=True,
          transformation=transformation, wrap=wrap, update=update)
      self._icon_events.append(event)
    #  }}} Icon Events # 
    #  Icon Match Events {{{ # 
    elif event_definition.HasField("icon_match"):
      event = event_listeners.IconMatchEvent(event_definition.icon_match.path,
          _rect_to_list(event_definition.icon_match.rect), needs_detection=False,
          transformation=transformation, wrap=wrap, update=update)
      self._icon_match_events.append(event)
    elif event_definition.HasField("icon_detect_match"):
      event = event_listeners.IconMatchEvent(event_definition.icon_detect_match.path,
          _rect_to_list(event_definition.icon_detect_match.rect), needs_detection=True,
          transformation=transformation, wrap=wrap, update=update)
      self._icon_match_events.append(event)
    #  }}} Icon Match Events # 
    #  Other Events {{{ # 
    elif event_definition.HasField("view_hierarchy_event"):
      properties = []
      for prpt in event_definition.view_hierarchy_event.properties:
        #if not prpt.HasField("property_value"):
          #property_ = event_listeners.ViewHierarchyEvent.PureProperty(prpt.property_name)
        if prpt.HasField("pattern"):
          property_ = event_listeners.ViewHierarchyEvent.StringProperty(prpt.property_name, prpt.pattern)
        else:
          if prpt.sign==task_pb2.Event.ViewHierarchyEvent.Sign.EQ:
            comparator = operator.eq
          elif prpt.sign==task_pb2.Event.ViewHierarchyEvent.Sign.LE:
            comparator = operator.le
          elif prpt.sign==task_pb2.Event.ViewHierarchyEvent.Sign.LT:
            comparator = operator.lt
          elif prpt.sign==task_pb2.Event.ViewHierarchyEvent.Sign.GE:
            comparator = operator.ge
          elif prpt.sign==task_pb2.Event.ViewHierarchyEvent.Sign.GT:
            comparator = operator.gt
          else:
            comparator = operator.ne
          property_ = event_listeners.ViewHierarchyEvent.ScalarProperty(prpt.property_name,
              comparator, getattr(prpt, prpt.WhichOneof("property_value")))
        properties.append(property_)
      event = event_listeners.ViewHierarchyEvent(event_definition.view_hierarchy_event.view_hierarchy_path,
          properties, transformation=transformation, cast=cast, wrap=wrap, update=update)
      self._view_hierarchy_events.append(event)
    elif event_definition.HasField("log_event"):
      self._log_filters |= set(event_definition.log_event.filters)
      event = event_listeners.LogEvent(event_definition.log_event.filters, event_definition.log_event.pattern,
          transformation=transformation, cast=cast, wrap=wrap, update=update)
      self._log_events.append(event)
    #  }}} Other Events # 
    #  Combined Events {{{ # 
    elif event_definition.HasField("or"):
      sub_events = list(
          map(functools.partial(self.parse_event_listeners, cast=cast, wrap=wrap, update=update),
            getattr(event_definition, "or").events))
      event = event_listeners.Or(sub_events, transformation, cast, wrap, update)
    elif event_definition.HasField("and"):
      sub_events = list(
          map(functools.partial(self.parse_event_listeners, cast=cast, wrap=wrap, update=update),
            getattr(event_definition, "and").events))
      event = event_listeners.And(sub_events, transformation, cast, wrap)
    #  }}} Combined Events # 

    #  Handle the prerequisites {{{ # 
    if event_definition.id!=0:
      event_id = event_definition.id
      self._events_with_id[event_id] = event
      if event_id in self._events_in_need:
        for evt in self._events_in_need[event_id]:
          evt.add_prerequisites(event)
        del self._events_in_need[event_id]
    if len(event_definition.prerequisite)>0:
      for evt_id in event_definition.prerequisite:
        if evt_id in self._events_with_id:
          event.add_prerequisites(self._events_with_id[evt_id])
        else:
          if evt_id not in self._events_in_need:
            self._events_in_need[evt_id] = []
          self._events_in_need[evt_id].append(event)
    #  }}} Handle the prerequisites # 

    return event
    #  }}} method `parse_event_listeners` # 

  #  Properties {{{ # 
  def task(self) -> task_pb2.Task:
    return self._task
  def command(self) -> List[str]:
    """
    return list of str
    """

    return self._task.command
  def nb_tokens(self) -> int:
    """
    return int
    """

    return len(self._vocabulary)
  def vocabulary(self) -> List[str]:
    """
    return list of str
    """

    return self._vocabulary
  #  }}} Properties # 

  def increment_steps(self):
    self._episode_steps += 1

  def log_dict(self) -> Dict[str, Any]:
    log_dict = copy.deepcopy(self._log_dict)
    log_dict.update(self._setup_step_interpreter.log_dict())
    return log_dict

  #  Episode Management {{{ # 
  def _reset_counters(self):
    """Reset counters at the end of an RL episode."""

    if not self._is_bad_episode:
      self._bad_state_counter = 0
    self._is_bad_episode = False

    self._episode_steps = 0
    self._task_start_time = datetime.datetime.now()
    with self._lock:
      self._latest_values = {
          #'reward': 0.0,
          'score': 0.0,
          "player_exited": False,
          #'extra': {},
          #'episode_end': False,
      }
      self._score_event.clear()
      self._reward_event.clear()
      self._episode_end_event.clear()
      self._extra_event.clear()
      self._json_extra_event.clear()

  def setup_task(self,
                 adb_controller: adb_control.AdbController,
                 emulator_stub: emulator_controller_pb2_grpc.EmulatorControllerStub, # zdy
                 image_format: emulator_controller_pb2.ImageFormat, # zdy
                 log_stream: log_stream_lib.LogStream,
                 ) -> None:
    """Starts the given task along with all relevant processes."""

    logging.info("#Text Events: {:d}".format(len(self._text_events)))
    logging.info("#Icon Events: {:d}".format(len(self._icon_events)))
    logging.info("#Icon Match Events: {:d}".format(len(self._icon_match_events)))
    logging.info("#VH Events: {:d}".format(len(self._view_hierarchy_events)))
    logging.info("#Log Events: {:d}".format(len(self._log_events)))

    self._adb_controller = adb_controller
    self._emulator_stub = emulator_stub
    self._image_format = image_format
    self._start_logcat_thread(log_stream=log_stream)
    self._start_setup_step_interpreter()
    self._setup_step_interpreter.interpret(self._task.setup_steps)

  def reset_task(self) -> None:
    """Resets a task at the end of an RL episode."""

    self.pause_task()
    self._setup_step_interpreter.interpret(self._task.reset_steps)
    self._resume_task()
    self._reset_counters()

  def pause_task(self) -> None:
    self._stop_dumpsys_thread()
    self._stop_screen_analyzer_thread() # zdy

  def _resume_task(self) -> None:
    self._start_dumpsys_thread()
    self._start_screen_analyzer_thread() # zdy
  #  }}} Episode Management # 

  #  Interaction Methods {{{ # 
  def send_token(token_id: int):
    #  method `send_token` {{{ # 
    """
    token_id - int
    """

    self._adb_controller.input_text(self._vocabulary[token_id] + " ")
    #  }}} method `send_token` # 

  def get_current_reward(self) -> float:
    #  method `get_current_reward` {{{ # 
    """Returns total reward accumulated since the last step."""

    # zdy
    self._run_screen_analyzer()
    try:
      self._run_dumpsys()
    except errors.NotAllowedError:
      self._latest_values["player_exited"] = True

    with self._lock:
      #reward = self._latest_values['reward']
      #self._latest_values['reward'] = 0.0

      # zdy
      if self._score_event.is_set():
        score = self._score_event.get()
        reward = score - self._latest_values["score"]
        self._latest_values["score"] = score
        self._score_event.clear()
      else:
        reward = 0

      reward += self._reward_event.get() if self._reward_event.is_set() else 0 # zdy
      self._reward_event.clear() # zdy
    return reward
    #  }}} method `get_current_reward` # 

  def get_current_extras(self) -> Dict[str, Any]:
    #  method `get_current_extras` {{{ # 
    """Returns task extras accumulated since the last step."""

    with self._lock:
      # zdy
      extras = self._extra_event.get() if self._extra_event.is_set() else {}
      self._extra_event.clear()
      extras = {k: list(map(ast.literal_eval, vals)) for k, vals in extras.items()}

      if self._json_extra_event.is_set():
        json_extras = self._json_extra_event.get()
        self._json_extra_event.clear()

        if not isinstance(json_extras, dict):
          try:
            json_extras = json.loads(json_extras)
          except ValueError:
            logging.error('JSON string could not be parsed: %s', json_extras)
            json_extras = {}

        for k in json_extras:
          if k in extras:
            extras[k] += json_extras[k]
          else:
            extras[k] = json_extras[k]

      #for name, values in self._latest_values['extra'].items(): # zdy
      for name, values in extras.items(): # zdy
        extras[name] = np.stack(values)
      #self._latest_values['extra'] = {} # zdy
      return extras
    #  }}} method `get_current_extras` # 

  def get_current_instructions(self) -> List[str]:
    #  function `get_current_instructions` {{{ # 
    """
    return list of str
    """

    instructions = self._instruction_event.get() if self._instruction_event.set() else []
    self._instruction_event.clear()

    if not isinstance(instructions, list):
      instructions = [instructions]

    return instructions
    #  }}} function `get_current_instructions` # 

  def check_if_episode_ended(self) -> bool:
    #  method `check_if_episode_ended` {{{ # 
    """Determines whether the episode should be terminated and reset."""

    # Check if player existed the task
    #if self._check_player_exited():
    if self._latest_values["player_exited"]:
      self._log_dict['reset_count_player_exited'] += 1
      logging.warning('Player exited the game. Ending episode.')
      logging.info('************* END OF EPISODE *************')
      return True

    # Check if episode has ended
    with self._lock:
      #if self._latest_values['episode_end']: # zdy
      if self._episode_end_event.is_set(): # zdy
        self._log_dict['reset_count_episode_end'] += 1
        logging.info('End of episode from logcat! Ending episode.')
        logging.info('************* END OF EPISODE *************')
        return True

    # Check if step limit or time limit has been reached
    if self._task.max_num_steps > 0:
      if self._episode_steps > self._task.max_num_steps:
        self._log_dict['reset_count_max_duration_reached'] += 1
        logging.info('Maximum task duration (steps) reached. Ending episode.')
        logging.info('************* END OF EPISODE *************')
        return True

    if self._task.max_duration_sec > 0.0:
      task_duration = datetime.datetime.now() - self._task_start_time
      max_duration_sec = self._task.max_duration_sec
      if task_duration > datetime.timedelta(seconds=int(max_duration_sec)):
        self._log_dict['reset_count_max_duration_reached'] += 1
        logging.info('Maximum task duration (sec) reached. Ending episode.')
        logging.info('************* END OF EPISODE *************')
        return True

    return False
    #  }}} method `check_if_episode_ended` # 

  #  Deprecated `_check_player_exited` method {{{ # 
  # zdy
  #def _check_player_exited(self) -> bool:
    #"""Returns whether the player has exited the game."""
    #try:
      #self._check_player_exited_impl()
      #return False
    #except errors.NotAllowedError:
      #return True
  #  }}} Deprecated `_check_player_exited` method # 

  #def _check_player_exited_impl(self):
  def _run_dumpsys(self): # zdy
    #  method `_run_dumpsys` {{{ # 
    """Raises an error if the OS is not in an allowed state."""

    if not hasattr(self, '_dumpsys_thread'):
      return

    self._dumpsys_thread.write(
        dumpsys_thread.DumpsysThread.Signal.FETCH_DUMPSYS)

    try:
      v = self._dumpsys_thread.read(block=False) # ZDY_COMMENT: TODO: whether block or not and a probable proper timeout value could be tested.
      if v == dumpsys_thread.DumpsysThread.Signal.USER_EXITED_ACTIVITY:
        self._increment_bad_state()
        raise errors.PlayerExitedActivityError()
      elif v == dumpsys_thread.DumpsysThread.Signal.USER_EXITED_VIEW_HIERARCHY:
        self._increment_bad_state()
        raise errors.PlayerExitedViewHierarchyError()
    except queue.Empty:
      pass  # Don't block here, just ignore if we have nothing.
    #  }}} method `_run_dumpsys` # 

  # zdy
  def _run_screen_analyzer(self):
    #  method `_run_screen_analyzer` {{{ # 
    if not hasattr(self, "_screen_analyzer_thread"):
      return

    self._screen_analyzer_thread.write(
      screen_analyzer_thread.ScreenAnalyzerThread.Signal.CHECK_SCREEN)

    try:
      status = self._screen_analyzer_thread.read(block=True, timeout=0.05) # TODO: maybe a better timeout value could be tuned to
      if status==screen_analyzer_thread.ScreenAnalyzerThread.Signal.CHECK_ERROR:
        logging.error("Screen Analyzer Error!")
      elif status==screen_analyzer_thread.ScreenAnalyzerThread.Signal.DID_NOT_CHECK:
        logging.info("Screen Analyzer did not check, maybe owing to the kill signal.")
    except queue.Empty:
      logging.warning("Screen Analyzer exceeds time limit!")
    #  }}} method `_run_screen_analyzer` # 
  #  }}} Interaction Methods # 

  #  Methods to Start and Stop the Assistant Threads {{{ # 
  def _start_setup_step_interpreter(self):
    self._setup_step_interpreter = setup_step_interpreter.SetupStepInterpreter(
        adb_controller=self._adb_controller,
        logcat=self._logcat_thread)

  def _start_logcat_thread(self, log_stream: log_stream_lib.LogStream):
    #self._logcat_thread = logcat_thread.LogcatThread(
        #log_stream=log_stream,
        #log_parsing_config=self._task.log_parsing_config)
    # zdy
    self._logcat_thread = logcat_thread.LogcatThread(
        log_stream=log_stream,
        log_filter=self._log_filters)

    #for event_listener in self._logcat_listeners():
    for event_listener in self._log_events: # zdy
      self._logcat_thread.add_event_listener(event_listener)

  def _start_dumpsys_thread(self):
    app_screen_checker_ = app_screen_checker.AppScreenChecker(
        self._adb_controller, self._task.expected_app_screen)
    app_screen_checker_.add_event_listeners(*self._view_hierarchy_events)
    self._dumpsys_thread = dumpsys_thread.DumpsysThread(
        app_screen_checker=app_screen_checker_,
        check_frequency=self._dumpsys_check_frequency,
        max_failed_current_activity=self._max_failed_current_activity,
        lock=self._lock,
        block_input=True,
        block_output=True)

  # zdy
  def _start_screen_analyzer_thread(self):
    #  method `_start_screen_analyzer_thread` {{{ # 
    # ZDY_COMMENT: TODO: instantiate models according to requirements

    text_detector = naive_functions.naive_text_detector
    text_recognizer = naive_functions.naive_text_recognizer
    icon_detector = naive_functions.naive_icon_detector
    icon_recognizer = naive_functions.naive_icon_recognizer
    icon_matcher = naive_functions.naive_icon_matcher

    self._screen_analyzer_thread = screen_analyzer_thread.ScreenAnalyzerThread(
        text_detector, text_recognizer,
        icon_detector, icon_recognizer, icon_matcher,
        self._emulator_stub, self._image_format,
        lock=self._lock,
        block_input=True, block_output=True)
    self._screen_analyzer_thread.add_text_event_listeners(*self._text_events)
    self._screen_analyzer_thread.add_icon_event_listeners(*self._icon_events)
    self._screen_analyzer_thread.add_icon_match_event_listeners(*self._icon_match_events)

    #  }}} method `_start_screen_analyzer_thread` # 

  def _stop_logcat_thread(self):
    if hasattr(self, '_logcat_thread'):
      self._logcat_thread.kill()

  def _stop_dumpsys_thread(self):
    if hasattr(self, '_dumpsys_thread'):
      self._dumpsys_thread.kill()

  # zdy
  def _stop_screen_analyzer_thread(self):
    if hasattr(self, "_screen_analyzer_thread"):
      self._screen_analyzer_thread.kill()
  #  }}} Methods to Start and Stop the Assistant Threads # 

  def _increment_bad_state(self) -> None:
    """Increments the bad state counter.

    Bad states are errors that shouldn't happen and that trigger an
    episode reset. If enough bad states have been seen consecutively,
    we restart the simulation in the hope of returning the simulation
    to a good state.
    """
    logging.warning('Bad state detected.')
    if self._max_bad_states:
      self._is_bad_episode = True
      self._bad_state_counter += 1
      logging.warning('Bad state counter: %d.', self._bad_state_counter)
      if self._bad_state_counter >= self._max_bad_states:
        logging.error('Too many consecutive bad states. Restarting simulator.')
        self._log_dict['restart_count_max_bad_states'] += 1
        self._should_restart = True
    else:
      logging.warning('Max bad states not set, bad states will be ignored.')

  # ZDY_COMMENT: I think it is time to obsolete this method
  def _logcat_listeners(self):
    #  method `_logcat_listeners` {{{ # 
    """Creates list of EventListeners for logcat thread."""

    # Defaults to 'a^' since that regex matches no string by definition.
    regexps = self._task.log_parsing_config.log_regexps
    listeners = []

    # Reward listeners
    def _reward_handler(event, match):
      del event
      reward = float(match.group(1))
      with self._lock:
        self._latest_values['reward'] += reward
        # ZDY_COMMENT: `_latest_values['reward']` is cleared during revoking `get_current_reward`

    for regexp in regexps.reward:
      listeners.append(logcat_thread.EventListener(
          regexp=re.compile(regexp or 'a^'),
          handler_fn=_reward_handler))

    # RewardEvent listeners
    # ZDY_COMMENT: RewardEvent returns a constant reward regardless of the log detail
    for reward_event in regexps.reward_event:

      def get_reward_event_handler(reward):
        def _reward_event_handler(event, match):
          del event, match
          with self._lock:
            self._latest_values['reward'] += reward
        return _reward_event_handler

      listeners.append(logcat_thread.EventListener(
          regexp=re.compile(reward_event.event or 'a^'),
          handler_fn=get_reward_event_handler(reward_event.reward)))

    # Score listener
    # ZDY_COMMENT: the increment of the score constructs the reward
    def _score_handler(event, match):
      del event
      current_score = float(match.group(1))
      with self._lock:
        current_reward = current_score - self._latest_values['score']
        self._latest_values['score'] = current_score
        self._latest_values['reward'] += current_reward

    listeners.append(logcat_thread.EventListener(
        regexp=re.compile(regexps.score or 'a^'),
        handler_fn=_score_handler))

    # Episode end listeners
    def _episode_end_handler(event, match):
      del event, match
      with self._lock:
        self._latest_values['episode_end'] = True

    for regexp in regexps.episode_end:
      listeners.append(logcat_thread.EventListener(
          regexp=re.compile(regexp or 'a^'),
          handler_fn=_episode_end_handler))

    # Extra listeners
    def _extras_handler(event, match):
      del event
      extra_name = match.group('name')
      extra = match.group('extra')
      if extra:
        try:
          extra = ast.literal_eval(extra)
          # ZDY_BOOKMARK: What's exatly in this
          # ZDY_COMMENT: oh, got it, maybe a list of basic type elements
        # Except all to avoid unnecessary crashes, only log error.
        except Exception:  # pylint: disable=broad-except
          logging.exception('Could not parse extra: %s', extra)
      else:
        # No extra value provided for boolean extra. Setting value to True.
        extra = 1
      _process_extra(extra_name, extra)

    for regexp in regexps.extra:
      listeners.append(logcat_thread.EventListener(
          regexp=re.compile(regexp or 'a^'),
          handler_fn=_extras_handler))

    # JSON extra listeners
    def _json_extras_handler(event, match):
      del event
      extra_data = match.group('json_extra')
      try:
        extra = dict(json.loads(extra_data))
      except ValueError:
        logging.error('JSON string could not be parsed: %s', extra_data)
        return
      for extra_name, extra_value in extra.items():
        _process_extra(extra_name, extra_value)

    for regexp in regexps.json_extra:
      listeners.append(logcat_thread.EventListener(
          regexp=re.compile(regexp or 'a^'),
          handler_fn=_json_extras_handler))

    def _process_extra(extra_name, extra):
      extra = np.array(extra)
      with self._lock:
        latest_extras = self._latest_values['extra']
        if extra_name in latest_extras:
          # If latest extra is not flushed, append.
          if len(latest_extras[extra_name]) >= self._extras_max_buffer_size:
            latest_extras[extra_name].pop(0)
          latest_extras[extra_name].append(extra)
        else:
          latest_extras[extra_name] = [extra]
        self._latest_values['extra'] = latest_extras
    # ZDY_COMMENT: multiple latest extras are buffered, maybe for the purpose to preserve the information of dynamics

    return listeners
    #  }}} method `_logcat_listeners` # 

  def close(self):
    if hasattr(self, '_logcat_thread'):
      self._logcat_thread.kill()
    if hasattr(self, '_dumpsys_thread'):
      self._dumpsys_thread.kill()
    # zdy
    if hasattr(self, "_screen_analyzer_thread"):
      self._screen_analyzer_thread.kill()
