import android_env
from android_env.wrappers import base_wrapper

from typing import Dict
import dm_env
from dm_env import specs

class VhIoWrapper(base_wrapper.BaseWrapper):
    """
    Wraps the environment with view hierarchy (VH) element iteractions.

    The actions are formalated as

    ```haskell
    data Action = CLICK Int -- eid
                | INPUT Int -- eid
                        String -- text
                | SCROLL Direction
    data Direction = UP | DOWN | LEFT | RIGHT
    ```
    """

    def __init__(self, env: android_env.AndroidEnv):
        #  method __init__ {{{ # 
        """
        Args:
            env (android_env.AndroidEnv): the environment to be wrapped
        """

        super(VhIoWrapper, self).__init__()

        self._bbox_list: List[List[int]] = [] # bboxes are saved as [x0, y0, x1, y1]
        self._action_spec: Dict[str, specs.Array] # TODO
        #  }}} method __init__ # 

    def action_spec(self) -> Dict[str, specs.Array]:
        #  method action_spec {{{ # 
        pass
        #  }}} method action_spec # 
