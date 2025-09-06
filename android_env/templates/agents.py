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
from typing import Optional, Generic, TypeVar, Callable
from typing import List, Dict

from android_env.templates.prompt_template import TemplateGroup, PromptGroupT
from android_env.templates.llm_caller import OpenAIProxy
from android_env.templates.llm_caller import ResponseError as LC_ResponseError
import openai
import numpy as np

from android_env.wrappers import VhIoWrapper, TapActionWrapper
#from copy import deepcopy
from android_env.templates.utils import convert_vh_to_html_list
from PIL import Image

import logging

logger = logging.getLogger("mobile_env.agents")

Obs = TypeVar("Observation")
Act = TypeVar("Action")
Reset = TypeVar("Optional information returned after agent resetting")

class MobileEnvAgent(abc.ABC, Generic[Obs, Act, Reset]):
    #  class MobileEnvAgent {{{ # 
    def __init__(self):
        #  method __init__ {{{ # 
        self._instruction_history: List[str] = []
        self._action_history: List[Act] = []
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
                self._get_action( observation=observation
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
    #  }}} class MobileEnvAgent # 

class NaiveTextLLMAgent(MobileEnvAgent[str, str, None]):
    #  NaiveTextLLMAgent {{{ # 
    """
    Naive Text-LLM-based agent directly accepting observation in str and
    returning action in str.
    """

    def __init__( self
                , prompt_template: TemplateGroup
                , action_parser: Callable[[str], str]
                , empty_action: str = "DO_NOTHING()"
                , llm_caller_function: Optional[Callable[[PromptGroupT, int, float], str]] = None
                , model_name: Optional[str] = None
                , api_key: Optional[str] = None
                , base_url: Optional[str] = None
                , max_tokens: int = 100
                , temperature: float = .1
                ):
        #  function __init__ {{{ # 
        """
        Args:
            prompt_template (TemplateGroup): prompt template for the LLM. the
              slots to be filled include
              * history_instructions: '\n'-joined instructions for the early
                stages
              * current_instruction: the instruction for the current stage
              * screen: screen representation in str
              * action_history: '\n'-joined history action list
            action_parser (Callable[[str], str]): function to parse action from
              the llm response

            empty_action (str): the format of the empty action. related to the
              specific prompt (or model)

            llm_caller_function (Optional[Callable[[PromptGroupT, int, float], str]]):
              function to invoke the LLM. the parameters are
              * PromptGroupT: the input message
              * int: the max number of tokens to generate
              * float: generation temperature
              if given, `api_key` and `base_url` arguments will be ignored. if
              not given, an instance of
              `android_env.templates.llm_caller.OpenAIProxy` will be built
              accroding to `api_key` and `base_url`
            model_name (Optional[str]): if `llm_caller_function`, this argument
              will be used to build a LLM caller. model name to invoke
            api_key (Optional[str]): if `llm_caller_function`, this argument
              will be used to build a LLM caller.
            base_url (Optional[str]): if `llm_caller_function`, this argument
              will be used to build a LLM caller. keep None if change of base
              url is not needed.

            max_tokens (int): max number of tokens to generate
            temperature (float): generation temperature
        """

        super(NaiveTextLLMAgent, self).__init__()

        self._prompt_template: TemplateGroup = prompt_template
        self._parse_action: Callable[[str], str] = action_parser

        if llm_caller_function is not None:
            self._llm_caller: Callable[[PromptGroupT, int, float], str] = llm_caller_function
        else:
            assert model_name is not None and api_key is not None\
                 , "`model_name` and `api_key` are required to build OpenAIProxy when `llm_caller_function` argument is missed"
            self._llm_caller: Callable[[PromptGroupT, int, float], str] =\
                    OpenAIProxy(api_key, base_url, model_name)

        self._max_tokens: int = max_tokens
        self._temperature: float = temperature

        self._empty_action: str = empty_action
        #  }}} function __init__ # 

    @property
    def _default_empty_action(self) -> str:
        return self._empty_action

    def _get_action( self
                   , observation: Optional[str] = None
                   , last_reward: Optional[float] = None
                   , **kwargs
                   ) -> Optional[str]:
        #  method _get_action {{{ # 
        if observation is None:
            return None
        
        message: PromptGroupT =\
                self._prompt_template.safe_substitute(
                        text_mapping={ "history_instructions":
                                        "\n".join(self._instruction_history[:-1])
                                     , "current_instruction":
                                        self._instruction_history[-1] if len(self._instruction_history)>0 else ""
                                     , "screen": observation
                                     , "action_history": "\n".join(self._action_history)
                                     }
                      )
        try:
            response: str = self._llm_caller(message, self._max_tokens, self._temperature)
        except (openai.BadRequestError, LC_ResponseError, openai.InternalServerError):
            logger.exception("LLM Request Error!")
            action = None

        try:
            action: str = self._parse_action(response)
        except:
            logger.exception("Action Parsing Error!")
            action: str = self._default_empty_action
        return action
        #  }}} method _get_action # 
    #  }}} NaiveTextLLMAgent # 

class SimpleTextLLMAgent(MobileEnvAgent[Dict[str, np.ndarray], Dict[str, np.ndarray], None]):
    #  class SimpleTextLLMAgent {{{ # 
    """
    Simple Text-LLM-based agent working with `android_env.wrappers.VhIoWrapper`
    """

    def __init__( self
                , prompt_template: TemplateGroup
                , action_parser: Callable[[str], Dict[str, np.ndarray]]
                , serialize_action: Callable[[Dict[str, np.ndarrray]], str]
                , llm_caller_function: Optional[Callable[[PromptGroupT, int, float], str]] = None
                , model_name: Optional[str] = None
                , api_key: Optional[str] = None
                , base_url: Optional[str] = None
                , max_tokens: int = 100
                , temperature: float = .1
                ):
        #  method __init__ {{{ # 
        """
        Args:
            prompt_template (TemplateGroup): prompt template for the LLM. the
              slots to be filled include
              * history_instructions: '\n'-joined instructions for the early
                stages
              * current_instruction: the instruction for the current stage
              * screen: screen representation in str
              * action_history: '\n'-joined history action list
            action_parser (Callable[[str], Dict[str, np.ndarray]]): function to
              parse action from the llm response
            serialize_action (Callable[[Dict[str, np.ndarrray]], str]):
              function to serialize action to str so that it can be inserted
              into the prompt

            llm_caller_function (Optional[Callable[[PromptGroupT, int, float], str]]):
              function to invoke the LLM. the parameters are
              * PromptGroupT: the input message
              * int: the max number of tokens to generate
              * float: generation temperature
              if given, `api_key` and `base_url` arguments will be ignored. if
              not given, an instance of
              `android_env.templates.llm_caller.OpenAIProxy` will be built
              accroding to `api_key` and `base_url`
            model_name (Optional[str]): if `llm_caller_function`, this argument
              will be used to build a LLM caller. model name to invoke
            api_key (Optional[str]): if `llm_caller_function`, this argument
              will be used to build a LLM caller.
            base_url (Optional[str]): if `llm_caller_function`, this argument
              will be used to build a LLM caller. keep None if change of base
              url is not needed.

            max_tokens (int): max number of tokens to generate
            temperature (float): generation temperature
        """

        super(SimpleTextLLMAgent, self).__init__()

        self._prompt_template: TemplateGroup = prompt_template
        self._parse_action: Callable[[str], Dict[str, np.ndarray]] = action_parser
        self._serialize_action: Callable[[Dict[str, np.ndarray]], str] = serialize_action

        if llm_caller_function is not None:
            self._llm_caller: Callable[[PromptGroupT, int, float], str] = llm_caller_function
        else:
            assert model_name is not None and api_key is not None\
                 , "`model_name` and `api_key` are required to build OpenAIProxy when `llm_caller_function` argument is missed"
            self._llm_caller: Callable[[PromptGroupT, int, float], str] =\
                    OpenAIProxy(api_key, base_url, model_name)

        self._max_tokens: int = max_tokens
        self._temperature: float = temperature
        #  }}} method __init__ # 

    @property
    def _default_empty_action(self) -> Dict[str, np.ndarray]:
        return {"action_type": VhIoWrapper.ActionType.NOTHING}

    def _get_action( self
                   , observation: Optional[Dict[str, np.ndarray]] = None
                   , last_reward: Optional[float] = None
                   , **kwargs
                   ) -> Optional[Dict[str, np.ndarray]]:
        #  method _get_action {{{ # 
        if observation is None or observation.get("view_hierarchy", None) is None:
            return None

        screen_representation: str = convert_vh_to_html_list(observation["view_hierarchy"])

        message: PromptGroupT =\
                self._prompt_template.safe_substitute(
                        text_mapping={ "history_instructions":
                                        "\n".join(self._instruction_history[:-1])
                                     , "current_instruction":
                                        self._instruction_history[-1] if len(self._instruction_history)>0 else ""
                                     , "screen": screen_representation
                                     , "action_history": "\n".join(map(self._serialize_action, self._action_history))
                                     }
                      )
        try:
            response: str = self._llm_caller(message, self._max_tokens, self._temperature)
        except (openai.BadRequestError, LC_ResponseError, openai.InternalServerError):
            logger.exception("LLM Request Error!")
            action = None

        try:
            action: Dict[str, np.ndarray] = self._parse_action(response)
        except:
            logger.exception("Action Parsing Error!")
            action: Dict[str, np.ndarray] = self._default_empty_action

        return action
        #  }}} method _get_action # 
    #  }}} class SimpleTextLLMAgent # 

class NaiveVLMAgent(MobileEnvAgent[np.ndarray, str, None]):
    #  class NaiveVLMAgent {{{ # 
    """
    Naive VLM-based agent accepting screen observation in image and returning
    action in str.
    """

    def __init__( self
                , prompt_template: TemplateGroup
                , action_parser: Callable[[str], str]
                , empty_action: str = "DO_NOTHING()"
                , llm_caller_function: Optional[Callable[[PromptGroupT, int, float], str]] = None
                , model_name: Optional[str] = None
                , api_key: Optional[str] = None
                , base_url: Optional[str] = None
                , max_tokens: int = 100
                , temperature: float = .1
                ):
        #  method __init__ {{{ # 
        """
        Args:
            prompt_template (TemplateGroup): prompt template for the LLM. the
              text slots to be filled include
              * history_instructions: '\n'-joined instructions for the early
                stages
              * current_instruction: the instruction for the current stage
              * action_history: '\n'-joined history action list
              the image slot to be filled include
              * screen: screen representation
            action_parser (Callable[[str], str]): function to parse action from
              the llm response

            empty_action (str): the format of the empty action. related to the
              specific prompt (or model)

            llm_caller_function (Optional[Callable[[PromptGroupT, int, float], str]]):
              function to invoke the LLM. the parameters are
              * PromptGroupT: the input message
              * int: the max number of tokens to generate
              * float: generation temperature
              if given, `api_key` and `base_url` arguments will be ignored. if
              not given, an instance of
              `android_env.templates.llm_caller.OpenAIProxy` will be built
              accroding to `api_key` and `base_url`
            model_name (Optional[str]): if `llm_caller_function`, this argument
              will be used to build a LLM caller. model name to invoke
            api_key (Optional[str]): if `llm_caller_function`, this argument
              will be used to build a LLM caller.
            base_url (Optional[str]): if `llm_caller_function`, this argument
              will be used to build a LLM caller. keep None if change of base
              url is not needed.

            max_tokens (int): max number of tokens to generate
            temperature (float): generation temperature
        """

        super(NaiveVLMAgent, self).__init__()

        self._prompt_template: TemplateGroup = prompt_template
        self._parse_action: Callable[[str], str] = action_parser

        if llm_caller_function is not None:
            self._llm_caller: Callable[[PromptGroupT, int, float], str] = llm_caller_function
        else:
            assert model_name is not None and api_key is not None\
                 , "`model_name` and `api_key` are required to build OpenAIProxy when `llm_caller_function` argument is missed"
            self._llm_caller: Callable[[PromptGroupT, int, float], str] =\
                    OpenAIProxy(api_key, base_url, model_name)

        self._max_tokens: int = max_tokens
        self._temperature: float = temperature

        self._empty_action: str = empty_action
        #  }}} method __init__ # 

    @property
    def _default_empty_action(self) -> str:
        return self._empty_action

    def _get_action( self
                   , observation: Optional[np.ndarray] = None
                   , last_reward: Optional[float] = None
                   , **kwargs
                   ) -> Optional[str]:
        #  method _get_action {{{ # 
        """
        Args:
            observation (Optional[np.ndarray]): the image representation of the
              screen. is expected to be have the shape like (H, W, 3) with
              channels RGB.
            last_reward (Optional[float]): the reward of the last step

        Returns:
            str: the action representation
        """

        if observation is None:
            return None

        message: PromptGroupT =\
                self._prompt_template.safe_substitute(
                        text_mapping={ "history_instructions":
                                        "\n".join(self._instruction_history[:-1])
                                     , "current_instruction":
                                        self._instruction_history[-1] if len(self._instruction_history)>0 else ""
                                     , "action_history": "\n".join(self._action_history)
                                     }
                      , img_mapping={"screen": Image.fromarray(observation)}
                      )
        try:
            response: str = self._llm_caller(message, self._max_tokens, self._temperature)
        except (openai.BadRequestError, LC_ResponseError, openai.InternalServerError):
            logger.exception("LLM Request Error!")
            action = None

        try:
            action: str = self._parse_action(response)
        except:
            logger.exception("Action Parsing Error!")
            action: str = self._default_empty_action
        return action
        #  }}} method _get_action # 
    #  }}} class NaiveVLMAgent # 

class SimpleVLMAgent(MobileEnvAgent[Dict[str, np.ndarray], Dict[str, np.ndarray], None]):
    #  class SimpleVLMAgent {{{ # 
    """
    Simple VLM-based agent working with `android_env.wrappers.TapActionWrapper`
    """

    def __init__( self
                , prompt_template: TemplateGroup
                , action_parser: Callable[[str], Dict[str, np.ndarray]]
                , serialize_action: Callable[[Dict[str, np.ndarrray]], str]
                , llm_caller_function: Optional[Callable[[PromptGroupT, int, float], str]] = None
                , model_name: Optional[str] = None
                , api_key: Optional[str] = None
                , base_url: Optional[str] = None
                , max_tokens: int = 100
                , temperature: float = .1
                ):
        #  method __init__ {{{ # 
        """
        Args:
            prompt_template (TemplateGroup): prompt template for the LLM. the
              slots to be filled include
              * history_instructions: '\n'-joined instructions for the early
                stages
              * current_instruction: the instruction for the current stage
              * action_history: '\n'-joined history action list
              the image slot to be filled include
              * screen: screen representation
            action_parser (Callable[[str], Dict[str, np.ndarray]]): function to
              parse action from the llm response
            serialize_action (Callable[[Dict[str, np.ndarrray]], str]):
              function to serialize action to str so that it can be inserted
              into the prompt

            llm_caller_function (Optional[Callable[[PromptGroupT, int, float], str]]):
              function to invoke the LLM. the parameters are
              * PromptGroupT: the input message
              * int: the max number of tokens to generate
              * float: generation temperature
              if given, `api_key` and `base_url` arguments will be ignored. if
              not given, an instance of
              `android_env.templates.llm_caller.OpenAIProxy` will be built
              accroding to `api_key` and `base_url`
            model_name (Optional[str]): if `llm_caller_function`, this argument
              will be used to build a LLM caller. model name to invoke
            api_key (Optional[str]): if `llm_caller_function`, this argument
              will be used to build a LLM caller.
            base_url (Optional[str]): if `llm_caller_function`, this argument
              will be used to build a LLM caller. keep None if change of base
              url is not needed.

            max_tokens (int): max number of tokens to generate
            temperature (float): generation temperature
        """

        super(SimpleVLMAgent, self).__init__()

        self._prompt_template: TemplateGroup = prompt_template
        self._parse_action: Callable[[str], Dict[str, np.ndarray]] = action_parser
        self._serialize_action: Callable[[Dict[str, np.ndarray]], str] = serialize_action

        if llm_caller_function is not None:
            self._llm_caller: Callable[[PromptGroupT, int, float], str] = llm_caller_function
        else:
            assert model_name is not None and api_key is not None\
                 , "`model_name` and `api_key` are required to build OpenAIProxy when `llm_caller_function` argument is missed"
            self._llm_caller: Callable[[PromptGroupT, int, float], str] =\
                    OpenAIProxy(api_key, base_url, model_name)

        self._max_tokens: int = max_tokens
        self._temperature: float = temperature
        #  }}} method __init__ # 

    @property
    def _default_empty_action(self) -> Dict[str, np.ndarray]:
        return {"action_type": TapActionWrapper.ActionType.NOTHING}

    def _get_action( self
                   , observation: Optional[Dict[str, np.ndarray]] = None
                   , last_reward: Optional[float] = None
                   , **kwargs
                   ) -> Optional[Dict[str, np.ndarray]]:
        #  method _get_action {{{ # 
        if observation is None or observation.get("pixels", None) is None:
            return None

        message: PromptGroupT =\
                self._prompt_template.safe_substitute(
                        text_mapping={ "history_instructions":
                                        "\n".join(self._instruction_history[:-1])
                                     , "current_instruction":
                                        self._instruction_history[-1] if len(self._instruction_history)>0 else ""
                                     , "action_history": "\n".join(map(self._serialize_action, self._action_history))
                                     }
                      , img_mapping={"screen": Image.fromarray(observation["pixels"])}
                      )
        try:
            response: str = self._llm_caller(message, self._max_tokens, self._temperature)
        except (openai.BadRequestError, LC_ResponseError, openai.InternalServerError):
            logger.exception("LLM Request Error!")
            action = None

        try:
            action: str = self._parse_action(response)
        except:
            logger.exception("Action Parsing Error!")
            action: str = self._default_empty_action
        return action
        #  }}} method _get_action # 
    #  }}} class SimpleVLMAgent # 
