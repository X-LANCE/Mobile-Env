# vim: set tabstop=2 shiftwidth=2:
# coding=utf-8
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
# 
# Revised by Danyang Zhang @X-Lance based on
# 
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

"""Coordinator handles interaction between internal components of AndroidEnv."""

import copy
import socket
import time
from typing import Any, Optional, Iterable, Union
from typing import Dict, Tuple, List

from absl import logging
from android_env.components import action_type as action_type_lib
from android_env.components import errors
from android_env.components import specs
from android_env.components import task_manager as task_manager_lib
from android_env.components.simulators import base_simulator
import dm_env
import numpy as np
import lxml.etree
import itertools

import enum
from numbers import Number

class EventCheckControl(enum.Flag):
  # Checks after each LIFT
  LIFT = enum.auto()

  # Checks after each TEXT
  TEXT = enum.auto()

  # Checks every t seconds; prior to STEP
  TIME = enum.auto()

  # Checks every n steps
  STEP = enum.auto()

class Coordinator():
  """Handles interaction between internal components of AndroidEnv."""

  def __init__( self
              , simulator: base_simulator.BaseSimulator
              , task_managers: Iterable[task_manager_lib.TaskManager]
              , step_timeout_sec: int = 10
              , max_steps_per_sec: float = 15.0
              , periodic_restart_time_min: float = 0.0
              , force_simulator_launch: bool = True
              , with_view_hierarchy: bool = False
              , vh_check_control_method: EventCheckControl = EventCheckControl.LIFT
              , vh_check_control_value: Optional[Union[float, int]] = 3.
              , screen_check_control_method: EventCheckControl = EventCheckControl.LIFT
              , screen_check_control_value: Optional[Union[float, int]] = 1.
  ):
    #  method `__init__` {{{ # 
    """Handles communication between AndroidEnv and its components.

    Args:
      simulator (base_simulator.BaseSimulator): A BaseSimulator instance.
      task_managers (Iterable[task_manager_lib.TaskManager]): iterable of
        task_manager_lib.TaskManager as the TaskManagers, responsible for
        coordinating RL tasks.

      step_timeout_sec (int): Timeout in seconds between steps. If step is not
        called within that time, the episode will reset at the next step. Set
        to 0 to disable.
      max_steps_per_sec (float): Maximum steps per second. If the simulator is
        faster, the Coordinator will wait before returning an observation.  If
        <=0.0, this functionality is turned off.
      periodic_restart_time_min (float): Time between periodic restarts in
        minutes.  If > 0.0, will trigger a simulator restart at the end of the
        next episode once the time has been reached.
      force_simulator_launch (bool): Forces the simulator to relaunch even if
        it is already launched.

      with_view_hierarchy (bool): if the view hierarchy should be included in
        the observation
      vh_check_control_method (EventCheckControl): control method
      vh_check_control_value (Optional[Union[float, int]]): only required for
        method TIME or STEP. for TIME, specifies the gap seconds as float. for
        STEP, specifies the gap steps as interger.

      screen_check_control_method (EventCheckControl): control method
      screen_check_control_value (Optional[Union[float, int]]): the seconds or
        steps of check gap for TIME and STEP
    """

    self._simulator: base_simulator.BaseSimulator = simulator
    self._task_manager_list: List[task_manager_lib.TaskManager] = list(task_managers)
    self._task_manager_index: int = 0
    self._task_manager: task_manager_lib.TaskManager = self._task_manager_list[self._task_manager_index]

    self._step_timeout_sec = step_timeout_sec
    self._max_steps_per_sec = max_steps_per_sec
    self._periodic_restart_time_min = periodic_restart_time_min
    self._force_simulator_launch = force_simulator_launch

    self._with_view_hierarchy: bool = with_view_hierarchy
    self._vh_check_control_method: EventCheckControl = vh_check_control_method
    self._vh_check_control_value: Number = vh_check_control_value or 0
    self._screen_check_control_method: EventCheckControl = screen_check_control_method
    self._screen_check_control_value: Number = screen_check_control_value or 0

    # Logging settings.
    self._log_dict = {
        'total_steps': 0,
        'episode_steps': 0,
        'restart_count': 0,
        'restart_count_periodic': 0,
        'restart_count_setup_steps': 0,
        'restart_count_reset_steps': 0,
        'restart_count_simulator_launch': 0,
        'restart_count_simulator_reset': 0,
        'restart_count_execute_action': 0,
        'restart_count_fetch_observation': 0,
        'restart_count_step_timeout': 0,
    }

    # Initialize counters.
    self._should_restart: bool = False
    self._latest_observation_time: Optional[float] = None
    self._simulator_start_time: Optional[float] = None

    self._last_screen_check_time: Optional[float] = None
    self._last_vh_check_time: Optional[float] = None
    self._elapsed_step_from_screen_check: int = -1
    self._elapsed_step_from_vh_check: int = -1

    logging.info('Starting the simulator...')
    self._restart_simulator()
    #  }}} method `__init__` # 

  #  Informational Interfaces {{{ # 
  def action_spec(self) -> Dict[str, dm_env.specs.Array]:
    num_tokens = self._task_manager.nb_tokens()
    num_fingers = self._simulator.num_fingers()
    return specs.base_action_spec(num_tokens=num_tokens, num_fingers=num_fingers)

  def observation_spec(self) -> Dict[str, dm_env.specs.Array]:
    screen_dims = self._simulator.screen_dimensions()
    return specs.base_observation_spec(
        height=screen_dims[0], width=screen_dims[1])

  def task_extras_spec(self) -> Dict[str, dm_env.specs.Array]:
    return specs.base_task_extras_spec(task=self._task_manager.task())

  def command(self) -> List[str]:
    """
    return list of str
    """

    return self._task_manager.command()
  def vocabulary(self) -> List[str]:
    """
    return list of str
    """

    return self._task_manager.vocabulary()

  @property
  def nb_tasks(self) -> int:
    return len(self._task_manager_list)
  @property
  def task_index(self) -> int:
    return self._task_manager_index
  @property
  def task_id(self) -> str:
    return self._task_manager.task().id
  @property
  def task_name(self) -> str:
    return self._task_manager.task().name
  @property
  def task_description(self) -> str:
    return self._task_manager.task().description
  #  }}} Informational Interfaces # 

  #  Reset Interfaces {{{ # 
  def reset_environment_state(self):
    """Resets the state of the simulation for a new RL episode.

    This involves resetting relevant counters and performing reset steps
    specific to the running task (e.g. restarting an application). A lift
    action is also performed to ensure that sequential touches are not
    interconnected between separate RL episodes.
    """

    # Restart the simulation if neccessary.
    if self._should_restart or self._should_periodic_restart():
      self._restart_simulator()

    # Reset counters.
    self._latest_observation_time = None
    self._last_screen_check_time = None
    self._last_vh_check_time = None
    self._elapsed_step_from_screen_check = -1
    self._elapsed_step_from_vh_check = -1
    for key in self._log_dict:
      if key.startswith('episode'):
        self._log_dict[key] = 0.0

    # Execute a lift action before resetting the task.
    self._lift_all_fingers()

    # Reset the task.
    try:
      self._task_manager.reset_task()
      self._simulator.update_device_orientation() # ZDY_COMMENT: device orientation updated only during reset
    except errors.StepCommandError:
      logging.exception('Failed to reset the task. Restarting simulator.')
      self._log_dict['restart_count_simulator_reset'] += 1
      self._should_restart = True

  def _lift_all_fingers(self) -> None:
    """Performs a lift action with every finger."""
    lift_action = {
        'action_type': np.array(action_type_lib.ActionType.LIFT),
        'touch_position': np.array([0, 0]),
    }
    for i in range(2, self._simulator.num_fingers()+1):
      lift_action.update({
          f'action_type_{i}': np.array(action_type_lib.ActionType.LIFT),
          f'touch_position_{i}': np.array([0, 0]),
      })
    self._send_action_to_simulator(lift_action)

  def _should_periodic_restart(self) -> bool:
    """Checks if it is time to restart the simulator.

    If a periodic restart time was specified, the Coordinator will re-launch
    the simulator at regular time intervals. This helps to make sure that the
    simulator is not is a stale state even if the environment has been running
    for a significant amount of time.

    Returns:
      Boolean indicating if it is time to restart the simulator.
    """

    if self._periodic_restart_time_min and self._simulator_start_time:
      sim_alive_time = (time.time() - self._simulator_start_time) / 60.0
      logging.info('Simulator has been running for %f mins', sim_alive_time)
      if sim_alive_time > self._periodic_restart_time_min:
        logging.info('Maximum alive time reached. Restarting simulator.')
        self._log_dict['restart_count_periodic'] += 1
        return True
    return False

  def _restart_simulator(self, max_retries: int = 3):
    """Restarts the simulation.

    Closes and re-launches the system, restarting the simulator process and
    reinitializing the task in the newly started simulator.

    Args:
      max_retries: Number of times to attempt a restart before raising an error.
    """

    # Reset counters.
    self._should_restart = False

    # Attempt to restart the system a given number of times.
    num_tries = 1
    while True:
      if num_tries > max_retries:
        logging.error('Maximum number of restarts reached.')
        raise errors.TooManyRestartsError
      logging.info('Simulator launch attempt %d of %d', num_tries, max_retries)

      # Launch the simulator (will restart if already launched).
      try:
        if self._force_simulator_launch or not self._simulator.is_launched():
          self._task_manager.pause_task()
          self._simulator.launch()
          self._simulator_start_time = time.time()
        if not hasattr(self, "_adb_controller") or self._adb_controller is None:
          self._adb_controller = self._simulator.create_adb_controller()
        log_stream = self._simulator.get_log_stream()
      except errors.AdbControllerError:
        logging.error('Error launching the simulator.')
        self._log_dict['restart_count_simulator_launch'] += 1
        num_tries += 1
        continue

      # Start the task.
      for t_mng in self._task_manager_list:
        t_mng.clear_setup_flag()
      try:
        self._task_manager.setup_task(
            adb_controller=self._adb_controller,
            #emulator_stub=self._simulator.get_emulator_stub(), # zdy
            #image_format=self._simulator.image_format, # zdy
            log_stream=log_stream)
      except errors.StepCommandError:
        logging.error('Failed to set up the task. Restarting simulator.')
        self._log_dict['restart_count_setup_steps'] += 1
        num_tries += 1
        continue

      # Restart was successful.
      break

  def add_task_manager(self, task_manager: task_manager_lib.TaskManager):
    #  method `add_task_manager` {{{ # 
    """
    Args:
        task_manager: task_manager_lib.TaskManager
    """

    self._task_manager_list.append(task_manager)
    #  }}} method `add_task_manager` # 

  def switch_task_manager(self, index: int):
    #  method `change_task_manager` {{{ # 
    self._task_manager_index = index
    self._task_manager = self._task_manager_list[self._task_manager_index]

    if not self._task_manager.setup_flag():
      try:
        self._task_manager.setup_task(
            adb_controller=self._adb_controller,
            #emulator_stub=self._simulator.get_emulator_stub(), # zdy
            #image_format=self._simulator.image_format, # zdy
            log_stream=self._simulator.get_log_stream())
      except errors.StepCommandError:
        logging.error('Failed to set up the task. Restarting simulator.')
        self._log_dict['restart_count_setup_steps'] += 1
        self._should_restart = True

    self.reset_environment_state()
    #  }}} method `change_task_manager` # 
  #  }}} Reset Interfaces # 

  def execute_action( self
                    , action: Optional[ Union[ Dict[str, np.ndarray]
                                             , List[Dict[str, np.ndarray]]
                                             ]
                                      ]
                    ) -> Tuple[ Optional[ Dict[ str
                                              , Union[ np.ndarray
                                                     , Optional[lxml.etree.Element]
                                                     ]
                                              ]
                                        ]
                              , float
                              , Dict[str, Any]
                              , List[str]
                              , bool
                              ]:
    #  method execute_action {{{ # 
    """Executes the selected action and returns transition info.

    Args:
      action (Optional[Dict[str, Optional[Union[np.ndarray, str]]]]): Selected
        action to perform on the simulated Android device. dict like
          {
            "action_type": action_type_lib.ActionType
            "touch_position": np.ndarray with shape (2,) of float32 as [x, y]
              from [0, 1], optional for TEXT
            "input_token": np.ndarray with shape () of int32, required only for
              TEXT
            "response": np.ndarray with shape () of object (str), optional
              response to human user
          }
          of list of such dicts (if the simulator supports)

    Returns:
      Optional[Dict[str, Union[np.ndarray, Optional[lxml.etree.Element]]]]:
        observation, dict like
          {
            "observation": np.ndarray with shape (H, W, 3) of uint8, Pixel
              observations as displayed on the screen.
            "orientation": np.ndarray with shape (4,) of uint8
            "timedelta": np.ndarray with shape () of int64
            "view_hierarchy": optional lxml.etree.Element, present if
              `self._with_view_hierarchy`
          }
      float: reward, Total reward collected since the last call.
      Dict[str, Any]: extras, Task extras observed since the last call.
      List[str]: instructions, Task instructions received since the last call.
      bool: episode end, Boolean indicating if the RL episode should be terminated.
    """

    # Increment counters.
    self._task_manager.increment_steps()
    if action is not None:
      self._log_dict['total_steps'] += 1
      self._log_dict['episode_steps'] += 1

    # If a restart is neccessary, end the episode.
    if self._should_restart or self._check_timeout():
      return None, 0.0, {}, [], True

    if isinstance(action, list):
      responses: Iterable[str] = filter( lambda rsp: rsp is not None and rsp != ""
                                       , map( lambda act: act.get("response", np.array("")).item()
                                            , action
                                            )
                                       )
      for rsp in responses:
        self._task_manager.receive_response(rsp)

      actions: Iterable[Tuple[int, Dict[str, np.ndarray]]] =\
          map( lambda act: ( np.clip(act["action_type"]-1, 0, 2).item() # 0 for TOUCH & LIFT (simulator), 1 for REPEAT, 2 for TEXT (taskmanager)
                           , act
                           )
             , action
             )
      actions: Iterable[int, Iterable[Tuple[int, Dict[str, np.ndarray]]]] =\
          itertools.groupby( actions
                           , key=(lambda act: act[0])
                           )
      for act_t, act in actions:
        if act_t==0:
          self._send_action_to_simulator(list(map(lambda t: t[1], act)))
        elif act_t==2:
          for _, tkn in act:
            self._send_action_to_taskmanager(tkn)

      last_action: Optional[action_type_lib.ActionType] =\
          None if len(action)>0 else action[-1]["action_type"].item()
      #get_vh: bool = len(action)<=0 or action[-1]["action_type"].item()==action_type_lib.ActionType.LIFT

    elif action is not None:

      if "response" in action\
          and action["response"] is not None\
          and action["response"] != "":
        self._task_manager.receive_response(action["response"].item())
        pass

      if action["action_type"].item() == action_type_lib.ActionType.TEXT:
        self._send_action_to_taskmanager(action)
      elif action['action_type'].item() != action_type_lib.ActionType.REPEAT:
        self._send_action_to_simulator(action)

      last_action: Optional[action_type_lib.ActionType] = action["action_type"].item()
      #get_vh: bool = action["action_type"].item()==action_type_lib.ActionType.LIFT

    else:
      last_action: Optional[action_type_lib.ActionType] = None
      #get_vh: bool = True

    get_vh: bool = last_action is None or last_action==action_type_lib.ActionType.LIFT
    get_vh = get_vh and self._with_view_hierarchy

    self._elapsed_step_from_screen_check += 1
    self._elapsed_step_from_vh_check += 1

    check_vh: bool = self._check_check( self._vh_check_control_method
                                      , self._vh_check_control_value
                                      , last_action=last_action
                                      , last_time=self._last_vh_check_time
                                      , elapsed_step=self._elapsed_step_from_vh_check
                                      )
    check_screen: bool = self._check_check( self._screen_check_control_method
                                          , self._screen_check_control_value
                                          , last_action=last_action
                                          , last_time=self._last_screen_check_time
                                          , elapsed_step=self._elapsed_step_from_screen_check
                                          )

    # Sleep to maintain a steady interaction rate.
    if self._max_steps_per_sec > 0.0:
      self._wait_for_next_frame()
    #time.sleep(1)

    # Read necessary transition information and return it to the agent.
    try:
      self._latest_observation_time = time.time()
      observation = self._simulator.get_observation()

      if check_screen:
        self._last_screen_check_time = time.time()
        self._elapsed_step_from_screen_check = 0
      if check_vh:
        self._last_vh_check_time = time.time()
        self._elapsed_step_from_vh_check = 0
      view_hierarchy: Optional[lxml.etree.Element] =\
          self._task_manager.snapshot_events( observation["pixels"]
                                            , check_screen, get_vh, check_vh
                                            )
      if self._with_view_hierarchy:
        observation["view_hierarchy"] = view_hierarchy

      reward = self._task_manager.get_current_reward() # zdy
      task_extras = self._task_manager.get_current_extras()
      instructions = self._task_manager.get_current_instructions()
      episode_end = self._task_manager.check_if_episode_ended(self._with_view_hierarchy)

      self._task_manager.clear_events()

      return observation, reward, task_extras, instructions, episode_end

    except (errors.ReadObservationError, socket.error):
      logging.exception('Unable to fetch observation. Restarting simulator.')
      self._log_dict['restart_count_fetch_observation'] += 1
      self._should_restart = True
      return None, 0.0, {}, [], True
    #  }}} method execute_action # 

  def _send_action_to_taskmanager(self, action: Dict[str, np.ndarray]):
    #  method `_send_action_to_taskmanager` {{{ # 
    """
    action - dict like
      {
        "action_type": scalar array of int32 with value 3,
        "input_token": scalar array of int32
      }
    """

    self._task_manager.send_token(action["input_token"].item())
    #  }}} method `_send_action_to_taskmanager` # 

  def _send_action_to_simulator( self
                               , action: Union[ Dict[str, np.ndarray]
                                              , List[Dict[str, np.ndarray]]
                                              ]
                               ):
    #  method _send_action_to_simulator {{{ # 
    """Sends the selected action to the simulator.

    The simulator will interpret the action as a touchscreen event and perform
    it accordingly. The effect this action triggers in the Android OS will be
    determined by the currently running application.

    Args:
      action: action which will get interpreted as a touchscreen event.
    """

    try:
      self._simulator.send_action(action)
    except (socket.error, errors.SendActionError):
      logging.exception('Unable to execute action. Restarting simulator.')
      self._log_dict['restart_count_execute_action'] += 1
      self._should_restart = True
    #  }}} method _send_action_to_simulator # 

  def _check_timeout(self) -> bool:
    #  method _check_timeout {{{ # 
    """Checks if timeout between steps have exceeded.

    If too much time has passed since the last step was performed, it is assumed
    that the simulation is in a bad state, so the Coordinator will re-launch
    the simulator to make sure interaction proceeds from a clean state.

    Returns:
      Boolean indicating if the step timeout limit has been reached.
    """

    if not self._with_view_hierarchy\
        and self._step_timeout_sec and self._latest_observation_time:
      time_since_last_obs = self._get_time_since_last_observation()
      if time_since_last_obs > self._step_timeout_sec:
        logging.exception('Time between steps exceeded %f',
                          self._step_timeout_sec)
        self._log_dict['restart_count_step_timeout'] += 1
        self._should_restart = True
        return True
    return False
    #  }}} method _check_timeout # 

  def _wait_for_next_frame(self) -> None:
    """Pauses the environment so that the interaction is around 1/FPS."""

    time_since_observation = self._get_time_since_last_observation()
    time_to_wait = 1. / self._max_steps_per_sec - time_since_observation
    if time_to_wait > 0.0:
      time.sleep(time_to_wait)

  def _get_time_since_last_observation(self) -> float:
    """Computes time passed since the last observation was fetched."""

    if self._latest_observation_time is not None:
      return time.time() - self._latest_observation_time
    else:
      return np.inf

  def _check_check( self
                  , method: EventCheckControl
                  , value: Number
                  , last_action: Optional[action_type_lib.ActionType]
                  , last_time: Optional[float]
                  , elapsed_step: int
                  ) -> bool:
    #  method _check_check {{{ # 
    """
    Args:
        method (EventCheckControl): control method
        value (Number): corresponding setting value

        last_action (Optional[action_type_lib.ActionType]): last action type
        last_time (Optional[float]): last check time
        elapsed_step (int): elapsed steps since last check

    Returns:
        bool: to check or not
    """

    check: bool = EventCheckControl.LIFT in method and last_action==action_type_lib.ActionType.LIFT\
               or EventCheckControl.TEXT in method and last_action==action_type_lib.ActionType.TEXT\
               or ( last_time is None or time.time()-last_time>=value if EventCheckControl.TIME in method\
               else EventCheckControl.STEP in method and (elapsed_step==0 or elapsed_step>=value)
                  )
    return check
    #  }}} method _check_check # 

  def get_logs(self) -> Dict[str, Any]:
    """Returns internal counter values."""

    log_dict = copy.deepcopy(self._log_dict)
    log_dict.update(self._task_manager.log_dict())
    return log_dict

  def close(self):
    """Cleans up the state of this Coordinator."""

    if hasattr(self, '_task_manager'):
      self._task_manager.close()
    if hasattr(self, '_simulator'):
      self._simulator.close()
