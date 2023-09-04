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

# Created by Danyang Zhang @X-Lance.

from android_env.components.simulators import base_simulator
from android_env.components.adb_controller import AdbController
from android_env.components.log_stream import LogStream

#import requests

from typing import Dict, List
from typing import Optional
import numpy as np

class RemoteSimulator(base_simulator.BaseSimulator):
    #  class RemoteSimulator {{{ # 
    def __init__( self
                , address: str
                , port: int
                , **kwargs
                ):
        #  method __init__ {{{ # 
        super(RemoteSimulator, self).__init__(**kwargs)

        self._address: str = address
        self._port: int = port
        #  }}} method __init__ # 

    def _restart_impl(self):
        # TODO
        pass
    def _launch_impl(self):
        # TODO
        pass
    def close(self):
        # TODO
        super(RemoteSimulator, self).close()

    def adb_device_name(self) -> str:
        # TODO
        pass
    def create_adb_controller(self) -> AdbController:
        # TODO
        pass
    def _create_log_stream(self) -> LogStream:
        # TODO
        pass

    def send_action(self, action: Dict[str, np.ndarray]):
        # TODO
        pass
    def _get_observation(self) -> Optional[List[np.ndarray]]:
        # TODO
        pass
    #  }}} class RemoteSimulator # 
