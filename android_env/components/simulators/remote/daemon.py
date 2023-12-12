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

from flask import Flask, request, session
import flask_compress
import threading

import secrets
import yaml
import os.path
import numpy as np
import base64
from PIL import Image

import logging
import datetime
import sys

from android_env.components.simulators import EmulatorSimulator
from android_env.components.adb_controller import AdbController
from android_env.components.adb_log_stream import AdbLogStream

from typing import Dict, List
from typing import Any, Optional, Union, Iterator

app = Flask(__name__)
app.secret_key = secrets.token_bytes()
flask_compress.Compress(app)

#  Logger Configs {{{ # 
logger = logging.getLogger()
logger.setLevel(logging.DEBUG)

datetime_str: str = datetime.datetime.now().strftime("%Y%m%d@%H%M%S")

file_handler = logging.FileHandler(os.path.join("simu_daemon_logs", "normal-{:}.log".format(datetime_str)))
debug_handler = logging.FileHandler(os.path.join("simu_daemon_logs", "debug-{:}.log".format(datetime_str)))
stdout_handler = logging.StreamHandler(sys.stdout)

file_handler.setLevel(logging.INFO)
debug_handler.setLevel(logging.DEBUG)
stdout_handler.setLevel(logging.INFO)

formatter = logging.Formatter(fmt="\x1b[1;33m[%(asctime)s \x1b[31m%(levelname)s \x1b[32m%(module)s/%(lineno)d-%(processName)s\x1b[1;33m] \x1b[0m%(message)s")
file_handler.setFormatter(formatter)
debug_handler.setFormatter(formatter)
stdout_handler.setFormatter(formatter)

#stdout_handler.addFilter(logging.Filter(app.logger.name))

logger.addHandler(file_handler)
logger.addHandler(debug_handler)
logger.addHandler(stdout_handler)

logger: logging.Logger = app.logger
#  }}} Logger Configs # 

with open("android-envd.conf.yaml") as f:
    config: Dict[str, Any] = yaml.load(f, Loader=yaml.Loader)

# session/manager dict:
# {
#   //"simulator": EmulatorSimulator
#   "is_launched": optional bool, defaults to False
#   //"adb_controller": list of AdbController
#   //"lock": threading.Lock
#   "sid": int
# }

manager: List[Dict[str, Any]] = []
glock = threading.Lock()

@app.route("/init", methods=["POST"])
def init() -> str:
    #  function init {{{ # 
    if not session.get("is_launched", False):
        session["is_launched"] = True

        adb_controller_args = { "adb_path": os.path.expanduser(config.get("adb_path", "~/Android/Sdk/platform-tools/adb"))
                              , "adb_server_port": 5037
                              , "prompt_regex": r"\w*:\/ [$#]"
                              }
        emulator_launcher_args = { "avd_name": config["avd_name"]
                                 , "android_avd_home": os.path.expanduser(config.get("android_avd_home", "~/.android/avd"))
                                 , "android_sdk_root": os.path.expanduser(config.get("android_sdk_root", "~/Android/Sdk"))
                                 , "emulator_path": os.path.expanduser(config.get("emulator_path", "~/Android/Sdk/emulator/emulator"))
                                 , "run_headless": config.get("run_headless", False)
                                 , "gpu_mode": "swiftshader_indirect"
                                 , "writable_system": False
                                 }
        adb_root = False
        frida_server: Optional[str] = None
        gap_sec: float = config.get("gap_sec", 0.05)

        if "mitm_config" in config\
                and config["mitm_config"] is not None\
                and len(config["mitm_config"])>0:
            mitm_config: Dict[str, str] = config["mitm_config"]

            emulator_launcher_args["writable_system"] = True
            emulator_launcher_args["proxy_address"] = mitm_config.get("address", "127.0.0.1")
            emulator_launcher_args["proxy_port"] = mitm_config.get("port", "8080")

            if mitm_config["method"]=="frida":
                adb_root = True
                frida_server = mitm_config.get("frida-server", "/data/local/tmp/frida-server")
                adb_controller_args["frida"] = mitm_config.get("frida", "frida")
                adb_controller_args["frida_script"] = mitm_config.get("frida-script", "frida-script.js")

        simulator = EmulatorSimulator( adb_controller_args=adb_controller_args
                                     , emulator_launcher_args=emulator_launcher_args
                                     , adb_root=adb_root
                                     , frida_server=frida_server
                                     , gap_sec=gap_sec
                                     )

        with glock:
            session["sid"] = len(manager)
            manager.append({})
        sid: int = session["sid"]
        manager[sid]["lock"] = threading.Lock()
        with manager[sid]["lock"]:
            manager[sid]["simulator"] = simulator
    return "OK"
    #  }}} function init # 

@app.route("/launch", methods=["POST"])
def launch() -> str:
    #  function launch {{{ # 
    sid: int = session["sid"]
    with manager[sid]["lock"]:
        manager[sid]["simulator"].launch()
    return "OK"
    #  }}} function launch # 

@app.route("/restart", methods=["POST"])
def restart() -> str:
    #  function restart {{{ # 
    sid: int = session["sid"]
    with manager[sid]["lock"]:
        manager[sid]["simulator"].restart()
    return "OK"
    #  }}} function restart # 

@app.route("/close", methods=["POST"])
def close() -> str:
    #  function close {{{ # 
    sid: int = session["sid"]
    with manager[sid]["lock"]:
        manager[sid]["simulator"].close()
        if "adb_controller" in manager[sid]:
            for adb_ctrl in manager[sid]["adb_controller"]:
                adb_ctrl.close()
    return "OK"
    #  }}} function close # 

@app.route("/create_adbc", methods=["POST"])
def create_adb_controller() -> Dict[str, Union[str, int]]:
    #  function create_adb_controller {{{ # 
    sid: int = session["sid"]
    with manager[sid]["lock"]:
        if not "adb_controller" in manager[sid]:
            manager[sid]["adb_controller"] = []
        adbc_id: int = len(manager[sid]["adb_controller"])
        manager[sid]["adb_controller"].append(manager[sid]["simulator"].create_adb_controller())
    return { "name": manager[sid]["simulator"].adb_device_name()
           , "id": adbc_id
           }
    #  }}} function create_adb_controller # 

@app.route("/adb", methods=["POST"])
def adb() -> Dict[str, Union[int, Optional[str]]]:
    #  function adb {{{ # 
    """
    Returns:
        Dict[str, Union[int, Optional[str]]]: dict like
          {
            "id": int as the id of adb controller
            "output": str as base64 of output bytes
          }
    """

    args: Dict[str, Union[int, List[str], Optional[float]]] =\
            request.json

    sid: int = session["sid"]
    adb_controller: AdbController = manager[sid]["adb_controller"][args["id"]]
    output: Optional[bytes] = adb_controller._execute_command(args["cmd"], timeout=args["timeout"])
    if isinstance(output, bytes):
        output: Optional[str] = base64.b64encode(output).decode()
    return { "id": args["id"]
           , "output": output
           }
    #  }}} function adb # 

@app.route("/create_logs", methods=["GET"])
def create_log_stream() -> Iterator[str]:
    #  function create_log_stream {{{ # 
    sid: int = session["sid"]
    log_stream: AdbLogStream = manager[sid]["simulator"].get_log_stream()
    return log_stream.get_stream_output(), {"Content-Type": "text/event-stream"}
    #  }}} function create_log_stream # 

@app.route("/set_filts", methods=["POST"])
def set_log_filters() -> str:
    #  function set_log_filters {{{ # 
    args: Dict[str, List[str]] = request.json

    sid: int = session["sid"]
    with manager[sid]["lock"]:
        manager[sid]["simulator"].get_log_stream().set_log_filters(args["filts"])
    return "OK"
    #  }}} function set_log_filters # 

@app.route("/act", methods=["POST"])
def action() -> str:
    #  function action {{{ # 
    args: List[Dict[str, Union[int, List[float], str]]] =\
            request.json

    action_dicts: List[Dict[str, np.ndarray]] = []
    for arg in args:
        action_dict: Dict[str, np.ndarray] = {}
        action_dict["action_type"] = np.array(arg["action_type"])
        if "touch_position" in arg:
            action_dict["touch_position"] = np.array(arg["touch_position"])
        if "input_token" in arg:
            action_dict["input_token"] = np.array(arg["input_token"])
        if "response" in arg:
            action_dict["response"] = np.array(arg["response"], dtype=np.object_)
        action_dicts.append(action_dict)

    sid: int = session["sid"]
    with manager[sid]["lock"]:
        manager[sid]["simulator"].send_action(action_dicts)
    return "OK"
    #  }}} function action # 

@app.route("/observ", methods=["POST"])
def observation() -> Dict[str, Union[str, List[int], int]]:
    #  function observation {{{ # 
    """
    Returns:
        Dict[str, Union[str, List[int], int]]: dict like
          {
            "img": str as the base64 of image bytes
            "size": [int, int] as [width, height] of image
            "time": int as the timestamp
          }
    """
    args: Dict[str, List[int]] = request.json

    sid: int = session["sid"]
    with manager[sid]["lock"]:
        observation: np.ndarray
        timestamp: np.int64
        observation, timestamp = manager[sid]["simulator"]._get_observation()

    raw_width: int
    raw_height: int
    raw_height, raw_width, _ = observation.shape

    if "resize_to" in args:
        observation = np.array( Image.fromarray(observation).resize(args["resize_to"])
                              , dtype=np.uint8
                              )
    width: int
    height: int
    height, width, _ = observation.shape

    observation: str = base64.b64encode(observation.tobytes()).decode()
    return { "img": observation
           , "size": [width, height]
           , "raw_size": [raw_width, raw_height]
           , "time": timestamp.item()
           }
    #  }}} function observation # 
