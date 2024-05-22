# coding=utf-8
# vim: set tabstop=2 shiftwidth=2:
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

"""Base class for AndroidEnv wrappers."""

from typing import Any, Dict, List
from android_env.interfaces import timestep
from android_env.interfaces import specs
from android_env.interfaces.env import Environment

class BaseWrapper(Environment):
  """AndroidEnv wrapper."""

  def __init__(self, env: Environment):
    self._env: Environment = env

  def switch_task(self, index: int) -> timestep.TimeStep:
    self._reset_state()
    timestep = self._env.switch_task(index)
    self._post_switch_task()
    timestep = self._process_timestep(timestep)
    return timestep

  def reset(self) -> timestep.TimeStep:
    self._reset_state()
    timestep = self._process_timestep(self._env.reset())
    return timestep

  def step(self, action: Any) -> timestep.TimeStep:
    action = self._process_action(action)
    return self._process_timestep(self._env.step(action))

  def _post_switch_task(self):
    pass

  def _reset_state(self):
    # CLEAR states rather than restart states
    pass

  def _process_action(self, action: Any) -> Any:
    return action

  def _process_timestep(self, timestep: timestep.TimeStep) -> timestep.TimeStep:
    return timestep

  def observation_spec(self) -> Dict[str, specs.Array]:
    return self._env.observation_spec()

  def action_spec(self) -> Dict[str, specs.Array]:
    return self._env.action_spec()

  def command(self) -> List[str]:
    return self._env.command()

  def vocabulary(self) -> List[str]:
    return self._env.vocabulary()

  @property
  def nb_tasks(self) -> int:
    return self._env.nb_tasks

  @property
  def task_index(self) -> int:
    return self._env.task_index

  @property
  def task_id(self) -> str:
    return self._env.task_id

  @property
  def task_name(self) -> str:
    return self._env.task_name

  @property
  def task_description(self) -> str:
    return self._env.task_description

  def task_instructions(self) -> str:
    return self._env.task_instructions()

  def task_extras(self) -> str:
    return self._env.task_extras()

  def _wrapper_logs(self) -> Dict[str, Any]:
    """Add wrapper specific logging here."""
    return {}

  def android_logs(self) -> Dict[str, Any]:
    info = self._env.android_logs()
    info.update(self._wrapper_logs())
    return info

  @property
  def raw_env(self):
    """Recursively unwrap until we reach the true 'raw' env."""
    wrapped = self._env
    if hasattr(wrapped, 'raw_env'):
      return wrapped.raw_env
    return wrapped

  def __getattr__(self, attr):
    """Delegate attribute access to underlying environment."""
    return getattr(self._env, attr)

  def close(self):
    self._env.close()
