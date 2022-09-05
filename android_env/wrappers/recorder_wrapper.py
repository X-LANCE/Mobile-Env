from android_env.wrappers import base_wrapper
from android_env.environment import AndroidEnv
from android_env.components import action_type
from typing import Dict
import dm_env
import os.path

class RecorderWrapper(base_wrapper.BaseWrapper):
    #  class `RecorderWrapper` {{{ # 
    def __init__(self, env: AndroidEnv, dump_file: str):
        super(RecorderWrapper, self).__init__(env)

        self.dump_file: str = os.path.splitext(dump_file)[0]
        self.prev_type: action_type.ActionType = action_type.ActionType.LIFT

        self.trajectories:\
            List[List[Dict[str, Any]]]\
                = []
        self.current_trajectory:\
            List[Dict[str, Any]]\
                = []

    def step(self, action: Dict[str, Any]) -> dm_env.TimeStep:
        #  function `step` {{{ # 
        timestep = self._env.step(action)

        current_type = action["action_type"].item()
        if not (current_type==action_type.ActionType.LIFT\
                and self.prev_type==action_type.ActionType.LIFT):
            record = {}
            record["action_type"] = current_type
            if current_type==action_type.ActionType.TEXT:
                record["input_token"] = action["input_token"].item()
            elif current_type==action_type.ActionType.TOUCH:
                record["touch_position"] = action["touch_position"]
            record["reward"] = timestep.reward
            record["observation"] = timestep.observation["pixels"]
            record["view_hierarchy"] = timestep.observation["view_hierarchy"]
            record["orientation"] = np.argmax(timestep.observation["orientation"])
            self.current_trajectory.append(record)

        if timestep.last():
            self.trajectories.append(self.current_trajectory)
            self.current_trajectory = []
        #  }}} function `step` # 
    #  }}} class `RecorderWrapper` # 
