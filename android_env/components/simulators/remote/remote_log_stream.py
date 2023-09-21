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

from android_env.components import log_stream
from android_env.components.simulators.remote import remote_base

import requests
from typing import Iterable, Optional
from typing import List

class RemoteLogStream( log_stream.LogStream
                     , remote_base.RemoteBase
                     ):
    #  class RemoteLogStream {{{ # 
    def __init__( self
                , address: str
                , port: int
                , session: requests.Session
                , timeout: float
                , retry: int
                ):
        #  method __init__ {{{ # 
        super(RemoteLogStream, self).__init__()

        self._address: str = address
        self._port: int = port
        self._url_base = "http://{:}:{:}/".format(self._address, self._port)
        self._session: requests.Session = session
        self._timeout: float = timeout
        self._retry: int = retry

        self._response: Optional[requests.Response] = None
        #  }}} method __init__ # 

    def _get_stream_output(self) -> Iterable[str]:
        self._response: requests.Response = self._get_response( "create_logs"
                                                              , stream=True
                                                              , timeout=(self._timeout, None)
                                                              , method="GET"
                                                              )
        return map(bytes.decode, self._response.iter_lines())

    def stop_stream(self):
        #self._response.close()
        pass

    def set_log_filters(self, log_filters: List[str]):
        super(RemoteLogStream, self).set_log_filters(log_filters)

        self._get_response( "set_filts"
                          , { "filts": log_filters
                            }
                          )
    #  }}} class RemoteLogStream # 
