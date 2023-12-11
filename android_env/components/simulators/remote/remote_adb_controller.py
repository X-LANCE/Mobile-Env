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
from android_env.components.simulators.remote import remote_base

import requests
from typing import Optional
from typing import List, Dict
import base64

from absl import logging

# ZDY_COMMENT: adb and frida arguments are left to server daemon

class RemoteAdbController( AdbController
                         , remote_base.RemoteBase
                         ):
    #  class RemoteAdbController {{{ # 

    def __init__( self
                , address: str
                , port: int
                , session: requests.Session
                , timeout: float
                , retry: int
                , remote_id: int
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
        self._timeout: float = timeout
        self._retry: int = retry

        self._remote_id: int = remote_id
        #  }}} method __init__ # 

    def _execute_command( self, args: List[str]
                        , timeout: Optional[float] = None
                        ) -> Optional[bytes]:
        #  method _execute_command {{{ # 
        """
        Args:
            args (List[str]): adb command, e.g., `["install", "a.apk"]`
            timeout (Optional[float]): if ignored, then the default timeout
              defined at the remote daemon will be adopted

        Returns:
            Optional[bytes]: the output of the command from the stdout. None if
              the command failed
        """
        with self._execute_command_lock:
            response: requests.Response =\
                    self._get_response( "adb"
                                      , { "id": self._remote_id
                                        , "cmd": args
                                        , "timeout": timeout
                                        }
                                      )
        response: Dict[str, Optional[bytes]] = response.json()

        output: Optional[str] = response["output"]
        if isinstance(output, str):
            output: Optional[bytes] = base64.b64decode(output.encode())
        logging.debug( "Remote ADB response for %d from %d: %s"
                     , self._remote_id, response["id"]
                     , output
                     )
        assert self._remote_id==response["id"]\
             , "Request Id: {:d}, Response Id: {:d}"\
                .format(self._remote_id, response["id"])

        return output
        #  }}} method _execute_command # 

    def install_apk( self
                   , local_apk_path: str
                   , timeout: Optional[float] = None
                   ):
        """
        Installs an app given a `local_apk_path` in the filesystem.

        Args:
            local_apk_path (str): Path to .apk file in the local filesystem.
            timeout (Optional[float]): A timeout to use for this operation. If
              not set the default timeout set on the constructor will be used.
        """
        self._execute_command( ['install', '-r', '-t', '-g', local_apk_path]
                             , timeout=timeout
                             )
    #  }}} class RemoteAdbController # 
