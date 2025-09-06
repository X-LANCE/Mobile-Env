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
from android_env.templates.agents import MobileEnvAgent
from android_env.templates.agents import Obs, Act, Reset
from typing import TypedDict, List, Tuple, Dict
from typing import Optional, Any
from numbers import Number
#from pathlib import Path
from os import PathLike

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
    # TODO: evaluate one task
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

def evaluate_llm_agent():
    #  function evaluate_llm_agent {{{ # 
    # TODO
    pass
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
