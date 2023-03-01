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

"""Converts pixel observation to from int to float32 between 0.0 and 1.0."""

from typing import Dict

from android_env.components import utils
from android_env.wrappers import base_wrapper
import dm_env
from dm_env import specs
import numpy as np

imgnet_mean = np.array([0.485, 0.456, 0.406])
imgnet_std = np.array([0.229, 0.224, 0.225])
def normalize_pixels(pixels: np.ndarray, imgnet_norm: bool = False) -> np.ndarray:
  #  function `normalize_pixel` {{{ # 
  """
  Args:
      pixels: array of uint8 with shape (height, width, nb_channels)
      imgnet_norm: bool

  Returns:
      array of float32 with the same shape as `pixels`
  """

  float_pixels = np.clip(pixels, 0, 255).astype(np.float32)/255.
  if imgnet_norm:
    float_pixels -= imgnet_mean
    float_pixels /= imgnet_std
  return float_pixels
    #  }}} function `normalize_pixel` # 

class FloatPixelsWrapper(base_wrapper.BaseWrapper):
  """Wraps AndroidEnv for Panultimate agent."""

  def __init__(self, env: dm_env.Environment, imgnet_norm: bool = False):
    super().__init__(env)
    self._should_convert_int_to_float = np.issubdtype(
        self._env.observation_spec()['pixels'].dtype, np.integer)
    self._imgnet_norm = imgnet_norm

  def _process_observation(
      self, observation: Dict[str, np.ndarray]
  ) -> Dict[str, np.ndarray]:
    if self._should_convert_int_to_float:
      #float_pixels = utils.convert_int_to_float(
          #observation['pixels'],
          #self._env.observation_spec()['pixels'],
          #np.float32)
      float_pixels = normalize_pixels(observation["pixels"], self._imgnet_norm)
      observation['pixels'] = float_pixels
    return observation

  def _process_timestep(self, timestep: dm_env.TimeStep) -> dm_env.TimeStep:
    step_type, reward, discount, observation = timestep
    return dm_env.TimeStep(
        step_type=step_type,
        reward=reward,
        discount=discount,
        observation=self._process_observation(observation))

  def reset(self) -> dm_env.TimeStep:
    timestep = self._env.reset()
    return self._process_timestep(timestep)

  def step(self, action: Dict[str, np.ndarray]) -> dm_env.TimeStep:
    timestep = self._env.step(action)
    return self._process_timestep(timestep)

  def observation_spec(self) -> Dict[str, specs.Array]:
    if self._should_convert_int_to_float:
      observation_spec = self._env.observation_spec()
      observation_spec['pixels'] = specs.BoundedArray(
          shape=self._env.observation_spec()['pixels'].shape,
          dtype=np.float32,
          minimum=0.0,
          maximum=1.0,
          name=self._env.observation_spec()['pixels'].name)
      return observation_spec
    return self._env.observation_spec()
