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

"""
Created by Danyang Zhang @X-Lance.
"""

from android_env.environment import AndroidEnv
from android_env.wrappers import base_wrapper

from typing import Dict, List, Pattern, Tuple
from typing import Union
from numbers import Number
import dm_env
from dm_env import specs
from android_env.components import action_type

import enum
from transformers import PreTrainedTokenizer
import numpy as np
import lxml.etree
import re
import time

#import logging

def filter_elements(tree: lxml.etree.Element)\
        -> Tuple[ List[lxml.etree.Element]
                , List[List[int]]
                ]:
    #  function filter_elements {{{ # 
    node_list: List[lxml.etree.Element] = []
    bbox_list: List[List[int]] = []

    for n in tree.iterdescendants():
        n.set( "clickable"
             , str(  n.get("clickable")=="true"\
                  or n.getparent().get("clickable")=="true"
                  ).lower()
             )
        if n.get("bounds")=="[0,0][0,0]":
            continue
        if len(list(n))==0:
            bounds_match = VhIoWrapper.bounds_pattern.match(n.get("bounds"))
            bbox: List[int] = list( map( int
                                       , bounds_match.groups()
                                       )
                                  )
            if bbox[0]>=bbox[2] or bbox[1]>=bbox[3]:
                continue

            node_list.append(n)
            bbox_list.append(bbox)

    return node_list, bbox_list
    #  }}} function filter_elements # 

class VhIoWrapper(base_wrapper.BaseWrapper):
    """
    Wraps the environment with view hierarchy (VH) element iteractions.

    The actions are formulated as

    ```haskell
    data Action = CLICK Int -- eid
                | INPUT Int -- eid
                        String -- text
                | SCROLL Direction
                | GOBACK
                | NOTHING
    data Direction = UP | DOWN | LEFT | RIGHT
    ```
    """

    #  Enum Types for VH Actions {{{ # 
    class ActionType(enum.IntEnum):
        NOTHING = 0
        CLICK = 1
        INPUT = 2
        SCROLL = 3
        GOBACK = 4

    class ScrollDirection(enum.IntEnum):
        LEFT = 0
        UP = 1
        RIGHT = 2
        DOWN = 3
    #  }}} Enum Types for VH Actions # 

    bounds_pattern: Pattern[str] = re.compile(r"\[(\d+),(\d+)\]\[(\d+),(\d+)\]")

    def __init__( self
                , env: AndroidEnv
                , tokenizer: PreTrainedTokenizer
                , nb_click_frames: int = 3
                , nb_scroll_frmaes: int = 10
                , wait_sec: float = 0.
                , action_batch: bool = False
                ):
        #  method __init__ {{{ # 
        """
        Args:
            env (AndroidEnv): the environment to be wrapped
            tokenizer (PreTrainedTokenizer): tokenizer to tokenize the input
              text into the tokens from the vocabulary of the environment
            nb_click_frames (int): the duration the TOUCH action will last for
              the CLICK iteraction
            nb_scroll_frmaes (int): the duration the TOUCH action will last for
              the SCROLL iteraction
            wait_sec (float): waiting time after each action performed
            action_batch (bool): if actions are combined in a batch
        """

        super(VhIoWrapper, self).__init__(env)

        self._bbox_list: List[List[int]] = [] # bboxes are saved as [x0, y0, x1, y1]
        self._instructions: List[str] = []

        self._tokenizer: PreTrainedTokenizer = tokenizer
        self._nb_click_frames: int = nb_click_frames
        self._nb_scroll_frames: int = nb_scroll_frmaes
        self._wait_sec: float = wait_sec
        self._action_batch: bool = action_batch

        self._env_steps: int = 0

        self._action_spec: Dict[str, specs.Array] =\
                { "action_type": specs.DiscreteArray( num_values=len(VhIoWrapper.ActionType)
                                                    , name="action_type"
                                                    )
                , "element_id": specs.DiscreteArray( num_values=max(1, len(self._bbox_list))
                                                   , name="element_id"
                                                   )
                , "text": specs.StringArray( shape=()
                                           , name="text"
                                           )
                , "direction": specs.DiscreteArray( num_values=len(VhIoWrapper.ScrollDirection)
                                                  , name="direction"
                                                  )
                , "response": specs.StringArray( shape=()
                                               , name="response"
                                               )
                }

        scroll_trajectory = np.linspace(0.2, 0.8, num=self._nb_scroll_frames, dtype=np.float32)
        scroll_trajectory = np.stack( [ scroll_trajectory
                                      , np.full( (self._nb_scroll_frames,)
                                               , 0.5
                                               , dtype=np.float32
                                               )
                                      ]
                                    , axis=1
                                    ) # (SF, 2); SF = self._nb_scroll_frames
        self._direction_trajectories: Dict[ VhIoWrapper.ScrollDirection
                                          , np.ndarray
                                          ] = { VhIoWrapper.ScrollDirection.LEFT:
                                                    scroll_trajectory
                                              , VhIoWrapper.ScrollDirection.UP:
                                                    scroll_trajectory[:, [1, 0]]
                                              , VhIoWrapper.ScrollDirection.RIGHT:
                                                    scroll_trajectory[::-1]
                                              , VhIoWrapper.ScrollDirection.DOWN:
                                                    scroll_trajectory[::-1, [1, 0]]
                                              }
        #  }}} method __init__ # 

    def action_spec(self) -> Dict[str, specs.Array]:
        #  method action_spec {{{ # 
        self._action_spec["element_id"] = specs.DiscreteArray( num_values=max(1, len(self._bbox_list))
                                                             , name="element_id"
                                                             )
        return self._action_spec
        #  }}} method action_spec # 

    def _process_action(self, action: Dict[str, np.ndarray])\
            -> List[Dict[str, np.ndarray]]:
        #  method _process_action {{{ # 
        """
        Args:
            action (Dict[str, np.ndarray]): dict like
              {
                "action_type": NOTHING | GOBACK
              } or
              {
                "action_type": CLICK
                "element_id": int
              } or
              {
                "action_type": INPUT
                "element_id": int
                "text": str
              } or
              {
                "action_type": SCROLL
                "direction": Direction
              }
              all the values in `action` are wrapped in np.ndarray.

        Return:
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

        if action["action_type"]==VhIoWrapper.ActionType.NOTHING:
            return [{"action_type": np.array(action_type.ActionType.REPEAT, dtype=np.int32)}]
        if action["action_type"]==VhIoWrapper.ActionType.GOBACK:
            return []

        actions: List[Dict[str, np.ndarray]] = []

        if "element_id" in action:
            bbox: List[int] = self._bbox_list[action["element_id"]]
            x = (bbox[0]+bbox[2])/2./self._env.observation_spec()["pixels"].shape[1]
            y = (bbox[1]+bbox[3])/2./self._env.observation_spec()["pixels"].shape[0]

            touch_action = { "action_type": np.array( action_type.ActionType.TOUCH
                                                    , dtype=np.int32
                                                    )
                           , "touch_position": np.array( [x, y]
                                                       , dtype=np.float32
                                                       )
                           }
            lift_action = { "action_type": np.array( action_type.ActionType.LIFT
                                                   , dtype=np.int32
                                                   )
                          , "touch_position": np.array( [x, y]
                                                      , dtype=np.float32
                                                      )
                          }
            actions += [touch_action] * self._nb_click_frames
            actions.append(lift_action)

        if action["action_type"]==VhIoWrapper.ActionType.CLICK:
            return actions
        if action["action_type"]==VhIoWrapper.ActionType.INPUT:
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
        if action["action_type"]==VhIoWrapper.ActionType.SCROLL:
            for pst in self._direction_trajectories[action["direction"].item()]:
                actions.append( { "action_type": np.array( action_type.ActionType.TOUCH
                                                         , dtype=np.int32
                                                         )
                                , "touch_position": pst
                                }
                              )
            return actions
        #  }}} method _process_action # 

    def _process_timestep(self, timestep: dm_env.TimeStep) -> dm_env.TimeStep:
        #  method _process_timestep {{{ # 
        self._bbox_list: List[List[int]] = filter_elements(timestep.observation["view_hierarchy"])[1]
        return timestep
        #  }}} method _process_timestep # 

    def step(self, action: Dict[str, np.ndarray]) -> dm_env.TimeStep:
        #  method step {{{ # 
        """
        Args:
            action (Dict[str, np.ndarray): vh-element-wise action

        Returns:
            dm_env.TimeStep
        """

        actions: List[Dict[str, np.ndarray]] = self._process_action(action)
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
                #step_type: dm_env.StepType
                #reward: float
                #discount: float
                #observation: Dict[str, Any]
                #step_type, reward, discount, observation = self._env.step(act)
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

        if action["action_type"]==VhIoWrapper.ActionType.INPUT:
            self._env._coordinator._task_manager._adb_controller.input_key("KEYCODE_ENTER")
        elif action["action_type"]==VhIoWrapper.ActionType.GOBACK:
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

        if self._wait_sec>0.:
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

        timestep: dm_env.TimeStep = self._process_timestep(timestep)

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

    def android_logs(self) -> Dict[str, Number]:
        """
        Returns a dictionary of metrics logged by the environment.
        """
        logs: Dict[str, Number] = self._env.android_logs()
        logs.update({'env_steps': self._env_steps})
        return logs
