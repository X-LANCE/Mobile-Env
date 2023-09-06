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

from android_env.components.adb_controller import AdbController

import requests

from typing import Optional
from typing import List

# ZDY_COMMENT: adb and frida arguments are left to server daemon

class RemoteAdbController(AdbController):
    #  class RemoteAdbController {{{ # 

    def __init__( self
                , address: str
                , port: int
                , session: requests.Session
                , device_name: str
                ):
        #  method __init__ {{{ # 
        super(RemoteAdbController, self).__init__(device_name)
        #self._local_device_name: str =\
                #device_name[14:] if device_name.startswith("remote-device:")\
                               #else ""

        self._address: str = address
        self._port: int = port
        self._url_base = "http://{:}:{:}/".format(self._address, self._port)

        self._session: requests.Session = session
        #  }}} method __init__ # 

    def _execute_command( self, args: List[str]
                        , timeout: Optional[float] = None
                        ) -> Optional[bytes]:
        # TODO
        pass
    #  }}} class RemoteAdbController # 
