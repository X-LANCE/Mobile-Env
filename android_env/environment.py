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

from typing import Any, Dict, List, Union
from absl import logging
from android_env.components import coordinator as coordinator_lib
from android_env.components import task_manager as task_manager_lib
from android_env.utils import fix_path
from android_env.proto import task_pb2
from google.protobuf import text_format
import os.path
import dm_env
import numpy as np

class AndroidEnv(dm_env.Environment):
  """An RL environment that interacts with Android apps."""

  def __init__(self, coordinator: coordinator_lib.Coordinator):
    """Initializes the state of this AndroidEnv object."""

    self._coordinator = coordinator
    self._latest_action = {}
    self._latest_observation = {}
    self._latest_extras = {}
    self._latest_instruction = []
    self._reset_next_step = True

    logging.info('Action spec: %s', self.action_spec())
    logging.info('Observation spec: %s', self.observation_spec())
    logging.info('Task extras spec: %s', self.task_extras_spec())

  #  Informational Interfaces {{{ # 
  def action_spec(self) -> Dict[str, dm_env.specs.Array]:
    return self._coordinator.action_spec()

  def observation_spec(self) -> Dict[str, dm_env.specs.Array]:
    return self._coordinator.observation_spec()

  def task_extras_spec(self) -> Dict[str, dm_env.specs.Array]:
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

  def add_task(self, task_path: str, **kwargs: Dict[str, Any]):
    #  method `add_task` {{{ # 
    task = task_pb2.Task()
    with open(task_path, 'r') as f:
      text_format.Parse(f.read(), task)

    fix_path(task, os.path.dirname(task_path))
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

  def switch_task(self, index: int) -> dm_env.TimeStep:
    #  method `change_task` {{{ # 
    logging.info('Changing Task to {:d}...'.format(index))

    # Change the task and reset state of the environment.
    self._coordinator.switch_task_manager(index)

    # Execute selected action (None when resetting).
    obs, _, extras, instructions, _ = self._coordinator.execute_action(action=None)

    # Process relevant information.
    if obs is not None:
      self._latest_observation = obs.copy()
    self._latest_extras = extras.copy()
    self._latest_instruction = instructions.copy()
    self._latest_action = {}
    self._reset_next_step = False

    logging.info('Done Changing Task.')
    logging.info('************* NEW EPISODE *************')

    return dm_env.TimeStep(
        step_type=dm_env.StepType.FIRST,
        observation=self._latest_observation,
        reward=0.0,
        discount=0.0)
    #  }}} method `change_task` # 

  def reset(self) -> dm_env.TimeStep:
    """Resets the environment for a new RL episode."""

    logging.info('Resetting AndroidEnv...')

    # Reset state of the environment.
    self._coordinator.reset_environment_state()

    # Execute selected action (None when resetting).
    obs, _, extras, instructions, _ = self._coordinator.execute_action(action=None)

    # Process relevant information.
    if obs is not None:
      self._latest_observation = obs.copy()
    self._latest_extras = extras.copy()
    self._latest_instruction = instructions.copy()
    self._latest_action = {}
    self._reset_next_step = False

    logging.info('Done resetting AndroidEnv.')
    logging.info('************* NEW EPISODE *************')

    return dm_env.TimeStep(
        step_type=dm_env.StepType.FIRST,
        observation=self._latest_observation,
        reward=0.0,
        discount=0.0)

  def step( self
          , action: Union[ Dict[str, np.ndarray]
                         , List[Dict[str, np.ndarray]]
                         ]
          ) -> dm_env.TimeStep:
    """Takes a step in the environment."""

    # Check if it's time to reset the episode.
    if self._reset_next_step:
      return self.reset()

    # Execute selected action.
    obs, reward, extras, instructions, episode_end = self._coordinator.execute_action(action)

    # Process relevant information.
    if obs is not None:
      self._latest_observation = obs.copy()
    self._latest_extras = extras.copy()
    self._latest_instruction = instructions.copy()
    self._latest_action = action.copy()
    self._reset_next_step = episode_end

    # Return timestep with reward and observation just computed.
    if episode_end:
      return dm_env.termination(
          observation=self._latest_observation, reward=reward)
    else:
      return dm_env.transition(
          observation=self._latest_observation, reward=reward, discount=0.0)

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
    logging.info('Cleaning up AndroidEnv...')
    if hasattr(self, '_coordinator'):
      self._coordinator.close()
    logging.info('Done cleaning up AndroidEnv.')

  def __del__(self) -> None:
    self.close()
