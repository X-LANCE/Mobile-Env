#!/usr/bin/python3
# vimc: call SyntaxRange#Include('```ebnf', '```', 'ebnf', 'NonText'):
# vimc: highlight ModifierId term=bold ctermfg=green:
# vimc: syn match ModifierId /\(\ \{4}\*\ \)\@<=\w\+\(\:\|$\)\@=/:

"""
A tool to simply edit the resaved action record pickles.

The syntax of the modifiers:

```ebnf
modifiers = modifier { "," modifier } ;
modifier = index ":" name [ ":" param { ":" param } ] ;
```

Supported modifiers:
    * delete:start:end
    * instructionize:action_idx:instruction_idx; if instruction_idx is -1, delete
      the instruction field; action_idx 0 is meta record
    * auto_instructionize
    * rewardize:action_idx:reward_delta; new_reward = old_reward+reward_delta, if
      old_reward doesn't exit, it is assumed to be 0, if new_reward is 0, it
      will be deleted from the record
    * remove
"""

import pickle as pkl
import sys
import shutil
import os.path
from android_env.proto import task_pb2
from google.protobuf import text_format
from typing import Tuple, List, Dict
from typing import Any
import functools

pkl_name = sys.argv[1]
modifiers = sys.argv[2] if len(sys.argv)>2 else ""
modifiers = modifiers.split(",")
modifiers = list( map( lambda mdf: mdf.split(":")
                     , modifiers
                     )
                )
task_definition_path = sys.argv[3] if len(sys.argv)>3 else "../../android_env/apps/wikihow/templates.miniout"

if len(modifiers)==0:
    exit(0)

#  Modifier Implementations {{{ # 
Trajectory = List[Dict[str, Any]]
def apply_modifier( mdf: Tuple[str]
                  , local_dict: Dict[str, Any]
                  , trajectories: List[Trajectory]
                  ):
    """
    Args:
        mdf: tuple of str
        local_dict: dict like {str: something}
        trajectories: list of list of dict like
          {
            "action_type": {0, 1, 2, 3}
            "input_token": str, present if `action_type` is 3
              (action_type.ActionType.TEXT)
            "touch_position": ndarray of float64 with shape (2,), present if
              `action_type` is not 3
            "reward": float, optional
            "instruction": list of str, optional
            "observation": ndarray of uint8 with shape (H, W, 3)
          }
    """

    if mdf[1]=="remove":
        del trajectories[int(mdf[0])]
    else:
        modifier_function = globals()[mdf[1]]
        if len(mdf)>2:
            modifier_function = functools.partial(modifier_function, *mdf[2:])
        modifier_function(local_dict, trajectories[int(mdf[0])])

def delete( start: str, end: str
           , local_dict: Dict[str, Any]
           , trajectory: Trajectory
           ):
    start = int(start)
    end= int(end)
    del trajectory[start:end]
def instructionize( action_index: str, instruction_index: str
                  , local_dict: Dict[str, Any]
                  , trajectory: Trajectory
                  ):
    action_index = int(action_index)
    instruction_index = int(instruction_index)
    if instruction_index==-1\
            and "instruction" in trajectory[action_index]:
        del trajectory[action_index]["instruction"]
    else:
        trajectory[action_index]["instruction"] =\
                local_dict["instructions"][instruction_index]
def auto_instructionize( local_dict: Dict[str, Any]
                       , trajectory: Trajectory
                       ):
    index = 0
    for rcd in trajectory[1:-1]:
        if rcd["reward"]>0:
            rcd["instruction"] = local_dict["instructions"][index]
            index += 1
            index = min(index, len(local_dict["instructions"])-1)
def rewardize( action_index: str, reward_delta: str
             , local_dict: Dict[str, Any]
             , trajectory: Trajectory
             ):
    action_index = int(action_index)
    reward_delta = float(reward_delta)
    reward = trajectory[action_index].get("reward", 0.)
    reward += reward_delta
    if reward==0. and "reward" in trajectory[action_index]:
        del trajectory[action_index]["reward"]
    else:
        trajectory[action_index]["reward"] = reward
#  }}} Modifier Implementations # 

needs_task_definition = any( map( lambda mdf: mdf[1] in {"instructionize"}
                                , modifiers
                                )
                           )

with open(pkl_name, "rb") as f:
    record = pkl.load(f)
shutil.move(pkl_name, pkl_name + ".old")

task_definition_id = record["meta"]["task_definition_id"]
if needs_task_definition:
    with open(os.path.join(task_definition_path, task_definition_id  + ".textproto")) as f:
        textproto = f.read()
    task_definition = task_pb2.Task()
    text_format.Parse(textproto, task_definition)

    def transformation_to_instruction(transformation: str) -> str:
        local_env = {}
        exec(transformation, globals(), local_env)
        return local_env["y"]

    instructions = list(
                    map( transformation_to_instruction
                       , map( lambda f_evt: f_evt.event.transformation[0]
                            , filter( lambda f_evt: f_evt.event.IsInitialized()\
                                        and len(f_evt.event.events)>0
                                    , task_definition.event_slots.instruction_listener.events
                                    )
                            )
                       )
                    )

for mdf in modifiers:
    apply_modifier(mdf, locals(), record["trajectories"])

with open(pkl_name, "wb") as f:
    pkl.dump(record, f)
