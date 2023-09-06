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

import requests

from typing import Dict, List
from typing import Optional
import numpy as np

from absl import logging
import traceback

# ZDY_COMMENT: adb_root and frida_server arguments are ignored here
# they should be configured directly on launching the daemon on server

class RemoteSimulator(base_simulator.BaseSimulator):
    #  class RemoteSimulator {{{ # 
    """
    Protocol:
    - without payloads and expectations:
      + launch
      + start
      + close
    - queries, with expectations
      + query_adbdevname
        + { "name": str }
    - queries, with both payloads and expectations:
      + adb
        + send {
            "command": list of str
            "timeout": float or none
          }
    """

    def __init__( self
                , address: str
                , port: int
                , timeout: float = 5.
                , retry: int = 3
                , **kwargs
                ):
        #  method __init__ {{{ # 
        super(RemoteSimulator, self).__init__(**kwargs)

        self._address: str = address
        self._port: int = port
        self._url_base = "http://{:}:{:}/".format(self._address, self._port)

        self._timeout: float = 5.
        self._retry: int = 3

        self._session: Optional[requests.Session] = None
        #  }}} method __init__ # 

    def _get_response(self, action: str, args: Optional[Dict[str, str]] = None) -> requests.Response:
        #  method _get_response {{{ # 
        for i in range(self._retry):
            response: requests.Response =\
                    self._session.post( self._url_base + action
                                      , json=args
                                      , timeout=self._timeout
                                      )
            if response.status_code==200:
                return response
            logging.debug( "Remote Simulator Response Error %d: %d"
                         , i, response.status_code
                         )
        raise ResponseError("Remote Simulator Response Error: {:d}"\
                                .format(response.status_code)
                           )
        #  }}} method _get_response # 

    #  Setup and Clear Methods {{{ # 
    def _restart_impl(self):
        self._get_response("restart")
    def _launch_impl(self):
        self._session = requests.Session()
        self._get_response("launch")
    def close(self):
        try:
            self._get_response("close")
        except:
            logging.exception("Response Error During Closing RemoteSimulator")
            traceback.print_exc()
        self._session.close()
        super(RemoteSimulator, self).close()
    #  }}} Setup and Clear Methods # 

    def adb_device_name(self) -> str:
        #  method adb_device_name {{{ # 
        try:
            response: requests.Response = self._get_response("query_adbdevname")
            name: str = response.json()["name"]
            name = "remote-device:{:}".format(name)
        except:
            name: str = "remote-device"
        return name
        #  }}} method adb_device_name # 
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

class ResponseError(Exception):
    def __init__(self, description: str):
        super(ResponseError, self).__init__(description)
