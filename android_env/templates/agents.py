# Copyright 2025 SJTU X-Lance Lab
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
# Created by Danyang Zhang @X-Lance

import abc
from typing import Optional, Generic, TypeVar

Obs = TypeVar("Observation")
Act = TypeVar("Action")
Reset = TypeVar("Optional information returned after agent resetting")

class WikiHowAgent(abc.ABC, Generic[Obs, Act, Reset]):
    #  class WikiHowAgent {{{ # 
    def __init__(self):
        #  method __init__ {{{ # 
        self._instruction_history: List[str] = []
        self._action_history: List[str] = []
        self._total_reward: float = 0.

        #  }}} method __init__ # 

    @property
    @abc.abstractmethod
    def _default_empty_action(self) -> Act:
        raise NotImplementedError()

    def __call__( self
                , instruction: Optional[str] = None
                , observation: Optional[Obs] = None
                , last_reward: Optional[float] = None
                , **kwargs
                ) -> Act:
        #  method __call__ {{{ # 
        if instruction is not None and len(instruction)>0:
            self._instruction_history.append(instruction)
        if last_reward is not None:
            self._total_reward += last_reward

        action: Optional[Act] =\
                self._get_action( instruction=instruction
                                , observation=observation
                                , last_reward=last_reward
                                , **kwargs
                                )
        if action is not None:
            self._action_history.append(action)
            return action
        return self._default_empty_action
        #  }}} method __call__ # 

    @abc.abstractmethod
    def _get_action( self
                   , instruction: Optional[str] = None
                   , observation: Optional[Obs] = None
                   , last_reward: Optional[float] = None
                   , **kwargs
                   ) -> Optional[Act]:
        raise NotImplementedError()

    def reset(self, *args, **kwargs) -> Optional[Reset]:
        #  method reset {{{ # 
        """
        Called at the beginning of each episode.
        """

        self._instruction_history = []
        self._action_history = []
        self._total_reward = 0.
        #  }}} method reset # 

    def clear(self):
        #  method clear {{{ # 
        """
        Called to totally clear all the internal states so that the agent will
          work as a new-constructed agent.
        """

        self.reset()
        #  }}} method clear # 
    #  }}} class WikiHowAgent # 

class NaiveTextLLMAgent(WikiHowAgent[str, str, None]):
    #  NaiveTextLLMAgent {{{ # 
    # TODO
    pass
    #  }}} NaiveTextLLMAgent # 

class SimpleTextLLMAgent(WikiHowAgent[Dict[str, np.ndarray], Dict[str, np.ndarray], None]):
    #  class SimpleTextLLMAgent {{{ # 
    # TODO
    pass
    #  }}} class SimpleTextLLMAgent # 
