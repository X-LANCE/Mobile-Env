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
from android_env.wrappers import VhIoWrapper, TapActionWrapper, ImageRescaleWrapper
import android_env
from typing import TypedDict, List, Tuple, Dict
from typing import Optional, Any, Literal, Callable
from numbers import Number
from pathlib import Path
from os import PathLike
import os
import functools
from transformers import AutoTokenizer
import numpy as np

import gzip
import pickle as pkl

import logging
import io
import traceback

import multiprocessing
from multiprocessing.pool import AsyncResult
from mpi4py import MPI

logger = logging.getLogger("mobile_env.evaluator")

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

class Diagnosis(TypedDict):
    #  class Diagnosis {{{ # 
    error_occurs: bool
    error_string: Optional[str]
    #  }}} class Diagnosis # 

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

def evaluate_llm_agent( *
                      , task_path: PathLike, avd_name: str, save_traj_to: Optional[PathLike]
                      , input_tokenizer: PathLike
                      , llm_type: Literal["text", "vlm"], prompt_template_path: PathLike
                      , model_name: str, api_key: str, base_url: Optional[str] = None
                      , max_tokens: int = 100, temperature: float = .1
                      , prompt_flag_macros: Optional[List[str]] = None
                      , prompt_value_macros: Optional[Dict[str, str]] = None
                      , starts_from: int = 0, ends_at: Optional[int] = None, max_steps: int = 15
                      , mitm_config: Optional[Dict[str, str]] = None
                      , ocr_langs: List[str] = ["en", "ch_sim"]
                      , restart_simulator_at_reset: bool = False
                      , screenshot_zoom_factors: Tuple[float, float] = (1., 1.)
                      , print_results: bool = True, save_eval_flow: bool = True
                      , android_avd_home: PathLike = Path("~/.android_env/avd").expanduser()
                      , android_sdk_root: PathLike = Path("~/Android/Sdk").expanduser()
                      , env_load_kwargs: Dict[str, Any] = {}
                      , text_vlm_env_wrapper_kwargs: Dict[str, Any] = {}
                      , custom_wrappers: List[Callable[[Environment], Environment]] = []
                      ) -> Tuple[Metrics, Metrics, EvalFlow, Diagnosis]:
    #  function evaluate_llm_agent {{{ # 
    """
    Inits a `SimpleTextLLMAgent` or `SimpleVLMAgent` and evaluates it on the
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
        ends_at (Optional[int]): evaluation will only be conducted on tasks
          from the `starts_from` to `ends_at`
        max_steps (int): max steps of episodes

        mitm_config (Optional[Dict[str, str]]): mitm config for Mobile-Env
        ocr_langs (List[str]): enabled languages for OCR model
        restart_simulator_at_reset (boo): whether the simulator needs to be
          restarted during environment reset
        screenshot_zoom_factors (Tuple[float, float]): zoom factors for
          screenshot. zoom factors are given for height and width sequentially

        print_results (bool): if the results should be printed to console
        save_eval_flow (bool): if the eval flow should be dumped to hard disk

        android_avd_home (PathLike): the home directory of AVDs
        android_sdk_root (PathLike): the root directory of Android SDKs

        env_load_kwargs (Dict[str, Any]): extra keyword arguments for
          `android_env.load` function
        text_vlm_env_wrapper_kwargs (Dict[str, Any]): extra keyword arguments
          for `VhIoWrapper` or `TapActionWrapper`
        custom_wrappers (List[Callable[[Environment], Environment]]):
          additional wrappers to apply upon `VhIoWrapper` and
          `TapActionWrapper`, applied in order. e.g.,
          `InstructionRewritingWrapper` for WikiHow task set.

    Returns:
        Metrics: average result metrics
        Metrics: verbose result metrics
        EvalFlow: the evaluation trajectory (without observations)
        Diagnosis: error messages
    """

    #  1. Build Agent {{{ # 
    prompt_template: TemplateGroup =  TemplateGroup.parse(
                                        os.fspath(prompt_template_path)
                                      , flag_macros=prompt_flag_macros
                                      , value_macros=prompt_value_macros
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
    logger.info("Agent Ready")
    #  }}} 1. Build Agent # 

    #  2. Build Environment {{{ # 
    obs_with_view_hierarchy: bool = llm_type=="text"
    other_coordinator_args: Dict[str, Any] = env_load_kwargs.pop("coordinator_args", {})
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
                                                          , "restart_simulator_at_reset": restart_simulator_at_reset
                                                          , **other_coordinator_args
                                                          }
                                       , **env_load_kwargs
                                       )
    if llm_type=="text":
        env = VhIoWrapper( env, AutoTokenizer.from_pretrained(input_tokenizer)
                         , wait_sec=1., retry_for_empty_view_hierarchy=3, action_batch=True
                         , **text_vlm_env_wrapper_kwargs
                         )
    elif llm_type=="vlm":
        env = ImageRescaleWrapper(env, zoom_factors=screenshot_zoom_factors)
        env = TapActionWrapper( env, AutoTokenizer.from_pretrained(input_tokenizer)
                              , wait_sec=1.5, action_batch=True
                              , **text_vlm_env_wrapper_kwargs
                              )
    for wrpp in custom_wrappers:
        env = wrpp(env)
    logger.info("Environment Ready")
    #  }}} 2. Build Environment # 

    if save_traj_to is not None:
        save_traj_to: Path = Path(save_traj_to)
        get_save_path: Callable[[int], Optional[Path]] = lambda i: save_traj_to/"{:d}.pkl.gz".format(i)
    else:
        get_save_path: Callable[[int], Optional[Path]] = lambda _: None
    if ends_at is None:
        ends_at: int = env.nb_tasks
    total_metrics: Metrics = {"step": [], "reward": [], "success": []}
    total_eval_flow: EvalFlow = []
    diagnosis: Diagnosis = {"error_occurs": False, "error_string": None}
    try:
        for i in range(starts_from, ends_at):
            task_metrics: Metrics
            task_eval_flow: EvalFlow
            task_metrics, task_eval_flow = evaluate_task( env, i, agent
                                                        , max_steps=max_steps
                                                        , save_to=get_save_path(i)
                                                        )
            for mtr in task_metrics:
                total_metrics.setdefault(mtr, []).extend(task_metrics[mtr])
            total_eval_flow += task_eval_flow
    except:
        diagnosis["error_occurs"] = True
        logger.exception("Eval Error!")
        with io.StringIO() as f:
            traceback.print_exc(file=f)
            diagnosis["error_string"]: str = f.getvalue()
    finally:
        average_metrics: Metrics = {}
        for mtr in total_metrics:
            average_metrics[mtr] = [np.mean(total_metrics[mtr]).item()]

    if save_eval_flow and save_traj_to is not None:
        (save_traj_to/"eval_flow.txt").write_text("\n".join(total_eval_flow))
    if print_results:
        print( "\x1b[42mCOMPLETEION with %s!\x1b[0m Avg #Steps: %.2f, Avg Reward: %.3f, SR: %.4f"\
             % ( "{:d}:{:d}".format(starts_from, ends_at)
               , average_metrics["step"][0], average_metrics["reward"][0], average_metrics["success"][0]
               )
             )

    return average_metrics, total_metrics, total_eval_flow, diagnosis
    #  }}} function evaluate_llm_agent # 

def evaluate_llm_agent_mp( nb_workers: int, starts_from: int, ends_at: int
                         , print_results: bool = True, save_eval_flow: bool = True
                         , **evaluation_arguments
                         ) -> Tuple[Metrics, Metrics, EvalFlow, Diagnosis]:
    #  function evaluate_llm_agent_mp {{{ # 
    """
    Inits `SimpleTextLLMAgent` or `SimpleVLMAgent` and evaluates it on the task
    set constructed from `task_path` with Python-based multiprocessing.

    Args:
        nb_workers (int): number of worker processes
        starts_from (int): evaluation will only be conducted on tasks from the
          `starts_from` to `ends_at`
        ends_at (int): evaluation will only be conducted on tasks from the
          `starts_from` to `ends_at`. NOTE THAT A POSITIVE INTEGER is required
          to dispense the tasks to workers.

        print_results (bool): if the results should be printed to console
        save_eval_flow (bool): if the eval flow should be dumped to hard disk

        evaluation_arguments (Dict[str, Any]): the arguments for
          `evaluate_llm_agent` function

    Returns:
        Metrics: average result metrics
        Metrics: verbose result metrics
        EvalFlow: the evaluation trajectory (without observations)
        Diagnosis: error messages
    """

    nb_tasks: int = ends_at-starts_from
    nb_tasks_per_rank: int
    remaining: int
    nb_tasks_per_rank, remaining = divmod(nb_tasks, nb_workers)
    split_points: np.ndarray = np.arange(nb_workers+1)
    split_points[:remaining+1] *= nb_tasks_per_rank+1
    split_points[remaining+1:] = split_points[remaining] + (split_points[remaining+1:]-remaining)*nb_tasks_per_rank
    split_points += starts_from

    eval_pool = multiprocessing.Pool(nb_workers)
    futures: List[AsyncResult] = []
    for i in range(nb_workers):
        future: AsyncResult = eval_pool.apply_async(
                                evaluate_llm_agent
                              , ()
                              , { **evaluation_arguments
                                , "starts_from": split_points[i]
                                , "ends_at": split_points[i+1]
                                , "print_results": False
                                , "save_eval_flow": False
                                }
                              )
        futures.append(future)

    total_metrics: Metrics = {"step": [], "reward": [], "success": []}
    total_eval_flow: EvalFlow = []
    total_diagnosis: Diagnosis = {"error_occurs": False, "error_string": []}
    ranges: List[str] = []
    for i, ftr in enumerate(futures):
        worker_metrics: Metrics
        worker_eval_flow: EvalFlow
        worker_diagnosis: Diagnosis
        _, worker_metrics, worker_eval_flow, worker_diagnosis = ftr.get()
        for mtr in worker_metrics:
            total_metrics.setdefault(mtr, []).extend(worker_metrics[mtr])
        total_eval_flow += worker_eval_flow
        if worker_diagnosis["error_occurs"]:
            total_diagnosis["error_occurs"] = True
            error_str: str = "Error in worker {:d}:\n{:}".format(i, worker_diagnosis["error_string"])
            logger.error(error_str)
            total_diagnosis["error_string"].append(error_str)
        ranges.append("{:d}:{:d}".format(split_points[i], split_points[i]+len(worker_metrics["success"])))
    average_metrics: Metrics = {}
    for mtr in total_metrics:
        average_metrics[mtr] = [np.mean(total_metrics[mtr]).item()]
    total_diagnosis["error_string"] = "\n\n---\n\n".join(total_diagnosis["error_string"])

    if save_eval_flow and evaluation_arguments["save_traj_to"] is not None:
        with open(os.path.join(evaluation_arguments["save_traj_to"], "eval_flow.txt"), "w") as f:
            f.write("\n".join(total_eval_flow))
    if print_results:
        print( "\x1b[42mCOMPLETEION with %s!\x1b[0m Avg #Steps: %.2f, Avg Reward: %.3f, SR: %.4f"\
             % ( ", ".join(ranges)
               , average_metrics["step"][0], average_metrics["reward"][0], average_metrics["success"][0]
               )
             )

    return average_metrics, total_metrics, total_eval_flow, total_diagnosis
    #  }}} function evaluate_llm_agent_mp # 

def evaluate_llm_agent_mpi( starts_from: int, ends_at: int
                          , print_results: bool = True, save_eval_flow: bool = True
                          , **evaluation_arguments
                          ) -> Tuple[ Tuple[Metrics, Metrics, EvalFlow, Diagnosis]
                                    , Tuple[Metrics, Metrics, EvalFlow, Diagnosis]
                                    ]:
    #  function evaluate_llm_agent_mpi {{{ # 
    """
    Inits `SimpleTextLLMAgent` or `SimpleVLMAgent` and evaluates it on the task
    set constructed from `task_path` with MPI.

    Args:
        starts_from (int): evaluation will only be conducted on tasks from the
          `starts_from` to `ends_at`
        ends_at (int): evaluation will only be conducted on tasks from the
          `starts_from` to `ends_at`. NOTE THAT A POSITIVE INTEGER is required
          to dispense the tasks to workers.

        print_results (bool): if the results should be printed to console
        save_eval_flow (bool): if the eval flow should be dumped to hard disk

        evaluation_arguments (Dict[str, Any]): the arguments for
          `evaluate_llm_agent` function

    Returns:
        - Metrics: average result metrics of the current rank
          Metrics: verbose result metrics of the current rank
          EvalFlow: the evaluation trajectory (without observations) of the
            current rank
          Diagnosis: error messages of the current rank
        - Metrics: reduced average result metrics across all ranks
          Metrics: reduced verbose result metrics across all ranks
          EvalFlow: reduced the evaluation trajectory (without observations)
            across all ranks
          Diagnosis: reduced error messages across all ranks
    """

    world = MPI.COMM_WORLD
    world_size = world.Get_size()
    world_rank = world.Get_rank()
    logger.debug("MPI world_size: %d, world_rank: %d, PID: %d", world_size, world_rank, os.getpid())

    nb_tasks: int = ends_at-starts_from
    nb_tasks_per_rank: int
    remaining: int
    nb_tasks_per_rank, remaining = divmod(nb_tasks, world_size)
    if world_rank<remaining:
        rank_starts_from: int = starts_from + world_rank*(nb_tasks_per_rank+1)
        rank_ends_at: int = starts_from + (world_rank+1)*(nb_tasks_per_rank+1)
    else:
        rank_starts_from: int = starts_from + remaining*(nb_tasks_per_rank+1) + (world_rank-remaining)*nb_tasks_per_rank
        rank_ends_at: int = starts_from + remaining*(nb_tasks_per_rank+1) + (world_rank-remaining+1)*nb_tasks_per_rank

    evaluation_arguments.pop("starts_from")
    evaluation_arguments.pop("ends_at")
    evaluation_arguments.pop("print_results")
    evaluation_arguments.pop("save_eval_flow")
    worker_avg_metrics: Metrics
    worker_metrics: Metrics
    worker_eval_flow: EvalFlow
    worker_diagnosis: Diagnosis
    worker_avg_metrics, worker_metrics, worker_eval_flow, worker_diagnosis =\
            evaluate_llm_agent( starts_from=rank_starts_from, ends_at=rank_ends_at
                              , print_results=False, save_eval_flow=False
                              , **evaluation_arguments
                              )
    world.Barrier()

    all_metrics: List[Metrics] = world.gather(worker_metrics, root=0)
    all_eval_flow: List[EvalFlow] = world.gather(worker_eval_flow, root=0)
    all_diagnosis: List[Diagnosis] = world.gather(worker_diagnosis, root=0)

    if world_rank==0:
        total_metrics: Metrics = {"step": [], "reward": [], "success": []}
        total_eval_flow: EvalFlow = []
        total_diagnosis: Diagnosis = {"error_occurs": False, "error_string": []}
        ranges: List[str] = []

        for mtrs, evfl, dgns in zip(all_metrics, all_eval_flow, all_diagnosis):
            for mtr in mtrs:
                total_metrics.setdefault(mtr, []).extend(mtrs[mtr])
            total_metrics += evfl
            if dgns["error_occurs"]:
                total_diagnosis["error_occurs"] = True
                error_str: str = "Error in process {:d}:\n{:}".format(world_rank, dgns["error_string"])
                logger.error(error_str)
            ranges.append("{:d}:{:d}".format(rank_starts_from, len(mtrs["success"])))
        average_metrics: Metrics = {}
        for mtr in total_metrics:
            average_metrics[mtr] = [np.mean(total_metrics[mtr]).item()]
        total_diagnosis["error_string"] = "\n\n---\n\n".join(total_diagnosis["error_string"])

        if save_eval_flow and evaluation_arguments["save_traj_to"] is not None:
            with open(os.path.join(evaluation_arguments["save_traj_to"], "eval_flow.txt"), "w") as f:
                f.write("\n".join(total_eval_flow))
        if print_results:
            print( "\x1b[42mCOMPLETEION with %s!\x1b[0m Avg #Steps: %.2f, Avg Reward: %.3f, SR: %.4f"\
                 % ( ", ".join(ranges)
                   , average_metrics["step"][0], average_metrics["reward"][0], average_metrics["success"][0]
                   )
                 )
    else:
        total_metrics = None
        total_eval_flow = None
        total_diagnosis = None
        average_metrics = None
    world.Barrier()

    total_avg_metrics: Metrics = world.bcast(average_metrics, root=0)
    total_metrics: Metrics = world.bcast(total_metrics, root=0)
    total_eval_flow: EvalFlow = world.bcast(total_eval_flow, root=0)
    total_diagnosis: Diagnosis = world.bcast(total_diagnosis, root=0)
    world.Barrier()

    return (worker_avg_metrics, worker_metrics, worker_eval_flow, worker_diagnosis)\
         , (total_avg_metrics, total_metrics, total_eval_flow, total_diagnosis)
    #  }}} function evaluate_llm_agent_mpi # 
