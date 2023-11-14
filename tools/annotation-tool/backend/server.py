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
# 
# Revised by Danyang Zhang @X-Lance based on a private repository at
# 
#     https://git.sjtu.edu.cn/549278303/ipa-web

from flask import Flask, request, send_file
from flask_compress import Compress

#import time
#import random
#import json
import os.path
import numpy as np
#import lxml.etree
import dm_env
from typing import Dict
from typing import Any
import os
from PIL import Image
import io
import base64
import sys
import threading

import android_env
from android_env.components import action_type
from android_env.wrappers import RecorderWrapper
from android_env.components.tools.easyocr_wrapper import EasyOCRWrapper

app = Flask(__name__)
app.config['SECRET_KEY'] = 'wikihow'
Compress(app)

lock = threading.Lock()

dump_file = sys.argv[1] if len(sys.argv)>1 else "../test_dump.pkl"
task_path = sys.argv[2] if len(sys.argv)>2 else "../../android_env/apps/wikihow/templates.miniout"

task_list = list(
        sorted(
            map(lambda t: os.path.splitext(t)[0],
                filter(lambda t: t.endswith(".textproto"),
                    os.listdir(task_path)))))
init_task = 0
task_dict = {0: 0}
android = android_env.load( os.path.join(task_path, task_list[0] + ".textproto")
                          , avd_name="Pixel_2_API_30_ga_x64_1"
                          , run_headless=True
                          , mitm_config={"method": "syscert"}
                          , text_model=EasyOCRWrapper()
                          , with_view_hierarchy=True
                          )
android = RecorderWrapper(android, dump_file=dump_file)

def timestep_to_json(timestep: dm_env.TimeStep) -> Dict[str, Any]:
    with io.BytesIO() as bff:
        image = Image.fromarray(timestep.observation["pixels"])
        image.save(bff, "png")
        bff.seek(0)
        png_data = bff.read()
        base64_data = base64.b64encode(png_data)
    return { "observation": "data:image/png;base64," + base64_data.decode()
           , "reward": timestep.reward
           , "episodeEnd": timestep.last()
           }

@app.route("/", methods=["GET"])
def main():
    return send_file("./template/index.html")

@app.route("/doAction", methods=["POST"])
def do_action():
    action = request.json
    #if action["actionType"]!=action_type.ActionType.REPEAT:
        #print(action)

    parsed_action = {}
    parsed_action["action_type"] = np.array(action["actionType"])
    if action["actionType"]==action_type.ActionType.TEXT:
        parsed_action["input_token"] = np.array(action["inputToken"])
    else:
        parsed_action["touch_position"] = np.array(action["touchPosition"])

    with lock:
        timestep = android.step(parsed_action)
        #if action["actionType"]!=action_type.ActionType.REPEAT:
            #print(timestep.reward, timestep.last())
        instruction = android.task_instructions()
    response = timestep_to_json(timestep)
    response["instruction"] = instruction
    return response

@app.route("/reset", methods=["POST"])
def reset():
    #timestep = android.reset()
    #response = timestep_to_json(timestep)
    response = {}
    response["taskList"] = task_list
    return response

@app.route("/switchTask", methods=["POST"])
def switch_task():
    task_index = request.json["task"]
    if task_index not in task_dict:
        task_id = len(task_dict)
        task_dict[task_index] = task_id
        android.add_task(os.path.join(task_path, task_list[task_index] + ".textproto"))
    with lock:
        timestep = android.switch_task(task_dict[task_index])

    response = timestep_to_json(timestep)
    response["command"] = android.command()
    response["vocabulary"] = android.vocabulary()
    return response

if __name__ == '__main__':
    app.run(host="0.0.0.0", debug=False)

    android.close()
