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

"""Wraps the AndroidEnv environment to provide tap actions of a given duration."""

from typing import Dict, List
from typing import Union
from numbers import Number

from android_env.environment import AndroidEnv
from android_env.components import action_type
from android_env.wrappers import base_wrapper
import dm_env
from dm_env import specs

import numpy as np
from transformers import PreTrainedTokenizer
import enum
import time

#ActionType = action_type.ActionType

class TapActionWrapper(base_wrapper.BaseWrapper):
  """
  AndroidEnv with tap actions.

  The actions are formulated as

  ```haskell
  data Point = Float Float -- (x, y)
  data Action = TAP Point
              | SCROLL Point Point -- from, to
              | TYPE String -- text
              | GOBACK
              | NOTHING
  ```
  """

  #  Type Definition {{{ # 
  class ActionType(enum.IntEnum):
    NOTHING = 0
    TAP = 1
    SCROLL = 2
    TYPE = 3
    GOBACK = 4
  #  }}} Type Definition # 

  def __init__( self
              , env: AndroidEnv
              , tokenizer: PreTrainedTokenizer
              , num_tap_frames: int = 5
              , num_scroll_frame_rate: int = 15
              , wait_sec: float = 1.
              , action_batch: bool = False
              ):
    #  method __init__ {{{ # 
    """
    Args:
        env (AndroidEnv): the environment to be wrapped
        tokenizer (PreTrainedTokenizer): tokenizer to tokenize the input
          text into the tokens from the vocabulary of the environment
        num_tap_frames (int): the duration the TOUCH action will last for the
          TAP iteraction
        num_scroll_frame_rate (int): the frame rate of the TOUCH action for
          SCROLL iteration. the real duration of a SCORLL action in frames is
          `int(round(num_scroll_frame_rate*euclidean_length))`.
        wait_sec (float): waiting time after each action performed
        action_batch (bool): if actions are combined in a batch
    """

    super().__init__(env)

    self._instructions: List[str] = []

    self._tokenizer: PreTrainedTokenizer = tokenizer
    self._nb_tap_frames: int = num_tap_frames
    self._nb_scroll_frame_rate: float = float(num_scroll_frame_rate)
    self._wait_sec: float = wait_sec
    self._action_batch: bool = action_batch

    self._env_steps: int = 0

    self._action_spec: Dict[str, specs.Array] =\
        { "action_type": specs.DiscreteArray( num_values=len(TapActionWrapper.ActionType)
                                            , name="action_type"
                                            )
        , "touch_position": specs.BoundedArray( shape=(2,)
                                              , dtype=np.float32
                                              , minimum=[0., 0.]
                                              , maximum=[1., 1.]
                                              , name="touch_position"
                                              )
        , "start_position": specs.BoundedArray( shape=(2,)
                                              , dtype=np.float32
                                              , minimum=[0., 0.]
                                              , maximum=[1., 1.]
                                              , name="touch_position"
                                              )
        , "end_position": specs.BoundedArray( shape=(2,)
                                            , dtype=np.float32
                                            , minimum=[0., 0.]
                                            , maximum=[1., 1.]
                                            , name="touch_position"
                                            )
         , "text": specs.StringArray( shape=()
                                    , name="text"
                                    )
         , "response": specs.StringArray( shape=()
                                        , name="response"
                                        )
         }
    #  }}} method __init__ # 

  def android_logs(self) -> Dict[str, Number]:
    """Returns a dictionary of metrics logged by the environment."""
    logs: Dict[str, Number] = self._env.android_logs()
    logs.update({'env_steps': self._env_steps})
    return logs

  def _process_action(self, action: Dict[str, np.ndarray]) -> List[Dict[str, np.ndarray]]:
    #  method _process_action {{{ # 
    """
    Args:
        action (Dict[str, np.ndarray]): dict like
          {
            "action_type": NOTHING | GOBACK
          } or
          { "action_type": TAP
          , "touch_position": [float, float]
          } or
          { "action_type": SCROLL
          , "start_position": [float, float]
          , "end_position": [float, float]
          } or
          { "action_type": TYPE
          , "text": str
          }
          all the values in `action` are wrapped in np.ndarray.

    Returns:
        List[Dict[str, np.ndarray]]: list of dict like
          {
            "action_type": np.ndarray of int32 scalar from TOUCH | LIFT | REPEAT
            "touch_position": np.ndarray of float32 with shape (2,)
          } or
          {
            "action_type": np.ndarray of int32 scalar from TEXT
            "input_token": np.ndarray of int32 scalar
          }
    """

    if action["action_type"]==TapActionWrapper.ActionType.NOTHING:
        return [{"action_type": np.array(action_type.ActionType.REPEAT, dtype=np.int32)}]
    if action["action_type"]==TapActionWrapper.ActionType.GOBACK:
        return []

    actions: List[Dict[str, np.ndarray]] = []

    if action["action_type"]==TapActionWrapper.ActionType.TAP:
      actions += [ { "action_type": np.array( action_type.ActionType.TOUCH
                                            , dtype=np.int32
                                            )
                   , "touch_position": action["touch_position"]
                   }
                 ] * self._nb_tap_frames
      actions.append( { "action_type": np.array( action_type.ActionType.LIFT
                                               , dtype=np.int32
                                               )
                      , "touch_position": action["touch_position"]
                      }
                    )
      return actions
    if action["action_type"]==TapActionWrapper.ActionType.SCROLL:
      scroll_distance: np.float64 = np.linalg.norm(action["end_position"]-action["start_position"])
      nb_frames: int = int(np.round(scroll_distance*self._nb_scroll_frame_rate))
      x_trajectory: np.array = np.linspace( action["start_position"][0], action["end_position"][0]
                                          , num=nb_frames
                                          , dtype=np.float32
                                          )
      y_trajectory: np.array = np.linspace( action["start_position"][1], action["end_position"][1]
                                          , num=nb_frames
                                          , dtype=np.float32
                                          )
      for p in np.stack([x_trajectory, y_trajectory], axis=-1):
        actions.append( { "action_type": np.array( action_type.ActionType.TOUCH
                                                 , dtype=np.int32
                                                 )
                        , "touch_position": p
                        }
                      )
      actions.append( { "action_type": np.array( action_type.ActionType.LIFT
                                               , dtype=np.int32
                                               )
                      , "touch_position": action["end_position"]
                      }
                    )
      return actions
    if action["action_type"]==TapActionWrapper.ActionType.TYPE:
      token_list: List[int] = self._tokenizer( action["text"].item()
                                             , add_special_tokens=False
                                             )["input_ids"]
      for tkn in token_list:
        actions.append( { "action_type": np.array( action_type.ActionType.TEXT
                                                 , dtype=np.int32
                                                 )
                        , "input_token": np.array(tkn, dtype=np.int32)
                        }
                      )
      return actions
    #  }}} method _process_action # 

  def step(self, action: Dict[str, np.ndarray]) -> dm_env.TimeStep:
    #  method step {{{ # 
    """Takes a step in the environment."""
    actions = self._process_action(action)
    self._env_steps += len(actions)+1

    total_reward = 0.
    instructions: List[str] = []
    if self._action_batch:
      timestep: dm_env.TimeStep = self._env.step(actions)
      instructions += self._env.task_instructions()
      if timestep.reward>0.:
        total_reward += timestep.reward


      if timestep.last():
        self._instructions = instructions
        return dm_env.TimeStep( step_type=timestep.step_type
                              , reward=total_reward
                              , discount=timestep.discount
                              , observation=timestep.observation
                              )
    else:
      for act in actions:
        timestep: dm_env.TimeStep = self._env.step(act)
        instructions += self._env.task_instructions()

        if timestep.reward>0.:
          total_reward += timestep.reward

        if timestep.last():
          self._instructions = instructions
          return dm_env.TimeStep( step_type=timestep.step_type
                                , reward=total_reward
                                , discount=timestep.discount
                                , observation=timestep.observation
                                )

    if action["action_type"]==TapActionWrapper.ActionType.TYPE:
        self._env._coordinator._task_manager._adb_controller.input_key("KEYCODE_ENTER")
    elif action["action_type"]==TapActionWrapper.ActionType.GOBACK:
        self._env._coordinator._task_manager._adb_controller.input_key("KEYCODE_BACK")

    appended_lift: Dict[str, np.ndarray] = { "action_type": np.array( action_type.ActionType.LIFT
                                                                    , dtype=np.int32
                                                                    )
                                           , "touch_position": np.array( [0., 0.]
                                                                       , dtype=np.float32
                                                                       )
                                           }
    if "response" in action\
            and action["response"] is not None\
            and action["response"] != "":
        appended_lift["response"] = action["response"]
    timestep = self._env.step(appended_lift)
    instructions += self._env.task_instructions()
    if timestep.reward>0.:
        total_reward += timestep.reward

    time.sleep(self._wait_sec)
    appended_lift: Dict[str, np.ndarray] = { "action_type": np.array( action_type.ActionType.LIFT
                                                                    , dtype=np.int32
                                                                    )
                                           , "touch_position": np.array( [0., 0.]
                                                                       , dtype=np.float32
                                                                       )
                                           }
    timestep = self._env.step(appended_lift)
    instructions += self._env.task_instructions()
    if timestep.reward>0.:
        total_reward += timestep.reward

    self._instructions = instructions
    return dm_env.TimeStep( step_type=timestep.step_type
                          , reward=total_reward
                          , discount=timestep.discount
                          , observation=timestep.observation
                          )
    #  }}} method step # 

  def task_instructions(self, latest_only: bool = False) -> Union[str, List[str]]:
      if latest_only:
          return self._instructions[-1] if len(self._instructions)>0 else ""
      else:
          return self._instructions.copy()

  def _reset_state(self):
      self._instructions = []

  def action_spec(self) -> Dict[str, dm_env.specs.Array]:
    return self._action_spec
