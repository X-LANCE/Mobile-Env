#!/usr/bin/python3
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

import re
import sys
import os.path

input_file = sys.argv[1]
stepname = sys.argv[2]
dump_path = sys.argv[3]

template_item_pattern = re.compile(r"<(?:(?P<modifiers>\w+(?:,\w+)*):)?(?P<identifier>\w+)>")

item_set = set()
with open(input_file) as f:
    for l in f:
        items = template_item_pattern.findall(l)
        for _, id_ in items:
            item_set.add(id_)

classname = os.path.basename(input_file).split(".")[0]
with open(os.path.join(dump_path, "{:}-{:}.conf".format(classname, stepname)), "w") as f:
    for itm in item_set:
        f.write("{:}: <VALUE>\n".format(itm))

