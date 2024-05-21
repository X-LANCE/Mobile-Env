# pylint: disable=g-bad-file-header
# vim: set tabstop=2 shiftwidth=2:
# Copyright 2024 SJTU X-Lance Lab
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
# Copyright 2019 The dm_env Authors. All Rights Reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#    http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or  implied.
# See the License for the specific language governing permissions and
# limitations under the License.
# ============================================================================

"""Python RL Environment API."""

#import abc
import enum
from typing import Any, Optional
from typing import NamedTuple

#from android_env.interfaces import specs

class StepType(enum.IntEnum):
  """Defines the status of a `TimeStep` within a sequence."""
  # Denotes the first `TimeStep` in a sequence.
  FIRST = 0
  # Denotes any `TimeStep` in a sequence that is not FIRST or LAST.
  MID = 1
  # Denotes the last `TimeStep` in a sequence.
  LAST = 2

  def first(self) -> bool:
    return self is StepType.FIRST

  def mid(self) -> bool:
    return self is StepType.MID

  def last(self) -> bool:
    return self is StepType.LAST

class TimeStep(NamedTuple):
  """Returned with every call to `step` and `reset` on an environment.

  A `TimeStep` contains the data emitted by an environment at each step of
  interaction. A `TimeStep` holds a `step_type`, an `observation` (typically a
  NumPy array or a dict or list of arrays), and an associated `reward` and
  `discount`.

  The first `TimeStep` in a sequence will have `StepType.FIRST`. The final
  `TimeStep` will have `StepType.LAST`. All other `TimeStep`s in a sequence will
  have `StepType.MID.

  Attributes:
    step_type (StepType): giving the step type.
    reward (float): the reward at the current step
    observation (Any): the observation
    succeeds (Optional[bool]): True for success, False for failure, and None
      for ending with exception
  """

  step_type: StepType
  reward: float
  observation: Any
  succeeds: Optional[bool]

  def first(self) -> bool:
    return self.step_type == StepType.FIRST

  def mid(self) -> bool:
    return self.step_type == StepType.MID

  def last(self) -> bool:
    return self.step_type == StepType.LAST

# Helper functions for creating TimeStep namedtuples with default settings.

def restart(observation: Any):
  """Returns a `TimeStep` with `step_type` set to `StepType.FIRST`."""
  return TimeStep(StepType.FIRST, 0., observation, None)

def transition(reward: float, observation: Any):
  """Returns a `TimeStep` with `step_type` set to `StepType.MID`."""
  return TimeStep(StepType.MID, reward, observation, None)

def success(reward: float, observation: Any):
  """Returns a `TimeStep` with `step_type` set to `StepType.LAST`."""
  return TimeStep(StepType.LAST, reward, observation, True)

def failure(reward: float, observation: Any):
  return TimeStep(StepType.LAST, reward, observation, False)

def truncation(reward: float, observation: Any):
  """Returns a `TimeStep` with `step_type` set to `StepType.LAST`."""
  return TimeStep(StepType.LAST, reward, observation, None)
