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

"""Android environment implementation."""

from typing import Any, Union, Optional
from typing import Dict, List
#from absl import logging
import logging
from android_env.components import coordinator as coordinator_lib
from android_env.components import task_manager as task_manager_lib
from android_env.utils import fix_path
from android_env.proto import task_pb2
from google.protobuf import text_format
import os.path
from android_env import interfaces
import numpy as np
from lxml.etree import _Element

logger = logging.getLogger("mobile_env.environment")

class AndroidEnv(interfaces.env.Environment):
  """An RL environment that interacts with Android apps."""

  def __init__(self, coordinator: coordinator_lib.Coordinator):
    """Initializes the state of this AndroidEnv object."""

    self._coordinator = coordinator
    self._latest_action = {}
    self._latest_observation = {}
    self._latest_extras = {}
    self._latest_instruction = []
    self._reset_next_step = True

    logger.info('Action spec: %s', self.action_spec())
    logger.info('Observation spec: %s', self.observation_spec())
    logger.info('Task extras spec: %s', self.task_extras_spec())

    self._max_reset_rounds: int = 10

  #  Informational Interfaces {{{ # 
  def action_spec(self) -> Dict[str, interfaces.specs.Array]:
    return self._coordinator.action_spec()

  def observation_spec(self) -> Dict[str, interfaces.specs.Array]:
    return self._coordinator.observation_spec()

  def task_extras_spec(self) -> Dict[str, interfaces.specs.Array]:
    return self._coordinator.task_extras_spec()

  def command(self) -> List[str]:
    """
    return list of str
    """

    return self._coordinator.command()

  def vocabulary(self) -> List[str]:
    """
    return list of str
    """

    return self._coordinator.vocabulary()

  @property
  def nb_tasks(self) -> int:
    return self._coordinator.nb_tasks
  @property
  def task_index(self) -> int:
    return self._coordinator.task_index
  @property
  def task_id(self) -> str:
    return self._coordinator.task_id
  @property
  def task_name(self) -> str:
    return self._coordinator.task_name
  @property
  def task_description(self) -> str:
    return self._coordinator.task_description
  #  }}} Informational Interfaces # 

  @property
  def raw_action(self):
    return self._latest_action

  @property
  def raw_observation(self):
    return self._latest_observation

  def android_logs(self) -> Dict[str, Any]:
    return self._coordinator.get_logs()

  def add_task(self, task_path: str, remote_path: Optional[str] = None, **kwargs: Dict[str, Any]):
    #  method `add_task` {{{ # 
    task = task_pb2.Task()
    with open(task_path, 'r') as f:
      text_format.Parse(f.read(), task)

    fix_path(task, os.path.dirname(task_path), remote_path)
    #for st in task.setup_steps:
      #if st.HasField("adb_call") and\
          #st.adb_call.HasField("install_apk"):
        #apk_path = st.adb_call.install_apk.filesystem.path
        #if not os.path.isabs(apk_path):
          #st.adb_call.install_apk.filesystem.path =\
              #os.path.normpath(
              #os.path.join(os.path.dirname(task_path),
                #apk_path))

    task_manager = task_manager_lib.TaskManager(task, **kwargs)
    self._coordinator.add_task_manager(task_manager)
    #  }}} method `add_task` # 

  def switch_task(self, index: int) -> interfaces.timestep.TimeStep:
    #  method `change_task` {{{ # 
    logger.info('Changing Task to {:d}...'.format(index))

    # Change the task and reset state of the environment.
    self._coordinator.switch_task_manager(index)

    self.reset()

    logger.info('Done Changing Task.')
    logger.info('************* NEW EPISODE *************')

    return interfaces.timestep.restart(observation=self._latest_observation)
    #  }}} method `change_task` # 

  def reset(self) -> interfaces.timestep.TimeStep:
    """Resets the environment for a new RL episode."""

    logger.info('Resetting AndroidEnv...')

    for i in range(self._max_reset_rounds):
      # Reset state of the environment.
      self._coordinator.reset_environment_state()

      # Execute selected action (None when resetting).
      obs: Dict[str, Union[np.ndarray, Optional[_Element]]]
      reward: float
      extras: Dict[str, Any]
      instructions: List[str]
      episode_end: bool
      #succeeds: Optional[bool]
      obs, reward, extras, instructions, episode_end, _ = self._coordinator.execute_action(action=None)

      if reward==0 and not episode_end:
        # Process relevant information.
        if obs is not None:
          self._latest_observation = obs.copy()
        self._latest_extras = extras.copy()
        self._latest_instruction = instructions.copy()
        self._latest_action = {}
        self._reset_next_step = False
        break
      else:
        logger.info("Events cleared with errors! Resetting again for %d times!", i+1)

    logger.info('Done resetting AndroidEnv.')
    logger.info('************* NEW EPISODE *************')

    return interfaces.timestep.restart(observation=self._latest_observation)

  def step( self
          , action: Union[ Dict[str, np.ndarray]
                         , List[Dict[str, np.ndarray]]
                         ]
          ) -> interfaces.timestep.TimeStep:
    """Takes a step in the environment."""

    # Check if it's time to reset the episode.
    if self._reset_next_step:
      return self.reset()

    # Execute selected action.
    obs: Dict[str, Union[np.ndarray, Optional[_Element]]]
    reward: float
    extras: Dict[str, Any]
    instructions: List[str]
    episode_end: bool
    succeeds: Optional[bool]
    obs, reward, extras, instructions, episode_end, succeeds =\
        self._coordinator.execute_action(action)

    # Process relevant information.
    if obs is not None:
      self._latest_observation = obs.copy()
    self._latest_extras = extras.copy()
    self._latest_instruction = instructions.copy()
    self._latest_action = action.copy()
    self._reset_next_step = episode_end

    # Return timestep with reward and observation just computed.
    if episode_end:
      if succeeds:
        return interfaces.timestep.success(
                observation=self._latest_observation
              , reward=reward
              )
      elif succeeds is None:
        return interfaces.timestep.truncation(
                observation=self._latest_observation
              , reward=reward
              )
      else:
        return interfaces.timestep.failure(
                observation=self._latest_observation
              , reward=reward
              )
    else:
      return interfaces.timestep.transition(
              observation=self._latest_observation
            , reward=reward
            )

  def task_extras(self, latest_only: bool = True) -> Dict[str, np.ndarray]:
    """Returns latest task extras."""

    task_extras = {}
    for key, spec in self.task_extras_spec().items():
      if key in self._latest_extras:
        extra_values = self._latest_extras[key].astype(spec.dtype)
        for extra in extra_values:
          spec.validate(extra)
        if latest_only:
          task_extras[key] = extra_values[-1] if len(extra_values)>0\
              else np.zeros(shape=spec.shape, dtype=spec.dtype)
        else:
          task_extras[key] = extra_values
    return task_extras

  def task_instructions(self, latest_only: bool = False) -> Union[str, List[str]]:
    """
    latest_only - bool

    return str or list of str
    """

    if latest_only:
      return self._latest_instruction[-1] if len(self._latest_instruction)>0 else ""
    else:
      return self._latest_instruction.copy()

  def close(self) -> None:
    """Cleans up running processes, threads and local files."""
    logger.info('Cleaning up AndroidEnv...')
    if hasattr(self, '_coordinator'):
      self._coordinator.close()
    logger.info('Done cleaning up AndroidEnv.')

  def __del__(self) -> None:
    self.close()
