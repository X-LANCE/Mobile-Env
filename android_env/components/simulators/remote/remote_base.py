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

import abc
import requests
from typing import Optional, Any, Union
from typing import Dict, Tuple

from absl import logging

class RemoteBase(abc.ABC):
    _session: requests.Session
    _timeout: float
    _retry: int
    _url_base: str

    def _get_response( self
                     , action: str
                     , args: Optional[Dict[str, Any]] = None
                     , stream: bool = False
                     , timeout: Union[ Optional[float]
                                     , Tuple[ Optional[float]
                                            , Optional[float]
                                            ]
                                     ] = None
                     , method: str = "POST"
                     ) -> requests.Response:
        #  method _get_response {{{ # 
        for i in range(self._retry):
            response: requests.Response =\
                    self._session.request( method
                                         , self._url_base + action
                                         , json=args
                                         , timeout=(timeout or self._timeout)
                                         , stream=stream
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

class ResponseError(Exception):
    def __init__(self, description: str):
        super(ResponseError, self).__init__(description)
