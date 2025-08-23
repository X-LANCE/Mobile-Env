# Copyright 2025 SJTU X-Lance Lab
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
# 
# Created by Danyang Zhang @X-Lance

import openai
from typing import Optional, Any, Union
from typing import List, Dict, Pattern, Match
from android_env.templates.prompt_template import PromptGroupT
import logging
import re

logger = logging.getLogger("mobile_env.agents.llm_caller")

class ResponseError(Exception):
    def __init__(self, description: str):
        super(ResponseError, self).__init__(description)

class OpenAIProxy:
    #  class OpenAIProxy {{{ # 
    """
    Works with openai ~= 1.13.3.
    """

    def __init__(self, api_key: str, base_url: Optional[str] = None, model: str = "gpt-4-turbo-2024-04-09"):
        #  function __init__ {{{ # 
        if base_url is None:
            self.client = openai.OpenAI(api_key=api_key)
        else:
            self.client = openai.OpenAI(api_key=api_key, base_url=base_url)

        self.model_name: str = model
        #  }}} function __init__ # 

    def __call__( self
                , messages: PromptGroupT
                , max_tokens: int
                , temperature: float
                , top_p: float = 1.
                , stream: bool = False
                , stop: Optional[Union[str, List[str]]] = None
                , presence_penalty: float = 0.
                , frequency_penalty: float = 0.
                , logit_bias: Optional[Dict[str, float]] = None
                , request_timeout: float = 5.
                , **params
                ) -> str:
        #  method __call__ {{{ # 
        kwargs: Dict[str, Any] = {}
        if stop is not None:
            kwargs["stop"] = stop
        if logit_bias is not None:
            kwargs["logit_bias"] = logit_bias
        completion = self.client.chat.completions.create( model=self.model_name
                                                        , messages=messages
                                                        , max_tokens=max_tokens
                                                        , temperature=temperature
                                                        , top_p=top_p
                                                        , stream=stream
                                                        , presence_penalty=presence_penalty
                                                        , frequency_penalty=frequency_penalty
                                                        , **kwargs
                                                        #, request_timeout=request_timeout
                                                        )
        logger.debug("%s Completion: %s", self.model_name, repr(completion))

        response_str: Optional[str] = completion.choices[0].message.content
        if response_str is None:
            raise ResponseError( "Empty response! Finish Reason is %s. The whole response object has been recorded in the log." % completion.choices[0].finish_reason
                               )
        return response_str
        #  }}} method __call__ # 
    #  }}} class OpenAIProxy # 
