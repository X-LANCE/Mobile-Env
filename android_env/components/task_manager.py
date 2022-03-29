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
from typing import Any, Dict
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
      emulator_stub: emulator_controller_pb2_grpc.EmulatorControllerStub = None, # zdy
      image_format: emulator_controller_pb2.ImageFormat = None, # zdy
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
      emulator_stub: Used by the screen analyzer to capture the screenshot.
      image_format: Used by the screen analyzer to parse the screenshot
    """
    self._task = task
    self._max_bad_states = max_bad_states
    self._dumpsys_check_frequency = dumpsys_check_frequency
    self._max_failed_current_activity = max_failed_current_activity

    self._lock = threading.Lock()
    self._extras_max_buffer_size = 100
    self._adb_controller = None
    self._setup_step_interpreter = None
    self._emulator_stub = emulator_stub # zdy

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
    self._text_events = []
    self._icon_events = []
    self._icon_match_events = []
    self._view_hierarchy_events = []
    self._log_events = []
    self._log_filters = set()

    self._score_event = self.parse_event_listeners(task.score_listener, cast=int)\
        if task.HasField("score_listener") else event_listeners.EmptyEvent()
    self._reward_event = self.parse_event_listeners(task.reward_listener, cast=int,
          update=operator.add)\
        if task.HasField("reward_listener") else event_listeners.EmptyEvent()
    self._episode_end_event = self.parse_event_listeners(task.episode_end_listener)\
        if task.HasField("episode_end_listener") else event_listeners.EmptyEvent()

    def _update_dict(buffer_size_limit, dict1, dict2):
      for k in dict2:
        if k in dict1:
          dict1[k] += dict2[k]
        else:
          dict1[k] = dict2[k]
        if len(dict1[k])>buffer_size_limit:
          dict1[k] = dict1[k][-buffer_size_limit:]
      return dict1
    self._extra_event = self.parse_event_listeners(task.extra_listener,
          update=functools.partial(_update_dict, self._extras_max_buffer_size))\
        if task.HasField("extra_listener") else event_listeners.EmptyEvent()

    def _update_json_extra(buffer_size_limit, extra1, extra2):
      try:
        extra1 = extra1 if isinstance(extra1, dict) else dict(json.loads(extra1))
      except ValueError:
        logging.error('JSON string could not be parsed: %s', extra1)
        extra1 = {}
      try:
        extra2 = dict(json.loads(extra2))
      except ValueError:
        logging.error('JSON string could not be parsed: %s', extra2)
        extra2 = {}
      return _update_dict(buffer_size_limit, extra1, extra2)
    self._json_extra_event = self.parse_event_listeners(task.json_extra_listener,
          update=functools.partial(_update_json_extra, self._extras_max_buffer_size))\
        if task.HasField("json_extra_listener") else event_listeners.EmptyEvent()
    #  }}} Event Infrastructures # 

    # Initialize internal state
    self._task_start_time = None
    self._episode_steps = 0
    self._bad_state_counter = 0
    self._is_bad_episode = False

    self._latest_values = {
        #'reward': 0.0,
        'score': 0.0,
        #'extra': {},
        #'episode_end': False,
    }

    logging.info('Task config: %s', self._task)
    #  }}} method `__init__` # 

  # zdy
  # TODO: test the correctness
  def parse_event_listeners(self, event_definition, cast=None, update=None):
    #  method `parse_event_listeners` {{{ # 
    """
    event_definition - task_pb2.Event
    cast - callable accepting something returning something else or None
    update - callable accepting
      + something as `self._value`
      + something as the new value
      and returning something

    return event_listeners.Event
    """

    def _rect_to_list(rect):
      #  function `_rect_to_list` {{{ # 
      """
      rect - task_pb2.Event.Rect

      return list of four floats
      """

      return [rect.x0, rect.y0, rect.x1, rect.y1]
      #  }}} function `_rect_to_list` # 

    #  Text Events {{{ # 
    if event_definition.HasField("text_recognize"):
      event = event_listeners.TextEvent(event_definition.text_recognize.expect,
          _rect_to_list(event_definition.text_recognize.rect), needs_detection=False,
          transformation=event_definition.transformation, cast=cast, update=update)
      self._text_events.append(event)
      return event
    if event_definition.HasField("text_detect"):
      event = event_listeners.TextEvent(event_definition.text_detect.expect,
          _rect_to_list(event_definition.text_detect.rect), needs_detection=True,
          transformation=event_definition.transformation, cast=cast, update=update)
      self._text_events.append(event)
      return event
    #  }}} Text Events # 

    #  Icon Events {{{ # 
    if event_definition.HasField("icon_recognize"):
      event = event_listeners.IconRecogEvent(event_definition.icon_recognize.class,
          _rect_to_list(event_definition.icon_recognize.rect), needs_detection=False,
          transformation=event_definition.transformation, update=update)
      self._icon_events.append(event)
      return event
    if event_definition.HasField("icon_detect"):
      event = event_listeners.IconRecogEvent(event_definition.icon_detect.class,
          _rect_to_list(event_definition.icon_detect.rect), needs_detection=True,
          transformation=event_definition.transformation, update=update)
      self._icon_events.append(event)
      return event
    #  }}} Icon Events # 

    #  Icon Match Events {{{ # 
    if event_definition.HasField("icon_match"):
      event = event_listeners.IconMatchEvent(event_definition.icon_match.path,
          _rect_to_list(event_definition.icon_match.rect), needs_detection=False,
          transformation=event_definition.transformation, update=update)
      self._icon_match_events.append(event)
      return event
    if event_definition.HasField("icon_detect_match"):
      event = event_listeners.IconMatchEvent(event_definition.icon_detect_match.path,
          _rect_to_list(event_definition.icon_detect_match.rect), needs_detection=True,
          transformation=event_definition.transformation, update=update)
      self._icon_match_events.append(event)
      return event
    #  }}} Icon Match Events # 

    #  Other Events {{{ # 
    if event_definition.HasField("view_hierarchy_event"):
      properties = []
      for prpt in event_definition.view_hierarchy_event.properties:
        if not prpt.HasField("property_value"):
          property_ = event_listeners.ViewHierarchyEvent.PureProperty(prpt.property_name)
        elif prpt.HasField("pattern"):
          property_ = event_listeners.ViewHierarchyEvent.StringProperty(prpt.property_name, prpt.pattern)
        else:
          property_ = event_listeners.ViewHierarchyEvent.ScalarProperty(prpt.property_name,
              getattr(prpt, prpt.WhichOneof("property_value")))
        properties.append(property_)
      event = event_listeners.ViewHierarchyEvent(event_definition.view_hierarchy_event.view_hierarchy_path,
          properties, transformation=event_definition.transformation, cast=cast, update=update)
      self._view_hierarchy_events.append(event)
      return event
    if event_definition.HasField("log_event"):
      self._log_filters |= set(event_definition.log_event.filters)
      event = event_listeners.LogEvent(event_definition.log_event.filters, event_definition.log_event.pattern,
          transformation=event_definition.transformation, cast=cast, update=update)
      self._log_events.append(event)
      return event
    #  }}} Other Events # 

    #  Combined Events {{{ # 
    if event_definition.HasField("or"):
      sub_events = list(
          map(functools.partial(self.parse_event_listeners, cast=cast, update=update),
            getattr(event_definition, "or").events))
      return event_listeners.Or(sub_events, event_definition.transformation, cast, update)
    if event_definition.HasField("and"):
      sub_events = list(
          map(functools.partial(self.parse_event_listeners, cast=cast, update=update),
            getattr(event_definition, "and").events))
      return event_listeners.And(sub_events, event_definition.transformation, cast, update)
    #  }}} Combined Events # 
    #  }}} method `parse_event_listeners` # 

  def task(self) -> task_pb2.Task:
    return self._task

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
                 log_stream: log_stream_lib.LogStream) -> None:
    """Starts the given task along with all relevant processes."""

    self._adb_controller = adb_controller
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
  def get_current_reward(self) -> float:
    """Returns total reward accumulated since the last step."""

    with self._lock:
      #reward = self._latest_values['reward']
      #self._latest_values['reward'] = 0.0
      score = self._score_event.get() if self._score_event.is_set() else 0 # zdy
      reward = score - self._latest_values["score"]
      self._latest_values["score"] = score
      self._score_event.clear()

      reward += self._reward_event.get() if self._reward_event.is_set() else 0 # zdy
      self._reward_event.clear() # zdy
    return reward

  def get_current_extras(self) -> Dict[str, Any]:
    """Returns task extras accumulated since the last step."""

    with self._lock:
      # zdy
      extras = self._extra_event.get() if self._extra_event.is_set() else {}
      self._extra_event.clear()

      if self._json_extra_event.is_set():
        json_extras = self._json_extra_event.get()

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

        self._json_extra_event.clear()

      #for name, values in self._latest_values['extra'].items(): # zdy
      for name, values in extras.items(): # zdy
        extras[name] = np.stack(values)
      #self._latest_values['extra'] = {} # zdy
      return extras

  def check_if_episode_ended(self) -> bool:
    """Determines whether the episode should be terminated and reset."""

    # Check if player existed the task
    if self._check_player_exited():
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

  def _check_player_exited(self) -> bool:
    """Returns whether the player has exited the game."""
    try:
      self._check_player_exited_impl()
      return False
    except errors.NotAllowedError:
      return True

  def _check_player_exited_impl(self):
    """Raises an error if the OS is not in an allowed state."""

    if not hasattr(self, '_dumpsys_thread'):
      return

    self._dumpsys_thread.write(
        dumpsys_thread.DumpsysThread.Signal.FETCH_DUMPSYS)

    try:
      v = self._dumpsys_thread.read(block=False)
      if v == dumpsys_thread.DumpsysThread.Signal.USER_EXITED_ACTIVITY:
        self._increment_bad_state()
        raise errors.PlayerExitedActivityError()
      elif v == dumpsys_thread.DumpsysThread.Signal.USER_EXITED_VIEW_HIERARCHY:
        self._increment_bad_state()
        raise errors.PlayerExitedViewHierarchyError()
    except queue.Empty:
      pass  # Don't block here, just ignore if we have nothing.
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
    self._dumpsys_thread = dumpsys_thread.DumpsysThread(
        app_screen_checker=app_screen_checker.AppScreenChecker(
            self._adb_controller, self._task.expected_app_screen),
        check_frequency=self._dumpsys_check_frequency,
        max_failed_current_activity=self._max_failed_current_activity,
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
        block_input=True, block_output=True)
    self._screen_analyzer_thread.add_text_event_listeners(self._text_events)
    self._screen_analyzer_thread.add_icon_event_listeners(self._icon_events)
    self._screen_analyzer_thread.add_icon_match_event_listeners(self._icon_match_events)

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
