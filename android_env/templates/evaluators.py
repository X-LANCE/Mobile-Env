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

from android_env.interfaces.env import Environment
from android_env.interfaces.timestep import TimeStep
from android_env.templates.agents import MobileEnvAgent, SimpleTextLLMAgent, SimpleVLMAgent
from android_env.templates.agents import Obs, Act, Reset
from android_env.templates.prompt_template import TemplateGroup
from android_env.templates.utils import ( parse_vh_vlm_action_from_action_markup
                                        , convert_action_object_to_history
                                        )
from android_env.components.tools.easyocr_wrapper import EasyOCRWrapper
from android_env.components.coordinator import EventCheckControl
import android_env
from typing import TypedDict, List, Tuple, Dict
from typing import Optional, Any, Literal
from numbers import Number
from pathlib import Path
from os import PathLike
import os
import functools

import gzip
import pickle as pkl

class Metrics(TypedDict):
    #  class Metrics {{{ # 
    step: List[Number]
    reward: List[Number]
    success: List[Number]
    #  }}} class Metrics # 

class StepRecord(TypedDict):
    #  class TypedDict {{{ # 
    instruction: str
    observation: Obs
    reward: float
    action: Optional[Act]
    #  }}} class TypedDict # 

EvalFlow = List[str]

def evaluate_task( env: Environment, task_index: int
                 , agent: MobileEnvAgent[Obs, Act, Reset]
                 , max_steps: int
                 , save_to: Optional[PathLike]
                 ) -> Tuple[Metrics, EvalFlow]:
    #  evaluate_task {{{ # 
    trajectory: List[StepRecord] = []
    eval_flow: EvalFlow = []
    instructions: List[str] = []

    step: TimeStep = env.switch_task(task_index)
    eval_flow.append("--- {:d}.{:}".format(task_index, env.task_id))
    command: List[str] = env.command()
    instruction: str = "\n".join(command + env.task_instructions())
    eval_flow.append("< {:}".format(instruction))
    instructions.append(instruction)

    nb_steps = 0
    reward: float = step.reward
    while not step.last():
        action: Act = agent(instruction, step.observation, step.reward)
        eval_flow.append("> {:d}: {:}".format(nb_steps, str(action)))

        step_record: StepRecord = { "instruction": instruction
                                  , "observation": step.observation
                                  , "reward": step.reward
                                  , "action": action
                                  }
        trajectory.append(step_record)

        step = env.step(action)
        instruction = "\n".join(env.task_instructions())
        if len(instruction)>0:
            eval_flow.append("< {:}".format(instruction))
            instructions.append(instruction)
        if step.reward!=0:
            eval_flow.append("+ {:.4f}".format(step.reward))
        reward += step.reward

        nb_steps += 1
        if nb_steps>=max_steps:
            break

    step_record = { "instruction": instruction
                  , "observation": step.observation
                  , "reward": step.reward
                  , "action": action
                  }
    trajectory.append(step_record)
    trajectory_dict: Dict[str, Any] = { "task_id": env.task_id
                                      , "instructions": instructions
                                      , "trajectory": trajectory
                                      , "success": step.is_success()
                                      , "total_reward": reward
                                      }
    if save_to is not None:
        with gzip.open(save_to, "wb") as f:
            pkl.dump(trajectory_dict, f)

    eval_flow.append("END: {:}".format(str(step.is_success())))
    metrics: Metrics = { "step": nb_steps
                       , "reward": reward
                       , "success": step.is_success()
                       }
    return metrics, eval_flow
    #  }}} evaluate_task # 

def evaluate_llm_agent( task_path: PathLike, avd_name: str, save_traj_to: Optional[PathLike]
                      , input_tokenizer: PathLike = None
                      , llm_type: Literal["text", "vlm"], prompt_template_path: PathLike
                      , model_name: str, api_key: str, base_url: Optional[str] = None
                      , max_tokens: int = 100, temperature: float = .1
                      , prompt_flag_macros: Optional[List[str]] = None
                      , prompt_value_macros: Optional[Dict[str, str]] = None
                      , starts_from: int = 0, ends_at: Optional[int] = None
                      , mitm_config: Optional[Dict[str, str]] = None
                      , ocr_langs: List[str] = ["en", "ch_sim"]
                      , print_results: bool = True
                      , android_avd_home: PathLike = Path("~/.android_env/avd").expanduser()
                      , android_sdk_root: PathLike = Path("~/Android/Sdk").expanduser()
                      , env_load_kwargs: Dict[str, Any] = {}
                      ) -> Tuple[Metrics, EvalFlow]:
    #  function evaluate_llm_agent {{{ # 
    """
    Inits a `SimpleTextLLMAgent` or `SimpleVLMAgent` and evaluate it on the
    task set constructed from `task_path`.

    Args:
        task_path (PathLike): the path to the task set
        avd_name (str): the AVD to use
        save_traj_to (Optional[PathLike]): the path to save the evaluation
          trajectories. None for not saving.
        input_tokenizer (PathLike): the tokenizer used for INPUT/TYPE actions

        llm_type (str): "text" | "vlm"
        prompt_template_path (PathLike): the prompt to use with
          `SimpleTextLLMAgent` or `SimpleVLMAgent`
        model_name (str): LLM model name to invoke
        api_key (str): API key to use
        base_url (Optional[str]): base url of OpenAI-style LLM endpoint

        max_tokens (int): max number of tokens to generate
        temperature (float): generating temperature

        prompt_flag_macros (Optional[List[str]]): flag macros used to construct
          prompt template
        prompt_value_macros (Optional[Dict[str, str]]): value macros used to
          construct prompt template

        starts_from (int): evaluation will only be conducted on tasks from the
          `starts_from` to `ends_at`
        ends_at (int): evaluation will only be conducted on tasks from the
          `starts_from` to `ends_at`

        mitm_config (Optional[Dict[str, str]]): mitm config for Mobile-Env
        ocr_langs (List[str]): enabled languages for OCR model

        print_results (bool): if the results should be printed to console

        android_avd_home (PathLike): the home directory of AVDs
        android_sdk_root (PathLike): the root directory of Android SDKs

        env_load_kwargs (Dict[str, Any]): other keyword arguments for
          `android_env.load` function

    Returns:
        Metrics: result metrics
        EvalFlow: the evaluation trajectory (without observations)
    """

    # 1. build agent
    prompt_template: TemplateGroup =  TemplateGroup.parse(
                                        os.fspath(prompt_template_path)
                                      , flag_macros=prompt_flag_macros
                                      , value_macros==prompt_value_macros
                                      )
    agent: MobileEnvAgent
    if llm_type=="text":
        action_parser: Callable[[str], Dict[str, np. ndarray]] =\
                functools.partial( parse_vh_vlm_action_from_action_markup
                                 , parse_for="vh_env"
                                 )
        action_serializer: Callable[[Dict[str, np.ndarray]], str] =\
                functools.partial( convert_action_object_to_history
                                 , action_for="vh_env"
                                 )
        agent = SimpleTextLLMAgent( prompt_template
                                  , action_parser, action_serializer
                                  , model_name=model_name, api_key=api_key, base_url=base_url
                                  , max_tokens=max_tokens, temperature=temperature
                                  )
    elif llm_type=="vlm":
        action_parser: Callable[[str], Dict[str, np. ndarray]] =\
                functools.partial( parse_vh_vlm_action_from_action_markup
                                 , parse_for="tap_env"
                                 )
        action_serializer: Callable[[Dict[str, np.ndarray]], str] =\
                functools.partial( convert_action_object_to_history
                                 , action_for="tap_env"
                                 )
        agent = SimpleVLMAgent( prompt_template
                              , action_parser, action_serializer
                              , model_name=model_name, api_key=api_key, base_url=base_url
                              , max_tokens=max_tokens, temperature=temperature
                              )
    else:
        raise NotImplementedError("Unsupported LLM type: {:}".format(llm_type))

    # 2. build environment
    obs_with_view_hierarchy: bool = llm_type=="text"
    env: Environment = android_env.load( os.fspath(task_path), avd_name
                                       , android_avd_home=os.fspath(android_avd_home)
                                        , android_sdk_root=os.fspath(android_sdk_root)
                                        , emulator_path=os.path.join(android_sdk_root, "emulator/emulator")
                                        , adb_path=os.path.join(android_sdk_root, "platform-tools/adb")
                                        , run_headless=True
                                        , mitm_config=mitm_config
                                        , unify_vocabulary=os.path.join(input_tokenizer, "vocab.txt")
                                        , text_model=EasyOCRWrapper(lang_list=ocr_langs)
                                        , with_view_hierarchy=obs_with_view_hierarchy
                                        , coordinator_args={ "vh_check_control_method": EventCheckControl.LIFT
                                                            , "screen_check_control_method": EventCheckControl.LIFT
                                                            , "step_timeout_sec": 60.
                                                            , "max_cached_task_managers": 1
                                                            , "periodic_restart_time_min": 600

    #  }}} function evaluate_llm_agent # 

def evaluate_llm_agent_mp():
    #  function evaluate_llm_agent_mp {{{ # 
    # TODO: implement with Python multiprocessing
    pass
    #  }}} function evaluate_llm_agent_mp # 

def evaluate_llm_agent_mpi():
    #  function evaluate_llm_agent_mpi {{{ # 
    # TODO: implement with MPI
    pass
    #  }}} function evaluate_llm_agent_mpi # 
