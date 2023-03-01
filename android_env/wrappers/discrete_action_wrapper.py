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

"""Wraps the AndroidEnv environment to provide discrete actions."""

from typing import Optional, Sequence
from typing import Dict, Tuple

import android_env
from android_env.components import action_type
from android_env.wrappers import base_wrapper
import dm_env
from dm_env import specs
import numpy as np

NOISE_CLIP_VALUE = 0.4999

class DiscreteActionWrapper(base_wrapper.BaseWrapper):
  """AndroidEnv with discrete actions."""

  def __init__(self,
               env: dm_env.Environment,
               action_grid: Sequence[int] = (10, 10),
               redundant_actions: bool = False,
               keep_repeat: bool = False,
               noise: float = 0.1):
    #  method `__init__` {{{ # 
    """
    Args:
        env: android_env.AndroidEnv
        action_grid: Sequence of int as (height, width)
        redundant_actions: bool
          - if True, then the action space will be ((G+V)*A,) where G is grid
            size, V is vocabulary size and A is the number of action types;
            action type ids are assigned to actions TOUCH, LIFT, REPEAT, TEXT
            by sequence where REPEAT is optional and is controlled by
            `keep_repeat` and TEXT is optional and is determined by the
            vocabulary size of the internal `env`
          - if False, the action space will be flatten to cat(TO, L, R, TE);
            the length of the TOUCH segment is G; LIFT and REPEAT occupy 1 slot
            respectively; TEXT segment is V-long. REPEAT and TEXT are also
            optional and the condition is as well as the case that
            `redundant_actions`==True
        keep_repeat: bool
        noise: floating
    """

    super().__init__(env)

    self._action_grid: Tuple[int, int] = tuple(action_grid)  # [height, width]
    self._grid_size: np.int64 = np.prod(self._action_grid)

    self._redundant_actions: bool = redundant_actions
    self._keep_repeat = keep_repeat
    self._noise: float = noise

    self._post_switch_task()
    #  }}} method `__init__` # 

  def _assert_base_env(self):
    """Checks that the wrapped env has the right action spec format."""

    assert len(self._parent_action_spec) == 2 or len(self._parent_action_spec) == 3
    assert not self._parent_action_spec['action_type'].shape
    assert self._parent_action_spec['touch_position'].shape == (2,)
    assert not self._parent_action_spec['input_token'].shape if "input_token" in self._parent_action_spec else True

  @property
  def num_actions(self) -> int:
    """Number of discrete actions."""

    if self._redundant_actions:
      return (self._grid_size+self._vocabulary_size) * self._num_action_types
    else:
      return self._grid_size + self._num_action_types - 1 + max(0, self._vocabulary_size-1)

  def step(self, action: Dict[str, int]) -> dm_env.TimeStep:
    """Take a step in the base environment."""

    return self._env.step(self._process_action(action))

  def _process_action(self, action: Dict[str, int]) -> Dict[str, np.ndarray]:
    """Transforms action so that it agrees with AndroidEnv's action spec."""

    action_type_ = self._get_action_type(action['action_id'])
    if action_type_!=action_type.ActionType.TEXT:
      return {
          'action_type':
              np.array(action_type_,
                       dtype=self._parent_action_spec['action_type'].dtype),
          'touch_position':
              np.array(self._get_touch_position(action['action_id']),
                       dtype=self._parent_action_spec['touch_position'].dtype)
      }
    else:
      return {
          "action_type":
            np.array(action_type_,
              dtype=self._parent_action_spec["action_type"].dtype),
          "input_token":
            np.array(action["action_id"]-self._grid_size-self._num_action_types+2,
              dtype=self._parent_action_spec["input_token"].dtype)
        }

  def _get_action_type(self, action_id: int) -> action_type.ActionType:
    #  method `_get_action_type` {{{ # 
    """Compute action type corresponding to the given action_id.

    When `self._redundant_actions` == True the `grid_size` is "broadcast" over
    all the possible actions so you end up with `grid_size` discrete actions
    of type 0, `grid_size` discrete actions of type 1, etc. for all action
    types.

    When `self._redundant_actions` == False the first `grid_size` actions are
    reserved for "touch" and the rest are just added (NOT multiplied) to the
    total number of discrete actions (exactly one of LIFT and REPEAT).

    Args:
      action_id: A discrete action.
    Returns:
      action_type: The action_type of the action.
    """

    if self._redundant_actions:
      assert action_id < self.num_actions
      return action_id // (self._grid_size+self._vocabulary_size)

    else:
      assert action_id <= self.num_actions
      if action_id < self._grid_size:
        return action_type.ActionType.TOUCH
      elif action_id == self._grid_size:
        return action_type.ActionType.LIFT
      else:
        if self._keep_repeat:
          return action_type.ActionType.REPEAT if action_id==self._grid_size+1\
              else action_type.ActionType.TEXT
        else:
          return action_type.ActionType.TEXT
    #  }}} method `_get_action_type` # 

  def _get_touch_position(self, action_id: int) -> Sequence[float]:
    #  method `_get_touch_position` {{{ # 
    """Compute the position corresponding to the given action_id.

    Note: in the touch_position (x, y) of an action, x corresponds to the
    horizontal axis (width), and y corresponds to the vertical axis (height)
    of the screen. BUT, the screen has dimensions (height, width), i.e. the
    first coordinate corresponds to y, and the second coordinate corresponds
    to x. Pay attention to this mismatch in the calculations below.

    Args:
      action_id: A discrete action.
    Returns:
      touch_position: The [0,1]x[0,1] coordinate of the action.
    """

    position_idx = action_id % self._grid_size

    x_pos_grid = position_idx % self._action_grid[1]  # WIDTH
    y_pos_grid = position_idx // self._action_grid[1]  # HEIGHT

    noise_x = np.random.normal(loc=0.0, scale=self._noise)
    noise_y = np.random.normal(loc=0.0, scale=self._noise)

    # Noise is clipped so that the action will strictly stay in the cell.
    noise_x = max(min(noise_x, NOISE_CLIP_VALUE), -NOISE_CLIP_VALUE)
    noise_y = max(min(noise_y, NOISE_CLIP_VALUE), -NOISE_CLIP_VALUE)

    x_pos = (x_pos_grid + 0.5 + noise_x) / self._action_grid[1]  # WIDTH
    y_pos = (y_pos_grid + 0.5 + noise_y) / self._action_grid[0]  # HEIGHT

    # Project action space to action_spec ranges. For the default case of
    # minimum = [0, 0] and maximum = [1, 1], this will not do anything.
    x_min, y_min = self._parent_action_spec['touch_position'].minimum
    x_max, y_max = self._parent_action_spec['touch_position'].maximum

    x_pos = x_min + x_pos * (x_max - x_min)
    y_pos = y_min + y_pos * (y_max - y_min)

    return [x_pos, y_pos]
    #  }}} method `_get_touch_position` # 

  def action_spec(self) -> Dict[str, specs.Array]:
    """Action spec of the wrapped environment."""

    return {
        'action_id':
            specs.DiscreteArray(
                num_values=self.num_actions,
                name='action_id')
    }

  def _post_switch_task(self):
    self._parent_action_spec: Dict[str, specs.Array] = self._env.action_spec()
    self._assert_base_env()

    self._num_action_types: int = self._parent_action_spec['action_type'].num_values
    if not self._keep_repeat:
      self._num_action_types -= 1
    self._vocabulary_size: int = self._parent_action_spec['input_token'].num_values\
            if "input_token" in self._parent_action_spec else 0
