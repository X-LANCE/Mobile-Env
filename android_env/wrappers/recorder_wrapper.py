from android_env.wrappers import base_wrapper
from android_env.environment import AndroidEnv
from android_env.components import action_type
from typing import Dict
from typing import Any
import dm_env
import os.path
import lxml.etree
import numpy as np
import pickle as pkl

# autosave at the reset time and episode end.

def is_real_action(action: action_type.ActionType) -> bool:
    return action==action_type.ActionType.TOUCH or action==action_type.ActionType.TEXT

class RecorderWrapper(base_wrapper.BaseWrapper):
    #  class `RecorderWrapper` {{{ # 
    def __init__(self, env: AndroidEnv, dump_file: str):
        super(RecorderWrapper, self).__init__(env)

        self._index: int = 0
        self.dump_file: str = os.path.splitext(dump_file)[0]

        self.prev_type: action_type.ActionType = action_type.ActionType.LIFT
        self._buffer: Dict[str, Any] = {}
        self.is_valid: bool = False

        #self.trajectories:\
            #List[List[Dict[str, Any]]]\
                #= []
        self.current_trajectory:\
            List[Dict[str, Any]]\
                = []

    def step(self, action: Dict[str, Any]) -> dm_env.TimeStep:
        #  function `step` {{{ # 
        timestep = self._env.step(action)

        current_type = action["action_type"].item()

        # late judge
        self.is_valid = self.is_valid\
                     or ( self.prev_type==action_type.ActionType.LIFT
                      and is_real_action(current_type)
                        )

        # dump the buffer
        if self.is_valid:
            self.current_trajectory.append(self._buffer)

        # early judge
        self.is_valid = current_type!=action_type.ActionType.REPEAT\
                    and not ( current_type==action_type.ActionType.LIFT
                          and self.prev_type==action_type.ActionType.LIFT
                            )\
                     or timestep.reward>0

        record = {}
        record["action_type"] = current_type
        if current_type==action_type.ActionType.TEXT:
            record["input_token"] = action["input_token"].item()
        elif current_type==action_type.ActionType.TOUCH:
            record["touch_position"] = action["touch_position"]
        record["reward"] = timestep.reward
        instruction = self._env.task_instructions()
        if len(instruction)>0:
            record["instruction"] = instruction
        record["observation"] = timestep.observation["pixels"]
        record["view_hierarchy"] = lxml.etree.tostring(
                timestep.observation["view_hierarchy"],
                encoding="unicode") if timestep.observation["view_hierarchy"]\
                        is not None else None
        record["orientation"] = np.argmax(timestep.observation["orientation"])
        #self.current_trajectory.append(record)
        self._buffer = record

        self.prev_type = current_type

        if timestep.last():
            #self.trajectories.append(self.current_trajectory)
            self._save()

        return timestep
        #  }}} function `step` # 

    def _process_timestep(self, timestep: dm_env.TimeStep) -> dm_env.TimeStep:
        if timestep.first():
            self.is_valid = True
            self.prev_type = action_type.ActionType.LIFT

            record = {}
            record["task_id"] = self._env.task_id
            record["task"] = self._env.task_name
            record["command"] = self._env.command()
            record["observation"] = timestep.observation["pixels"]
            record["view_hierarchy"] = lxml.etree.tostring(
                    timestep.observation["view_hierarchy"],
                    encoding="unicode") if timestep.observation["view_hierarchy"]\
                            is not None else None
            record["orientation"] = np.argmax(timestep.observation["orientation"])
            #self.current_trajectory.append(record)
            self._buffer = record
        return timestep

    def _reset_state(self):
        self._save()

    def close(self):
        self._save()
        self._env.close()

    def _save(self):
        #  function `_save` {{{ # 
        if len(self._buffer)>0:
            self.current_trajectory.append(self._buffer)
        if len(self.current_trajectory)>1:
            with open(self.dump_file + ".{:d}.pkl".format(self._index), "ab") as f:
                pkl.dump(self.current_trajectory, f)

        self.current_trajectory = []
        self._buffer = {}
        self._index += 1
        #  }}} function `_save` # 
    #  }}} class `RecorderWrapper` # 
