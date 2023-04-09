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

"""
Created by Danyang Zhang @X-Lance.
"""

import urllib.parse
from typing import Callable
import functools

Modifier = Callable[[str], str]

# Tool Functions

def escape(x: str) -> str:
    return x.replace("\\", "\\\\").replace("\"", "\\\"")

# List Operations

def to_list(x: str) -> str:
    return "["\
            + ",".join(
                map(lambda s: "\"{:}\"".format(s),
                    map(escape,
                        x.split(","))))\
            + "]"

def regex_list(x: str) -> str:
    return "(" + "|".join(x.split(",")) + ")"

# Regex Operations

_metaCharacters = str.maketrans({ch: "\\" + ch
                                 for ch in [ ".", "^", "$", "*"
                                           , "+", "?", "{", "}"
                                           , "\\", "[", "]", "|"
                                           , "(", ")"
                                           ]})
def regex_esc(x: str) -> str:
    return x.translate(_metaCharacters)

# URL Operations

url_path: Modifier = functools.partial(urllib.parse.quote,
                                       safe="/:@=()")
url_query: Modifier = urllib.parse.quote_plus

def url_title(x: str) -> str:
    return x.replace(" ", "-")

# Common String Operations

lower: Modifier = str.lower
upper: Modifier = str.upper

# Other Operations

def filter_comma(x: str) -> str:
    return x.replace(",", "")

def remove_howto(x: str) -> str:
    if len(x)<7:
        return x
    if x[:7]=="how to ":
        return x[7:]
    return x
